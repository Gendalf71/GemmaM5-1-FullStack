#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

execute=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --execute) execute=1 ;;
    -h|--help) printf '%s\n' 'Usage: scripts/create_github_release.sh [--execute]'; exit 0 ;;
    *) fail "Unknown argument: $1" ;;
  esac
  shift
done
for command_name in git gh shasum unzip awk python3; do require_command "$command_name"; done

owner="Gendalf71"
repo_name="GemmaM5-1-FullStack"
repo_full_name="$owner/$repo_name"
host_alias="github-gendalf71"
remote_url="git@${host_alias}:${repo_full_name}.git"
version="$(read_release_version)"
tag="v$version"
archive="$PROJECT_ROOT/dist/GemmaM5-1-FullStack-$version.zip"
sidecar="$archive.sha256"

cd "$PROJECT_ROOT"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "This directory is not a Git working tree."
[ "$(git branch --show-current)" = "main" ] || fail "Create releases only from branch main."
[ "$(git remote get-url origin 2>/dev/null || true)" = "$remote_url" ] || fail "origin must be exactly '$remote_url'."
[ -n "$(git config --local --get user.name || true)" ] || fail "Repository-local Git user.name is required to create an annotated tag."
[ -n "$(git config --local --get user.email || true)" ] || fail "Repository-local Git user.email is required to create an annotated tag."
git_user_name="$(git config --local --get user.name)"
git_user_email="$(git config --local --get user.email)"
python3 "$PROJECT_ROOT/scripts/validate_git_identity.py" --name "$git_user_name" --email "$git_user_email"

"$PROJECT_ROOT/scripts/verify_repo.sh"
"$PROJECT_ROOT/scripts/verify_git_inventory.sh" --require-clean
[ -f "$archive" ] || fail "Release archive is missing: $archive. Run make package first."
[ -f "$sidecar" ] || fail "Release checksum sidecar is missing: $sidecar. Run make package first."
python3 "$PROJECT_ROOT/scripts/validate_checksum_sidecar.py" "$sidecar" "$archive"
python3 "$PROJECT_ROOT/scripts/validate_release_zip.py" "$archive" --expected-root "GemmaM5-1-FullStack-$version" --manifest "$PROJECT_ROOT/SHA256SUMS" --repository-root "$PROJECT_ROOT"
unzip -t "$archive" >/dev/null

gh_login="$(gh api user --jq .login 2>/dev/null || true)"
[ "$gh_login" = "$owner" ] || fail "GitHub CLI is authenticated as '${gh_login:-unknown}', not '$owner'."
"$PROJECT_ROOT/scripts/check_github_ssh.sh" "$host_alias" "$owner" "$HOME/.ssh/id_ed25519_github_gendalf71_m5"
gh repo view "$repo_full_name" >/dev/null 2>&1 || fail "GitHub repository '$repo_full_name' does not exist or is inaccessible."
repo_state="$(gh repo view "$repo_full_name" --json visibility,isArchived --jq '.visibility + "\t" + (.isArchived|tostring)' 2>/dev/null)" || fail "The GitHub repository could not be inspected safely."
IFS=$'\t' read -r actual_visibility archived_state <<< "$repo_state"
actual_visibility="$(printf '%s' "$actual_visibility" | tr '[:upper:]' '[:lower:]')"
[ "$archived_state" = "false" ] || fail "The GitHub repository is archived."
[ "$actual_visibility" = "public" ] || fail "The release procedure requires the public repository profile; actual visibility is '$actual_visibility'."

local_head="$(git rev-parse HEAD)"
remote_main="$(git ls-remote --exit-code origin refs/heads/main | awk 'NR==1 {print $1}')" || fail "Unable to resolve origin/main. Push main successfully before creating a release."
[ -n "$remote_main" ] || fail "origin/main was not found."
[ "$local_head" = "$remote_main" ] || fail "Local HEAD ($local_head) does not equal origin/main ($remote_main). Refusing to tag an unverified commit."

ci_state="$(gh run list --repo "$repo_full_name" --workflow ci.yml --branch main --limit 50 --json headSha,status,conclusion --jq ".[] | select(.headSha == \"$local_head\") | [.status, .conclusion] | @tsv" 2>/dev/null | head -n 1)"
[ -n "$ci_state" ] || fail "No GitHub Actions run was found for commit $local_head."
IFS=$'\t' read -r ci_status ci_conclusion <<< "$ci_state"
[ "$ci_status" = "completed" ] && [ "$ci_conclusion" = "success" ] || fail "GitHub Actions for $local_head is status='$ci_status', conclusion='$ci_conclusion'; release requires completed/success."

local_tag_commit=""
if git show-ref --verify --quiet "refs/tags/$tag"; then
  local_tag_commit="$(git rev-list -n 1 "$tag")"
  [ "$local_tag_commit" = "$local_head" ] || fail "Local tag $tag points to $local_tag_commit, not $local_head."
fi
remote_tag_lines="$(git ls-remote --tags origin "refs/tags/$tag" "refs/tags/$tag^{}" || true)"
remote_tag_commit="$(printf '%s\n' "$remote_tag_lines" | awk -v peeled="refs/tags/$tag^{}" '$2 == peeled {print $1; exit}')"
if [ -z "$remote_tag_commit" ]; then
  remote_tag_commit="$(printf '%s\n' "$remote_tag_lines" | awk -v direct="refs/tags/$tag" '$2 == direct {print $1; exit}')"
fi
if [ -n "$remote_tag_commit" ]; then
  [ "$remote_tag_commit" = "$local_head" ] || fail "Remote tag $tag points to $remote_tag_commit, not $local_head."
fi
if gh release view "$tag" --repo "$repo_full_name" >/dev/null 2>&1; then
  fail "GitHub Release $tag already exists. Review it instead of creating a duplicate."
fi

log "Release plan"
log "Repository: $repo_full_name"
log "Commit: $local_head"
log "Tag: $tag"
log "Archive: $archive"
log "CI: completed/success"
if [ "$execute" -ne 1 ]; then
  log "Dry run completed. No tag or GitHub Release was created."
  log "Re-run with --execute after reviewing the plan."
  exit 0
fi
if [ -z "$local_tag_commit" ] && [ -z "$remote_tag_commit" ]; then
  git tag -a "$tag" -m "GemmaM5-1 FullStack $version"
fi
if [ -z "$remote_tag_commit" ]; then
  git push origin "$tag"
fi
remote_tag_lines="$(git ls-remote --tags origin "refs/tags/$tag" "refs/tags/$tag^{}")"
verified_remote_tag="$(printf '%s\n' "$remote_tag_lines" | awk -v peeled="refs/tags/$tag^{}" '$2 == peeled {print $1; exit}')"
if [ -z "$verified_remote_tag" ]; then
  verified_remote_tag="$(printf '%s\n' "$remote_tag_lines" | awk -v direct="refs/tags/$tag" '$2 == direct {print $1; exit}')"
fi
[ "$verified_remote_tag" = "$local_head" ] || fail "Remote tag verification failed after push."
gh release create "$tag" "$archive" "$sidecar" --repo "$repo_full_name" --title "GemmaM5-1 FullStack $version" --generate-notes --verify-tag
release_json="$(gh release view "$tag" --repo "$repo_full_name" --json tagName,isDraft,isPrerelease,assets)" || fail "Created Release could not be inspected."
printf '%s\n' "$release_json" | python3 "$PROJECT_ROOT/scripts/verify_github_release.py" \
  --expected-tag "$tag" \
  --archive-name "$(basename "$archive")" \
  --sidecar-name "$(basename "$sidecar")"
log "GitHub Release $tag was created from the verified origin/main commit and its assets were re-verified."
