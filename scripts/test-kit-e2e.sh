#!/usr/bin/env bash
#
# End-to-end test for the sonar-vortex kit.
#
# Boots a real sbx sandbox with the kit under a throwaway, scoped daemon and
# verifies the kit landed inside the container: the SonarQube CLI installed and
# resolvable, the MCP launcher present, the SONARQUBE_* env wired, and the token
# arriving as a proxy placeholder (never the real value).
#
# The token is NEVER passed as a plain-text arg/env by this script. It lives in
# the sbx secret store as a CUSTOM secret bound to the SonarQube Cloud host:
#
#   sbx --app-name sonar-vortex-tck secret set-custom \
#       --host api.sonarcloud.io --env SONARQUBE_CLI_TOKEN --value <user-token>
#
# (Use --ref 'op://…' instead of --value to source from 1Password.) Everything is
# scoped to a separate --app-name daemon, so your day-to-day sbx state is left
# untouched.
#
# Usage:
#   ./scripts/test-kit-e2e.sh
#
# Environment (never the token):
#   URL        SonarQube Cloud URL     (default: https://sonarcloud.io)
#   ORG        SonarQube org key       (default: empty)
#   APP_NAME   scoped sbx daemon name  (default: sonar-vortex-tck)
#   POLICY     default network policy  (default: balanced; empty to skip)
#   KEEP       keep the sandbox: 1 or 0 (default 0)

set -euo pipefail

# ---- config ----------------------------------------------------------------
URL="${URL:-https://sonarcloud.io}"
ORG="${ORG:-}"
APP_NAME="${APP_NAME:-sonar-vortex-tck}"
POLICY="${POLICY-balanced}"
KEEP="${KEEP:-0}"

# The credential host the secret must be bound to (bare host of $URL).
SQ_HOST="${URL#https://}"; SQ_HOST="${SQ_HOST%%/*}"
API_HOST="api.${SQ_HOST}"

KIT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SANDBOX="sonar-vortex-e2e-$$"
WORKDIR="$HOME/work/sbx-kit-sonar-vortex-e2e-$$"
SBX=(sbx --app-name "$APP_NAME")

pass=0 fail=0
say()  { printf '\n\033[1;34m== %s\033[0m\n' "$*"; }
ok()   { printf '  \033[0;32mPASS\033[0m %s\n' "$*"; pass=$((pass+1)); }
bad()  { printf '  \033[0;31mFAIL\033[0m %s\n' "$*"; fail=$((fail+1)); }
info() { printf '  \033[0;33m....\033[0m %s\n' "$*"; }

cleanup() {
  if [ "$KEEP" = "1" ]; then
    info "KEEP=1 — leaving sandbox '$SANDBOX' (rm with: ${SBX[*]} rm $SANDBOX -f)"
  else
    "${SBX[@]}" rm "$SANDBOX" -f >/dev/null 2>&1 || true
  fi
  rm -rf "$WORKDIR" 2>/dev/null || true
}
trap cleanup EXIT
mkdir -p "$WORKDIR"

# ---- preflight -------------------------------------------------------------
command -v sbx >/dev/null 2>&1 || { echo "ERROR: sbx not on PATH"; exit 1; }

# ---- 1. spec validation ----------------------------------------------------
say "1. Validate spec"
if "${SBX[@]}" kit validate "$KIT_DIR" >/dev/null 2>&1 || sbx kit validate "$KIT_DIR" >/dev/null 2>&1; then
  ok "sbx kit validate"
else
  bad "sbx kit validate"; exit 1
fi

# ---- 2. secret: custom secret bound to the SonarQube host ------------------
say "2. SonarQube token as a custom secret on $API_HOST / $SQ_HOST"
if [ -n "${SONARQUBE_CLI_TOKEN:-}" ]; then
  info "note: SONARQUBE_CLI_TOKEN found in env; this script ignores it and uses the secret store."
fi
for _ in 1 2 3 4 5; do "${SBX[@]}" secret ls >/dev/null 2>&1 && break; sleep 1; done
secrets_out="$("${SBX[@]}" secret ls 2>/dev/null || true)"
if grep -q "SONARQUBE_CLI_TOKEN" <<<"$secrets_out"; then
  ok "SONARQUBE_CLI_TOKEN custom secret present"
else
  bad "SONARQUBE_CLI_TOKEN custom secret missing"
  cat <<EOF

  Store the token first (value never touches this script), then re-run:
    ${SBX[*]} secret set-custom --host $API_HOST --env SONARQUBE_CLI_TOKEN --value <user-token>
  (or --ref 'op://<vault>/<item>/<field>' to source from 1Password)
EOF
  exit 1
fi

# ---- 3. scoped daemon policy -----------------------------------------------
say "3. Configure scoped daemon '$APP_NAME'"
if [ -n "$POLICY" ]; then
  "${SBX[@]}" policy reset --force >/dev/null 2>&1 || true
  if "${SBX[@]}" policy set "$POLICY" >/dev/null 2>&1 || "${SBX[@]}" policy init "$POLICY" >/dev/null 2>&1; then
    ok "network policy = $POLICY"
  else
    info "could not set policy '$POLICY' (continuing; check 'sbx policy --help')"
  fi
fi
if "${SBX[@]}" policy ls 2>/dev/null | grep -qi 'Managed by'; then
  info "daemon is org-managed governance — egress to $SQ_HOST may be transparent (no"
  info "interception), so the token swap can't happen and live 'sonar' calls may 401."
fi

# ---- 4. launch sandbox with the kit ----------------------------------------
say "4. Launch sandbox '$SANDBOX' with the kit"
KIT_ARGS=(--kit-arg "url=$URL")
[ -n "$ORG" ] && KIT_ARGS+=(--kit-arg "org=$ORG")
if "${SBX[@]}" run claude --kit "$KIT_DIR" "${KIT_ARGS[@]}" \
      --name "$SANDBOX" --detached "$WORKDIR" >/dev/null 2>&1; then
  ok "sandbox created"
else
  bad "sbx run failed (re-run without --detached to see any prompt)"; exit 1
fi
ex() { "${SBX[@]}" exec "$SANDBOX" -- "$@"; }

# ---- 5. in-container verification ------------------------------------------
say "5. Verify inside the container"
# sonar must resolve via a plain (non-login) exec — proves the ~/.local/bin symlink.
if v=$(ex sonar --version 2>/dev/null); then ok "sonar CLI on PATH ($(printf '%s' "$v" | head -1))"; else bad "sonar CLI not resolvable via plain exec (PATH symlink?)"; fi
[ "$(ex printenv SONARQUBE_CLI_SERVER 2>/dev/null)" = "$URL" ] && ok "SONARQUBE_CLI_SERVER=$URL" || bad "SONARQUBE_CLI_SERVER mismatch"
[ -n "$(ex printenv SONARQUBE_CLI_ORG 2>/dev/null || true)" ] || info "SONARQUBE_CLI_ORG empty (pass ORG=<org> to set it)"
# The container should only ever see a proxy placeholder, never a real token.
for var in SONARQUBE_CLI_TOKEN; do
  val="$(ex printenv "$var" 2>/dev/null || true)"
  case "$val" in
    ""|proxy-managed|sbx-cs-*) ok "$var = '${val:-unset}' (proxy placeholder, not a real token)" ;;
    *) bad "$var looks like a real credential value in the container (leak?)" ;;
  esac
done

# ---- 6. functional: auth + hit SonarQube Cloud (needs a valid token) --------
say "6. sonar auth status + live call to SonarQube Cloud"
if ex sonar auth status 2>&1 | grep -qi 'Connected'; then
  ok "sonar auth status: Connected (env-var auth)"
else
  info "sonar auth status not Connected (SONARQUBE_CLI_ORG/SERVER must both be set)"
fi
out=$(ex sonar list projects 2>&1 || true)
printf '%s\n' "$out" | head -5 | sed 's/^/      /'
case "$out" in
  *401*) info "list projects -> 401: plumbing OK (proxy swapped the token); token is invalid/synthetic" ;;
esac

# ---- 7. network policy log -------------------------------------------------
say "7. Network policy log (proof the call reached $SQ_HOST)"
"${SBX[@]}" policy log "$SANDBOX" 2>/dev/null | grep -iE "HOST|sonarcloud|sonarqube" | sed 's/^/      /' || info "policy log unavailable"

# ---- summary ---------------------------------------------------------------
say "Summary"
printf '  %d passed, %d failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ] && { echo "  e2e OK"; exit 0; } || { echo "  e2e had failures"; exit 1; }
