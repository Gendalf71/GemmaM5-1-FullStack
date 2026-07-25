# Publish the repository to Gendalf71 through SSH

The canonical repository is `Gendalf71/GemmaM5-1-FullStack`, public, with default branch `main`. Create it without a generated README, `.gitignore` or license because the package already contains those files.

## 1. Create a dedicated key

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
ssh-keygen -t ed25519 \
  -C "YOUR_VERIFIED_GITHUB_EMAIL" \
  -f ~/.ssh/id_ed25519_github_gendalf71_m5
```

Use a passphrase. Add the private key to the macOS keychain:

```bash
eval "$(ssh-agent -s)"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519_github_gendalf71_m5
ssh-add -l
```

## 2. Add an SSH alias

Back up an existing configuration before editing it:

```bash
[ ! -f ~/.ssh/config ] || cp -p ~/.ssh/config ~/.ssh/config.backup-$(date +%Y%m%d-%H%M%S)
```

Append this block to `~/.ssh/config`:

```sshconfig
Host github-gendalf71
  HostName github.com
  User git
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519_github_gendalf71_m5
  IdentitiesOnly yes
```

Then set permissions:

```bash
chmod 600 ~/.ssh/config ~/.ssh/id_ed25519_github_gendalf71_m5
chmod 644 ~/.ssh/id_ed25519_github_gendalf71_m5.pub
```

## 3. Add the public key to GitHub

```bash
pbcopy < ~/.ssh/id_ed25519_github_gendalf71_m5.pub
```

In GitHub Settings, open **SSH and GPG keys**, create an **Authentication Key**, and paste only the public key.

## 4. Verify the exact account

```bash
ssh -T git@github-gendalf71
./scripts/verify_github_known_hosts.sh ~/.ssh/known_hosts github.com
./scripts/check_github_ssh.sh github-gendalf71 Gendalf71 ~/.ssh/id_ed25519_github_gendalf71_m5
```

The authentication check is non-interactive (`BatchMode=yes`), requires strict host-key checking and has a bounded connection timeout.

At the first connection, verify GitHub's current Ed25519 host-key fingerprint:

```text
SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU
```

The response must contain `Hi Gendalf71!`. A successful GitHub SSH test normally exits with code 1 because GitHub does not provide shell access.

## 5. Prepare a repository-local Git identity

Do not change the identity of every Git repository merely for this publication. Configure the author locally after `git init` in the next section. Automated publication requires values stored in this repository's `.git/config` and intentionally rejects an inherited global identity.

Before extraction, keep the archive and its exact sidecar in the same directory and verify the outer package:

```bash
cd ~/Downloads
python3 ~/Projects/GemmaM5-1-FullStack-1.1.240/scripts/validate_checksum_sidecar.py \
  GemmaM5-1-FullStack-1.1.240.zip.sha256 GemmaM5-1-FullStack-1.1.240.zip
```

If the validator script is not yet extracted, first use `shasum -a 256 -c GemmaM5-1-FullStack-1.1.240.zip.sha256`, then run the repository validator immediately after extraction.

## 6. Extract, verify and push

Before the manual push, create the empty **public** repository `Gendalf71/GemmaM5-1-FullStack` in the GitHub web interface without a generated README, `.gitignore` or license. If the repository already exists, confirm that it is public and not archived.

Do not stage the entire working tree with a broad add command for the first publication. The dedicated staging script adds only paths declared by `SHA256SUMS` and stops if any unexpected untracked file is present.

```bash
mkdir -p ~/Projects
cd ~/Projects
unzip ~/Downloads/GemmaM5-1-FullStack-1.1.240.zip
cd GemmaM5-1-FullStack-1.1.240
chmod +x scripts/*.sh scripts/*.py examples/*.sh examples/*.py
shasum -a 256 -c SHA256SUMS
./scripts/verify_repo.sh

git init -b main
git config --local user.name "Grigoriy Dedenko"
git config --local user.email "YOUR_VERIFIED_OR_NOREPLY_GITHUB_EMAIL"
git config --local --list
./scripts/stage_release_files.sh
git status
git diff --cached --stat
git commit -m "Release GemmaM5-1 FullStack 1.1.240"
./scripts/verify_git_inventory.sh --require-clean
git remote -v
# A pre-existing unexpected origin must be reviewed; do not overwrite it blindly.
git remote add origin git@github-gendalf71:Gendalf71/GemmaM5-1-FullStack.git
git remote -v
git push -u origin main
```

## 7. Optional GitHub CLI publication

Authenticate `gh` as **Gendalf71**, not another account:

```bash
brew install gh
gh auth login
gh api user --jq .login
```

The last command must print `Gendalf71`. Use this route **instead of** the manual web-creation and push sequence. Initialize the local repository and set its local author identity first:

```bash
git init -b main
git config --local user.name "Grigoriy Dedenko"
git config --local user.email "YOUR_VERIFIED_OR_NOREPLY_GITHUB_EMAIL"
./scripts/publish_repository.sh
./scripts/publish_repository.sh --execute
```

The first command run is a non-mutating dry run that executes static repository verification. The executable path then rechecks SSH identity, `gh` identity, branch name, repository-local Git identity, the complete tracked-file inventory and the remote URL before pushing. It refuses to rewrite an unexpected existing `origin`, refuses an archived repository or a visibility mismatch, and after the push applies the canonical description, topics and `main` as the default branch.

The publication guard rejects placeholder, malformed and control-character-bearing identities; use an actually verified address or your exact GitHub `noreply` address.

## 8. Create the release asset after the first push

```bash
make package
```

Follow `docs/RELEASE.md`. First run `./scripts/create_github_release.sh` as a non-mutating dry run; only after it confirms that local `HEAD`, `origin/main`, successful CI and the release artifacts agree, run `./scripts/create_github_release.sh --execute`. Do not attach model weights.


## Model provenance after installation

```bash
make provenance
cat artifacts/model-provenance.json
```

This local report is ignored by Git and must be reviewed before publication.

The publication profile intentionally supports Public only: the Release procedure and README badge target the public `Gendalf71/GemmaM5-1-FullStack`. The script re-inspects exact `nameWithOwner`, visibility, archived state, description, the `main` branch and the complete canonical topic set after creation and after configuration.


## 9. SSH troubleshooting

- `Permission denied (publickey)`: confirm `ssh-add -l`, the public key in GitHub, and the effective alias with `ssh -G github-gendalf71`.
- Wrong account in the greeting: remove the wrong key from the agent, keep `IdentitiesOnly yes`, and rerun `./scripts/check_github_ssh.sh`.
- Duplicate `Host github-gendalf71` blocks: restore the backup and keep one canonical block; OpenSSH uses the first obtained value.
- Keychain prompt repeats: rerun `ssh-add --apple-use-keychain ~/.ssh/id_ed25519_github_gendalf71_m5`.
- Never replace an unexpected `origin` or use force-push merely to bypass an identity or inventory failure.

## Final 1.1.240 assurance commands

Before staging, run:

```bash
make sources-check
make assurance-check
./scripts/verify_repo.sh
```

`make sources-live` is an optional manual network probe and is deliberately excluded from deterministic CI.
