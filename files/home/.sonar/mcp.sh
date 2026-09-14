#!/usr/bin/env sh
#
# Sonar Vortex — launch the SonarQube MCP Server for the agent.
#
# Referenced by the workspace .mcp.json. Runs the MCP server through the native
# SonarQube CLI (`sonar run mcp`), so it inherits the sandbox environment:
#   - SONARQUBE_URL / SONARQUBE_ORG          (region + organization)
#   - SONARQUBE_TOKEN == "proxy-managed"     (real token swapped in by the proxy)
#   - HTTPS_PROXY                            (so the swap actually happens)
#
# Because it runs natively (not in a nested container), it trusts the sbx proxy
# CA and its egress to SonarQube Cloud is intercepted for credential injection.
set -eu

# The SonarQube CLI installer drops the binary here; make sure it is resolvable
# even in the non-login shell the MCP client spawns us from.
export PATH="$HOME/.local/share/sonarqube-cli/bin:$PATH"

if ! command -v sonar >/dev/null 2>&1; then
  echo "sonar-vortex: SonarQube CLI (sonar) not found on PATH — did install fail?" >&2
  exit 127
fi

# Scope to a project when one was configured (kit arg `project` -> SONAR_PROJECT_KEY).
if [ -n "${SONAR_PROJECT_KEY:-}" ]; then
  exec sonar run mcp --project "$SONAR_PROJECT_KEY"
fi

exec sonar run mcp
