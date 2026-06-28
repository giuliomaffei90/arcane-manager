#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

APP_NAME="Arcane Manager"
REPO="${REPO:-giuliomaffei90/arcane-manager}"
BUMP="minor"
DRY_RUN=0

usage() {
  cat <<USAGE
Usage: $0 [--bump major|minor|patch] [--repo owner/name] [--dry-run]

Publishes a versioned GitHub Release DMG.
Default bump is minor: v0.5 -> v0.6.
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --bump)
      BUMP="${2:-}"
      shift 2
      ;;
    --bump=*)
      BUMP="${1#--bump=}"
      shift
      ;;
    --repo)
      REPO="${2:-}"
      shift 2
      ;;
    --repo=*)
      REPO="${1#--repo=}"
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$BUMP" in
  major|minor|patch) ;;
  *)
    echo "Invalid bump '$BUMP'. Use major, minor, or patch." >&2
    exit 2
    ;;
esac

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI 'gh' is required to publish releases." >&2
  exit 1
fi

if ! command -v hdiutil >/dev/null 2>&1; then
  echo "macOS 'hdiutil' is required to create the DMG." >&2
  exit 1
fi

latest_tag="$(gh release list --repo "$REPO" --limit 1 --json tagName --jq '.[0].tagName')"
if [ -z "$latest_tag" ] || [ "$latest_tag" = "null" ]; then
  echo "No GitHub releases found for $REPO." >&2
  exit 1
fi

version="${latest_tag#v}"
if [[ ! "$version" =~ '^[0-9]+(\.[0-9]+){1,2}$' ]]; then
  echo "Latest release tag '$latest_tag' is not a supported version tag." >&2
  exit 1
fi

parts=("${(@s:.:)version}")
major="${parts[1]}"
minor="${parts[2]}"
patch=""
if [ "${#parts[@]}" -eq 3 ]; then
  patch="${parts[3]}"
fi

case "$BUMP" in
  major)
    major=$((major + 1))
    minor=0
    if [ -n "$patch" ]; then
      patch=0
    fi
    ;;
  minor)
    minor=$((minor + 1))
    if [ -n "$patch" ]; then
      patch=0
    fi
    ;;
  patch)
    if [ -z "$patch" ]; then
      patch=0
    fi
    patch=$((patch + 1))
    ;;
esac

next_version="$major.$minor"
if [ -n "$patch" ]; then
  next_version="$next_version.$patch"
fi

next_tag="v$next_version"
release_title="$APP_NAME $next_version"
dmg_name="$APP_NAME $next_version.dmg"

echo "Latest release: $latest_tag"
echo "Next release:   $next_tag"
echo "DMG asset:      $dmg_name"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "Dry run only; no app build, DMG creation, or GitHub upload performed."
  exit 0
fi

"$ROOT_DIR/scripts/build_app.zsh"

if [ ! -d "$APP_NAME.app" ]; then
  echo "Expected '$APP_NAME.app' after build, but it was not found." >&2
  exit 1
fi

rm -f "$dmg_name"
hdiutil create \
  -volname "$APP_NAME $next_version" \
  -srcfolder "$APP_NAME.app" \
  -ov \
  -format UDZO \
  "$dmg_name"

if gh release view "$next_tag" --repo "$REPO" >/dev/null 2>&1; then
  gh release upload "$next_tag" "$dmg_name" --repo "$REPO" --clobber
else
  gh release create "$next_tag" "$dmg_name" \
    --repo "$REPO" \
    --title "$release_title" \
    --notes "Release $next_version"
fi

rm -f "$dmg_name"
echo "Published $next_tag and removed local DMG."
