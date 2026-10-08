# syntax=docker/dockerfile:1
#
# Overlay recipe for the sonar-vortex MIXIN.
#
# v2 shipped a `files/` tree that `sbx kit push` bundled into the kit and the
# runtime dropped into the sandbox home. v3 ships the same tree as a scratch
# OVERLAY: content only, landing on whatever base the mixin is composed onto.
# The only shipped file is the operational runbook the agent-context points at
# (`~/runbooks/sonar-vortex.md`).
#
# The SonarQube CLI itself is NOT baked here: its installer fetches the `latest`
# release (no pin, no digest) and lays a native binary + a symlink into the
# agent's home, which the install hooks in sonar-vortex.yaml do at create time.
# A scratch overlay would have to reproduce that home layout on an unknown base
# and could not pin a version anyway, so the install stays a create-time hook
# (the same reasoning the lifecycle section of the migrate-kit-to-v3 skill gives
# for installers that can only fetch `latest`).
#
# DUPLICATION NOTE: this `files/` is a COPY of the repo-root `files/` (which the
# v2 kit still uses). A v3 build context is rooted at the kit directory and a
# recipe cannot COPY from outside it, so the overlay cannot reach ../../files and
# the tree has to live here too. The two copies must move together — edit the
# source once and mirror into both; `diff -rq files v3/sonar-vortex/files`
# (run from the repo root) must come back empty.
#
# Ownership (the one thing an overlay must get right): an overlay's directory
# entries OVERRIDE the base's, so /home must stay root-owned and /home/agent
# (the agent user, uid 1000) and everything under it must be uid 1000. BuildKit
# COPY lands files as root:root; the chown below starts EXACTLY at /out/home/agent
# so /out/home stays root and the agent's home subtree becomes 1000:1000.

FROM busybox:stable AS build

# Lands under a staging root mirroring the target home layout. COPY (no --chown)
# writes these as root:root; parents /out, /out/home, /out/home/agent are created
# root:root too.
COPY files/home/runbooks   /out/home/agent/runbooks

# Start the chown at the agent's home, not /out and not a level deeper: /out/home
# keeps root ownership, /out/home/agent and all shipped files become uid 1000.
RUN chown -R 1000:1000 /out/home/agent

# The overlay: pure content on scratch, plus the env-config merge.
FROM scratch
COPY --from=build /out /

# A mixin's ENV is an additive image-config field that merges at assembly, so it
# reaches the composed image; it must sit on the recipe's FINAL stage, since a
# build stage's config is discarded. The arg-driven SONARQUBE_* env resolves at
# create via each arg's `env:` field in the descriptor, not here.
ENV IS_SANDBOX=1
