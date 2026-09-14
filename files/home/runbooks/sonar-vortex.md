# Sonar Vortex — sandbox runbook

Sonar Vortex gives your AI coding agent **repository-aware context before it
writes code** and **real-time verification after every change**, using the same
SonarQube analysis engine trusted in production. This kit wires two pieces into
the sandbox:

- **SonarQube CLI** (`sonar`) — native binary for analysis, secrets scanning,
  quality-gate status, and the Vortex context.
- **SonarQube MCP Server** — declared in the workspace `.mcp.json`, launched via
  `~/.sonar/mcp.sh` (`sonar run mcp`). Exposes Vortex capabilities as MCP tools.

## Credentials & networking (how the swap works)

- `SONARQUBE_TOKEN` is the literal `proxy-managed` inside the container — **never
  the real token**. `SONAR_TOKEN` and `SONARQUBE_CLI_TOKEN` are aliases of the
  same sentinel.
- On outbound HTTPS to SonarQube Cloud, the sbx proxy swaps the sentinel in the
  `Authorization: Bearer` header for your real token (stored host-side). Both the
  CLI and the MCP server run natively, trust the proxy CA, and honor
  `HTTPS_PROXY`, so the swap is transparent.
- Egress is allowed to `sonarcloud.io` / `sonarqube.us` (+ `api.*`) and the
  CLI/analyzer download hosts. Everything else is denied by policy.

## Region & organization

- `SONARQUBE_URL` selects the region: `https://sonarcloud.io` (EU, default) or
  `https://sonarqube.us` (US). Set it with `--kit-arg url=https://sonarqube.us`.
- `SONARQUBE_ORG` is your organization key (`--kit-arg org=<your-org>`).
- `SONAR_PROJECT_KEY` (optional, `--kit-arg project=<key>`) scopes the MCP server
  and context to one project. The project must already have been analyzed on a
  long-lived branch in SonarQube Cloud.

## The Vortex loop

1. **Before writing code** — pull context with the `sonarqube` MCP tools:
   coding guidelines, third-party dependency health (before adding/bumping a
   dependency), architecture graphs/constraints, and semantic navigation. This
   front-loads the right constraints so the first pass is compliant.
2. **After each change** — verify from the terminal:

   ```bash
   sonar analyze agentic        # fast, agent-oriented analysis of the change
   sonar analyze secrets        # scan for hardcoded secrets
   sonar quality-gate status    # is the project still passing its gate?
   sonar list issues            # issues to fix before finishing
   ```

3. **Fix and re-run** until analysis is clean and the quality gate passes.

## Verify the wiring

```bash
# CLI present and on PATH
sonar --version

# Token is the proxy sentinel inside the container (never a real value)
printenv SONARQUBE_TOKEN            # -> proxy-managed

# Region / org / project wired
printenv SONARQUBE_URL SONARQUBE_ORG SONAR_PROJECT_KEY

# MCP launcher resolves the CLI
sh "$HOME/.sonar/mcp.sh" --help 2>/dev/null | head || true

# Confirm calls actually reached SonarQube Cloud
#   (run from the host)  sbx policy log <sandbox> | grep -Ei 'sonarcloud|sonarqube'
```

## Troubleshooting

- **`sonar: command not found`** — open a new shell (the installer appends PATH
  to your rc files), or run `export PATH="$HOME/.local/share/sonarqube-cli/bin:$PATH"`.
- **401 / auth errors** — the token binding is missing or is not a **USER**
  token. Connected mode requires a user token; project/global/scoped-org tokens
  do not bind. Store it host-side (see the kit README) and recreate the sandbox.
- **Empty context / project not found** — the project must exist and have been
  analyzed on a long-lived branch in SonarQube Cloud, and `SONARQUBE_ORG` must
  match. Confirm the region (`SONARQUBE_URL`) matches where the project lives.
- **Egress blocked** — under org-managed governance the kit's allowlist is not
  applied and injection may be forced transparent; an org admin must allow the
  SonarQube host and permit interception for the token swap to happen.

Docs: <https://www.sonarsource.com/products/sonar-vortex/> ·
<https://docs.sonarsource.com/sonarqube-cli/>
