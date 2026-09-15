# Sonar Vortex — Docker Sandboxes kit

A [Docker Sandboxes](https://docs.docker.com/ai/sandboxes/) **mixin** that adds
[Sonar Vortex](https://www.sonarsource.com/products/sonar-vortex/) to a Claude
Code sandbox. It installs the SonarQube CLI (`sonar`) and wires the SonarQube MCP
Server so the agent gets **repository-aware context before it writes code** and
**verifies every change in real time** against your SonarQube Cloud quality
profiles — using the same algorithmic analysis engine trusted in production. Your
SonarQube token is proxy-injected and **never enters the container**.

![architecture](https://raw.githubusercontent.com/ajeetraina/sbx-kit-sonar-vortex/main/docs/architecture.png)

## Use it

```bash
sbx run claude --kit docker.io/ajeetraina777/sonar-vortex-kit:latest \
  --kit-arg org=<your-org> .
```

For the US region, add `--kit-arg url=https://sonarqube.us`; to scope to a
project, add `--kit-arg project=<key>`.

## What it does

- Installs the **SonarQube CLI** (`sonar`) and links it into `~/.local/bin`.
- Runs **`sonar integrate claude`** on start to wire the **SonarQube MCP Server**,
  secrets-scanning hooks, and Vortex context tools — coding guidelines, dependency
  health, architecture constraints, semantic navigation.
- Declares one proxy-injected credential — `sonarqube` → `SONARQUBE_CLI_TOKEN`.
  Inside the container it reads as a proxy placeholder; the proxy swaps in the real
  token on the `Authorization: Bearer` header for outbound calls to SonarQube
  Cloud, so the token never enters the container.
- Sets `SONARQUBE_CLI_SERVER` / `SONARQUBE_CLI_ORG` / `SONAR_PROJECT_KEY`, allows
  egress to `sonarcloud.io` / `sonarqube.us` (+ `api.*`) and the CLI/analyzer
  download hosts, and disables CLI telemetry.

## Store your SonarQube token

SonarQube isn't a built-in sbx service, so store a **USER token** as a custom
secret bound to the SonarQube Cloud hosts (bind the bare host *and* the wildcard
— the CLI calls both, and `*` doesn't match the bare host):

```bash
sbx secret set-custom --host sonarcloud.io --host '*.sonarcloud.io' \
  --env SONARQUBE_CLI_TOKEN --value <user-token>
```

Connected mode requires a user token — project/global/scoped-org tokens do not
bind. The real token is stored encrypted host-side and swapped in by the proxy at
request time.

## Provenance

Every published tag is signed with **Sigstore** (keyless). Inspect it with:

```bash
sbx kit inspect docker.io/ajeetraina777/sonar-vortex-kit:latest
```

---

Source, full docs, and issues:
<https://github.com/ajeetraina/sbx-kit-sonar-vortex> · Apache-2.0
