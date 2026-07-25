#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "$0")" && pwd)/lib/common.sh"

execute=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --execute) execute=1 ;;
    --public) ;;
    -h|--help)
      printf '%s\n' 'Usage: scripts/publish_repository.sh [--execute] [--public]'
      exit 0
      ;;
    *) fail "Unknown argument: $1" ;;
  esac
  shift
done

owner="Gendalf71"
repo_name="GemmaM5-1-FullStack"
repo_full_name="$owner/$repo_name"
host_alias="github-gendalf71"
remote_url="git@${host_alias}:${repo_full_name}.git"
description="Repeatable and auditable local Gemma 4 26B A4B QAT setup for MacBook Air M5 (24 GB) with vision, reasoning, documents, controlled tools, MCP and local APIs. No model weights included."
topics=(gemma-4 apple-silicon macbook-air m5 lm-studio local-llm vision tool-calling mcp rag gguf qat moe metal local-ai openai-compatible)
version="$(read_release_version)"
repo_fields="nameWithOwner,visibility,isArchived,description,defaultBranchRef,repositoryTopics"

log "Publication plan"
log "Repository: $repo_full_name"
log "Visibility: public"
log "Remote: $remote_url"
log ""

if [ "$execute" -ne 1 ]; then
  "$PROJECT_ROOT/scripts/verify_repo.sh"
  log ""
  log "Dry run completed. Static repository verification passed."
  log "No Git repository, commit, remote repository, remote URL or push was created or changed."
  log "Complete docs/ru/INSTALL_GITHUB_SSH.md, then re-run with --execute."
  exit 0
fi

require_command git
cd "$PROJECT_ROOT"
if [ ! -d .git ]; then git init -b main; fi
current_branch="$(git branch --show-current)"
[ "$current_branch" = "main" ] || fail "Current branch is '$current_branch'; expected 'main'."

git_user_name="$(git config --local --get user.name || true)"
git_user_email="$(git config --local --get user.email || true)"
[ -n "$git_user_name" ] || \
  fail "Set repository-local Git identity with: git config --local user.name 'Grigoriy Dedenko'"
[ -n "$git_user_email" ] || \
  fail "Set repository-local Git email with: git config --local user.email 'YOUR_VERIFIED_OR_NOREPLY_GITHUB_EMAIL'"
python3 "$PROJECT_ROOT/scripts/validate_git_identity.py" --name "$git_user_name" --email "$git_user_email"

origin_exists=0
if git remote get-url origin >/dev/null 2>&1; then
  origin_exists=1
  existing_origin="$(git remote get-url origin)"
  [ "$existing_origin" = "$remote_url" ] || \
    fail "Existing origin is '$existing_origin', expected '$remote_url'. Refusing to rewrite it implicitly. Review the repository and run: git remote set-url origin '$remote_url'"
fi

require_command gh
"$PROJECT_ROOT/scripts/check_github_ssh.sh" \
  "$host_alias" "$owner" "$HOME/.ssh/id_ed25519_github_gendalf71_m5"
gh_login="$(gh api user --jq .login 2>/dev/null || true)"
[ "$gh_login" = "$owner" ] || \
  fail "GitHub CLI is authenticated as '${gh_login:-unknown}', not '$owner'. Run gh auth login for the correct account."

"$PROJECT_ROOT/scripts/verify_repo.sh"
"$PROJECT_ROOT/scripts/stage_release_files.sh"
if git diff --cached --quiet; then
  "$PROJECT_ROOT/scripts/verify_git_inventory.sh" --require-clean
  log "Existing clean manifest-exact commit detected; no new commit is required."
else
  git commit -m "Release GemmaM5-1 FullStack $version"
  "$PROJECT_ROOT/scripts/verify_git_inventory.sh" --require-clean
fi

repo_exists=0
if repo_json="$(gh repo view "$repo_full_name" --json "$repo_fields" 2>/dev/null)"; then
  repo_exists=1
  printf '%s\n' "$repo_json" | python3 "$PROJECT_ROOT/scripts/verify_github_repository.py" \
    --expected-name "$repo_full_name" \
    --expected-visibility public
  log "The remote GitHub repository already exists with the expected public identity."
else
  gh repo create "$repo_full_name" \
    --public \
    --description "$description"
  repo_json="$(gh repo view "$repo_full_name" --json "$repo_fields")" || \
    fail "The newly created GitHub repository could not be inspected."
  printf '%s\n' "$repo_json" | python3 "$PROJECT_ROOT/scripts/verify_github_repository.py" \
    --expected-name "$repo_full_name" \
    --expected-visibility public \
    --expected-description "$description"
fi

if [ "$origin_exists" -eq 0 ]; then
  git remote add origin "$remote_url"
fi
[ "$(git remote get-url origin)" = "$remote_url" ] || fail "Unexpected origin URL."
git push -u origin main

topic_args=()
for topic in "${topics[@]}"; do topic_args+=(--add-topic "$topic"); done
gh repo edit "$repo_full_name" \
  --default-branch main \
  --description "$description" \
  "${topic_args[@]}"

repo_json="$(gh repo view "$repo_full_name" --json "$repo_fields")" || \
  fail "The published GitHub repository could not be re-inspected."
verify_args=(
  --expected-name "$repo_full_name"
  --expected-visibility public
  --expected-description "$description"
  --expected-default-branch main
)
for topic in "${topics[@]}"; do verify_args+=(--expected-topic "$topic"); done
printf '%s\n' "$repo_json" | python3 "$PROJECT_ROOT/scripts/verify_github_repository.py" "${verify_args[@]}"

if [ "$repo_exists" -eq 0 ]; then
  log "The GitHub repository was created with public visibility."
fi
log "Publication completed. Repository description, default branch and topics were applied and verified."
