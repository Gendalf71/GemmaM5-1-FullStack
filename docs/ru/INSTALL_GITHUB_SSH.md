# Публикация репозитория в аккаунте Gendalf71 по SSH

## 1. Параметры репозитория

```text
Owner: Gendalf71
Repository name: GemmaM5-1-FullStack
Description: Repeatable and auditable local Gemma 4 26B A4B QAT setup for MacBook Air M5 (24 GB) with vision, reasoning, documents, controlled tools, MCP and local APIs. No model weights included.
Visibility: Public
Default branch: main
```

Темы:

```text
gemma-4 apple-silicon macbook-air m5 lm-studio local-llm vision tool-calling mcp rag gguf qat moe metal local-ai openai-compatible
```

Инструкция охватывает как первый push в пустой репозиторий, так и проверенное обновление уже существующего репозитория.

## 2. Проверка существующих SSH-ключей

```bash
ls -la ~/.ssh
```

Существующие ключи не удаляйте. Для аккаунта `Gendalf71` создайте отдельную пару:

```text
~/.ssh/id_ed25519_github_gendalf71_m5
~/.ssh/id_ed25519_github_gendalf71_m5.pub
```

## 3. Создание Ed25519-ключа

Подставьте подтверждённый в GitHub адрес либо адрес `noreply` из GitHub Settings, Emails:

```bash
mkdir -p ~/.ssh
chmod 700 ~/.ssh
ssh-keygen -t ed25519 \
  -C "YOUR_VERIFIED_GITHUB_EMAIL" \
  -f ~/.ssh/id_ed25519_github_gendalf71_m5
```

Задайте парольную фразу. Приватный файл без расширения `.pub` никому не передавайте.

```bash
eval "$(ssh-agent -s)"
ssh-add --apple-use-keychain ~/.ssh/id_ed25519_github_gendalf71_m5
ssh-add -l
```

## 4. Настройка отдельного SSH alias

Перед редактированием сохраните резервную копию существующего файла:

```bash
[ ! -f ~/.ssh/config ] || cp -p ~/.ssh/config ~/.ssh/config.backup-$(date +%Y%m%d-%H%M%S)
touch ~/.ssh/config
chmod 600 ~/.ssh/config
nano ~/.ssh/config
```

Перед добавлением убедитесь, что alias ещё не определён: `grep -n "^Host github-gendalf71$" ~/.ssh/config || true`. Дублированные блоки запрещены, поскольку OpenSSH применяет первое полученное значение параметра. Добавьте один блок:

```sshconfig
Host github-gendalf71
  HostName github.com
  User git
  AddKeysToAgent yes
  UseKeychain yes
  IdentityFile ~/.ssh/id_ed25519_github_gendalf71_m5
  IdentitiesOnly yes
```

Установите права:

```bash
chmod 600 ~/.ssh/config ~/.ssh/id_ed25519_github_gendalf71_m5
chmod 644 ~/.ssh/id_ed25519_github_gendalf71_m5.pub
```

## 5. Добавление публичного ключа в GitHub

```bash
pbcopy < ~/.ssh/id_ed25519_github_gendalf71_m5.pub
```

Откройте GitHub Settings, SSH and GPG keys, New SSH key. Тип — `Authentication Key`. Вставьте только содержимое `.pub`.

## 6. Проверка сервера GitHub и точного аккаунта

```bash
ssh -T git@github-gendalf71
```

При первом подключении сверьте Ed25519 fingerprint GitHub:

```text
SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU
```

Успешный ответ обязан содержать `Hi Gendalf71! You've successfully authenticated`. Код возврата при этом обычно равен 1, поскольку GitHub не предоставляет shell.

Перед сетевым подключением сценарий читает `ssh -G` и требует эффективные `HostName github.com`, `User git`, точный `IdentityFile`, `IdentitiesOnly yes` и отсутствие `ProxyCommand`/`ProxyJump`. Автоматическая проверка не просто ищет слово `authenticated`, а сверяет точный логин:

Перед автоматической аутентификацией проверьте сохранённый Ed25519-ключ `github.com` по опубликованному GitHub fingerprint. Сценарий намеренно не доверяет одному лишь выводу `ssh-keyscan`:

```bash
./scripts/verify_github_known_hosts.sh ~/.ssh/known_hosts github.com
./scripts/check_github_ssh.sh github-gendalf71 Gendalf71 ~/.ssh/id_ed25519_github_gendalf71_m5
```

Проверка аутентификации выполняется неинтерактивно (`BatchMode=yes`), требует строгой проверки host key и имеет ограниченный тайм-аут соединения.

## 7. Подготовка локальной идентичности автора Git

Не меняйте автора сразу для всех Git-репозиториев только ради этой публикации. Локальные `user.name` и `user.email` задаются после `git init` в шаге 10. Автоматическая публикация требует именно значения из локального файла `.git/config` и намеренно не принимает унаследованную глобальную идентичность. Email не следует угадывать по имени пользователя. Публикационный guard отклоняет placeholder, некорректные адреса и управляющие символы; укажите реально подтверждённый адрес или точный GitHub-адрес `noreply`.

Перед распаковкой поместите архив и его точный sidecar в один каталог и проверьте внешний пакет:

```bash
cd ~/Downloads
shasum -a 256 -c GemmaM5-1-FullStack-1.1.240.zip.sha256
```

После распаковки дополнительно выполните `scripts/validate_checksum_sidecar.py` и внутреннюю проверку `SHA256SUMS`; несовпадение имени архива либо хеша является основанием остановиться.

## 8. Распаковка финального комплекта

```bash
mkdir -p ~/Projects
cd ~/Projects
unzip ~/Downloads/GemmaM5-1-FullStack-1.1.240.zip
cd GemmaM5-1-FullStack-1.1.240
chmod +x scripts/*.sh scripts/*.py examples/*.sh examples/*.py
```

Команда `chmod` является безопасной страховкой на случай распаковщика, который не восстановил Unix executable-биты.

Проверьте целостность и статические тесты:

```bash
shasum -a 256 -c SHA256SUMS
./scripts/verify_repo.sh
```

## 9. Создание пустого репозитория через веб-интерфейс

Создайте `Gendalf71/GemmaM5-1-FullStack` как Public. Не включайте автоматическое создание README, `.gitignore` и лицензии. Они уже находятся в архиве.

## 10. Первый commit и push по SSH

Не добавляйте всё рабочее дерево одной общей командой: она способна захватить случайный локальный файл. Специальный сценарий добавляет только файлы из `SHA256SUMS` и останавливается при обнаружении любого дополнительного untracked-пути.

```bash
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
# Если origin уже существует и отличается, остановитесь и проверьте каталог; не переписывайте его вслепую.
git remote add origin git@github-gendalf71:Gendalf71/GemmaM5-1-FullStack.git
git remote -v
git push -u origin main
```

После push проверьте README, четыре изображения, лицензию, Actions и дерево `docs/ru/`.

## 11. Альтернатива через GitHub CLI

Этот вариант применяется **вместо** ручного создания репозитория и push из шагов 9–10.

```bash
brew install gh
gh auth login
gh api user --jq .login
```

Последняя команда должна вывести строго `Gendalf71`. Затем из корня проекта сначала создайте локальный Git-репозиторий и задайте именно локальную идентичность автора:

```bash
git init -b main
git config --local user.name "Grigoriy Dedenko"
git config --local user.email "YOUR_VERIFIED_OR_NOREPLY_GITHUB_EMAIL"
./scripts/publish_repository.sh
./scripts/publish_repository.sh --execute
```

Первый запуск является немодифицирующей проверкой: он выполняет статическую верификацию репозитория, но ничего не создаёт и не меняет. Второй проверяет SSH-аккаунт, аккаунт `gh`, ветку `main`, строго локальную идентичность Git, полный tracked-инвентарь и адрес `origin`. Сценарий не переписывает неожиданный существующий `origin`, отклоняет архивный репозиторий и несовпадение visibility; после push он устанавливает каноническое описание, topics и ветку `main` по умолчанию.

## 12. Заполнение About

Описание:

```text
Repeatable and auditable local Gemma 4 26B A4B QAT setup for MacBook Air M5 (24 GB) with vision, reasoning, documents, controlled tools, MCP and local APIs. No model weights included.
```

Topics:

```text
gemma-4 apple-silicon macbook-air m5 lm-studio local-llm vision tool-calling mcp rag gguf qat moe metal local-ai openai-compatible
```

В Settings, Actions оставьте workflow с правами `contents: read`. После первого стабильного push можно добавить защиту ветки `main`.

## 13. Последующие изменения

```bash
git switch main
git pull --ff-only
git status
./scripts/verify_repo.sh
./scripts/stage_release_files.sh
git diff --cached
git commit -m "Release GemmaM5-1 FullStack 1.1.240"
./scripts/verify_git_inventory.sh --require-clean
git push
```

Не применяйте force push для обычного исправления конфликта и не добавляйте модельные веса, токены или `config/local.conf`.

## 14. Создание Release после первого push

```bash
make package
```

Далее выполните процедуру из `docs/ru/RELEASE.md`: сначала запустите немодифицирующий `./scripts/create_github_release.sh`, а после подтверждения равенства локального `HEAD`, `origin/main`, зелёного CI и релизных файлов — `./scripts/create_github_release.sh --execute`. Веса модели к релизу не прикладываются.


## Происхождение модели после установки

```bash
make provenance
cat artifacts/model-provenance.json
```

Локальный отчёт исключён из Git; перед публикацией его необходимо просмотреть.

Профиль публикации намеренно поддерживает только Public: процедура Release и README badge рассчитаны на публичный `Gendalf71/GemmaM5-1-FullStack`. Сценарий после создания и после настройки повторно проверяет точное `nameWithOwner`, visibility, archived state, description, ветку `main` и полный канонический набор topics.


## 15. Диагностика SSH

- `Permission denied (publickey)`: проверьте `ssh-add -l`, наличие публичного ключа в GitHub и эффективную конфигурацию `ssh -G github-gendalf71`.
- В приветствии указан другой аккаунт: удалите неверный ключ из агента, сохраните `IdentitiesOnly yes` и снова запустите `./scripts/check_github_ssh.sh`.
- Найдены дубли `Host github-gendalf71`: восстановите резервную копию и оставьте один канонический блок; OpenSSH применяет первое полученное значение.
- Keychain снова спрашивает ключ: повторите `ssh-add --apple-use-keychain ~/.ssh/id_ed25519_github_gendalf71_m5`.
- Не заменяйте неожиданный `origin` и не применяйте force-push ради обхода отказа идентичности или инвентаря.

## Финальные assurance-команды 1.1.240

До staging выполните:

```bash
make sources-check
make assurance-check
./scripts/verify_repo.sh
```

`make sources-live` — необязательная ручная сетевая проверка; она намеренно исключена из детерминированного CI.
