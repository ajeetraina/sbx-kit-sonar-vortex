#!/usr/bin/env bash
# Build and push the Kit v3 sonar-vortex mixin (v3/sonar-vortex) to Docker Hub.
# A v3 kit is an ordinary OCI image: BuildKit reads the descriptor's
# `# syntax=docker/sandbox-kit:3` line, pulls the kit frontend, validates the
# descriptor, builds the overlay and attaches the descriptor to the manifest. No
# sbx CLI required — just docker buildx — so this runs on a plain Linux runner.
#
#   ./scripts/push-kit-v3.sh                         # push :latest (+ version pin)
#   ./scripts/push-kit-v3.sh 0.2.0                   # push :0.2.0 (+ version pin)
#   PUSH=0 ./scripts/push-kit-v3.sh                  # build only, into an OCI layout
#   DOCKERHUB_NAMESPACE=me ./scripts/push-kit-v3.sh  # push to another namespace
#
# This is the v3 counterpart to scripts/push-kit.sh + .github/workflows/
# publish-kit.yml (which publish the repo-root v2 spec.yaml with `sbx kit push`).
# Both the v2 and v3 kits stay published: a v3 mixin only composes onto v3
# workloads, a v2 mixin only onto v2 agents.
#
# NOTE ON TAGS: the v3 kit publishes under its OWN Docker Hub image name,
# sonar-vortex-kit-v3 — fully distinct from the v2 sonar-vortex-kit — so its
# :latest never collides with the v2 publish. It also always pushes a
# :<tag>-<version> pin read from the descriptor's version: field (a bare :latest
# says nothing about which build it points at).
set -euo pipefail

# Default namespace is the Docker Hub user (ajeetraina777), not the GitHub name.
namespace="${DOCKERHUB_NAMESPACE:-${DOCKER_NAMESPACE:-ajeetraina777}}"
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
push="${PUSH:-1}"
platforms="${PLATFORMS:-linux/amd64,linux/arm64}"

kit_dir="$repo_root/v3/sonar-vortex"
descriptor="sonar-vortex.yaml"
image_name="sonar-vortex-kit-v3"
tag="${1:-${TAG:-latest}}"

command -v docker >/dev/null 2>&1 || { echo "push-kit-v3: docker not found." >&2; exit 1; }
docker buildx version >/dev/null 2>&1 || { echo "push-kit-v3: docker buildx not available." >&2; exit 1; }

# Read the descriptor's own `version:` so the pinned tag says what the image is.
version="$(sed -n 's/^version:[[:space:]]*"\{0,1\}\([0-9][^"]*\)"\{0,1\}[[:space:]]*$/\1/p' "$kit_dir/$descriptor")"
[ -n "$version" ] || { echo "push-kit-v3: $descriptor has no version: field" >&2; exit 1; }

image="docker.io/$namespace/$image_name"

if [ "$push" = "1" ]; then
  docker buildx build "$kit_dir" -f "$kit_dir/$descriptor" \
    --platform "$platforms" --push --provenance=true \
    -t "$image:$tag" -t "$image:$tag-$version"
  echo
  echo "Pushed $image:$tag (and :$tag-$version) from $kit_dir"
  echo "Consume with:  sbx run claude --kit $image:$tag-$version --kit-arg org=<your-org> ."
else
  layout="/tmp/sbx-kit-${image_name}-layout"
  rm -rf "$layout"
  docker buildx build "$kit_dir" -f "$kit_dir/$descriptor" \
    -t "$image_name:$tag-$version" \
    --output "type=oci,dest=$layout,tar=false"
  echo
  echo "Built $image_name:$tag-$version into $layout"
  echo "  kit-tck validate --layout $layout $tag-$version"
fi
