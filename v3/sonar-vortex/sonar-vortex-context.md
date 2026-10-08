# Sonar Vortex

This sandbox has the **SonarQube CLI** (`sonar`) installed and, on start,
runs `sonar integrate claude` to wire **Sonar Vortex** — the SonarQube MCP
Server, secrets-scanning hooks, and repository-aware context. Use it to write
higher-quality, more secure code with fewer tokens and less rework.

## First, make sure Vortex is wired

If the `sonarqube` MCP tools or `sonar context` aren't available yet (e.g. the
token was bound after boot), run once:

```bash
sonar integrate claude --non-interactive        # add --project <key> to scope it
```

Verify with `sonar auth status` (should show **Connected**) and
`sonar context` (should list available context, not "not installed").

## Already configured

- **Credentials**: `SONARQUBE_CLI_TOKEN` is a proxy placeholder inside the
  container, never the real token. Do **not** read or print it — the sbx proxy
  swaps in the real value on the `Authorization: Bearer` header for outbound
  calls to SonarQube Cloud (`$SONARQUBE_CLI_SERVER`). It never exists in the
  container.
- **Environment**: `SONARQUBE_CLI_SERVER` (region), `SONARQUBE_CLI_ORG`
  (organization), and `SONAR_PROJECT_KEY` (optional) are exported.
- **CLI on PATH**: `sonar` is linked into `~/.local/bin`.
- **Network**: egress is allowed to SonarQube Cloud (`sonarcloud.io` /
  `sonarqube.us` + `api.*`) and the CLI/analyzer download hosts.

## The Vortex loop

1. **Before writing code**, pull project context — use the `sonarqube` MCP
   tools, or `sonar context` — for coding guidelines, third-party dependency
   health (before adding/bumping a package), architecture constraints, and
   semantic navigation. This front-loads the right constraints so you generate
   compliant code on the first pass.
2. **After each change**, verify from the terminal:

   ```bash
   sonar analyze agentic        # server-side Vortex analysis of the change
   sonar analyze secrets        # scan the diff/files for hardcoded secrets
   sonar quality-gate status    # is the project still passing its gate?
   sonar list issues            # issues Sonar found, to fix before finishing
   ```

3. **Fix what Sonar reports** and re-run until analysis is clean and the
   quality gate passes. Treat a failing quality gate or a new blocker/critical
   issue as a task that is not yet done.

Prefer resolving Sonar findings over ignoring them. If a rule genuinely does
not apply, note why rather than suppressing it silently.

An operational runbook is in `~/runbooks/sonar-vortex.md`. Docs:
https://www.sonarsource.com/products/sonar-vortex/
