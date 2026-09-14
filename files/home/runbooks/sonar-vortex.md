# Sonar Vortex — sandbox runbook

Sonar Vortex gives your AI coding agent **repository-aware context before it
writes code** and **real-time verification after every change**, using the same
SonarQube analysis engine trusted in production. This kit installs the
**SonarQube CLI** (`sonar`) and, on start, runs `sonar integrate claude` to wire
the **SonarQube MCP Server**, secrets-scanning hooks, and Vortex context.

## Make sure Vortex is wired

The kit attempts `sonar integrate claude --global --non-interactive` at startup,
but that needs a valid, proxy-injected token. If it wasn't bound/valid at boot,
run once from a shell:

```bash
sonar integrate claude --non-interactive        # add --project <key> to scope it
```

Check it:

```bash
sonar --version                 # CLI present (linked into ~/.local/bin)
sonar auth status               # -> Connected, Source: env vars (SONARQUBE_CLI_*)
sonar context                   # lists available Vortex context (not "not installed")
```

## Credentials & networking (how the swap works)

- The SonarQube CLI authenticates headlessly from three env vars:
  `SONARQUBE_CLI_TOKEN` + `SONARQUBE_CLI_SERVER` + `SONARQUBE_CLI_ORG`.
- `SONARQUBE_CLI_TOKEN` is a **proxy placeholder** inside the container, never the
  real token. On outbound HTTPS to SonarQube Cloud, the sbx proxy swaps the
  placeholder in the `Authorization: Bearer` header for your real token (stored
  host-side). The CLI runs natively, trusts the proxy CA, and honors
  `HTTPS_PROXY`, so the swap is transparent.
- Egress is allowed to `sonarcloud.io` / `sonarqube.us` (+ `api.*`) and the
  CLI/analyzer download hosts. CLI telemetry (`events.sonardata.io`) is disabled
  by the kit, so it is not attempted.

## Region & organization

- `SONARQUBE_CLI_SERVER` selects the region: `https://sonarcloud.io` (EU, default)
  or `https://sonarqube.us` (US). Set it with `--kit-arg url=https://sonarqube.us`.
- `SONARQUBE_CLI_ORG` is your organization key (`--kit-arg org=<your-org>`).
- `SONAR_PROJECT_KEY` (optional, `--kit-arg project=<key>`) scopes `integrate` and
  the Vortex context to one project. The project must already have been analyzed
  on a long-lived branch in SonarQube Cloud.

## The Vortex loop

1. **Before writing code** — pull context via the `sonarqube` MCP tools or
   `sonar context`: coding guidelines, third-party dependency health (before
   adding/bumping a dependency), architecture graphs/constraints, semantic
   navigation. This front-loads the right constraints so the first pass is
   compliant.
2. **After each change** — verify from the terminal:

   ```bash
   sonar analyze agentic        # server-side Vortex analysis of the change
   sonar analyze secrets        # scan for hardcoded secrets
   sonar quality-gate status    # is the project still passing its gate?
   sonar list issues            # issues to fix before finishing
   ```

3. **Fix and re-run** until analysis is clean and the quality gate passes.

## Troubleshooting

- **`sonar: command not found`** — the kit links it into `~/.local/bin`; if
  missing, run `export PATH="$HOME/.local/share/sonarqube-cli/bin:$PATH"`.
- **401 / "Token is invalid"** — the bound token is missing, expired, or is not a
  **USER** token. Connected mode requires a user token; project/global/scoped-org
  tokens do not bind. Bind it host-side (see the kit README) and recreate the
  sandbox, then re-run `sonar integrate claude --non-interactive`.
- **`integrate` says "Not authenticated"** — `SONARQUBE_CLI_SERVER` /
  `SONARQUBE_CLI_ORG` must both be set for env-var auth. They come from the kit
  args (`url`, `org`); confirm with `printenv | grep SONARQUBE_CLI_`.
- **Empty context / project not found** — the project must exist and have been
  analyzed on a long-lived branch, and `SONARQUBE_CLI_ORG` must match the region
  (`SONARQUBE_CLI_SERVER`) where the project lives.
- **Egress blocked** — under org-managed governance the kit's allowlist is not
  applied and injection may be forced transparent; an org admin must allow the
  SonarQube host and permit interception for the token swap to happen.

Docs: <https://www.sonarsource.com/products/sonar-vortex/> ·
<https://docs.sonarsource.com/sonarqube-cli/>
