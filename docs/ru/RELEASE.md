# Процедура GitHub Release

GitHub Release создаётся отдельно от первого push. Сценарий по умолчанию работает как dry run и запрещает тегирование, пока локальный commit, `origin/main`, CI, ZIP и контрольная сумма не совпадут.

## 1. Проверка и упаковка

```bash
./scripts/verify_repo.sh
./scripts/verify_git_inventory.sh --require-clean
make package
shasum -a 256 -c dist/GemmaM5-1-FullStack-1.1.240.zip.sha256
python3 scripts/validate_checksum_sidecar.py dist/GemmaM5-1-FullStack-1.1.240.zip.sha256 dist/GemmaM5-1-FullStack-1.1.240.zip
unzip -t dist/GemmaM5-1-FullStack-1.1.240.zip
```

До распаковки проверьте структуру и точный состав архива:

```bash
python3 scripts/validate_release_zip.py \
  dist/GemmaM5-1-FullStack-1.1.240.zip \
  --expected-root GemmaM5-1-FullStack-1.1.240 \
  --manifest SHA256SUMS \
  --repository-root .
```

## 2. Dry run защищённого Release

```bash
./scripts/create_github_release.sh
```

Проверяются локальная Git-идентичность, ветка `main`, точный SSH `origin`, чистый manifest-exact инвентарь, целостность ZIP, точные аккаунты `Gendalf71` для SSH и GitHub CLI, публичное неархивированное состояние репозитория, равенство локального `HEAD` и `origin/main`, зелёный GitHub Actions для того же commit, targets локального и удалённого тегов и отсутствие дубликата Release.

## 3. Создание Release

```bash
./scripts/create_github_release.sh --execute
```

Сценарий создаёт и отправляет аннотированный тег `v1.1.240`, только если он отсутствует, проверяет удалённый target после push и прикладывает ZIP с `.sha256` через `gh release create --verify-tag`. Переназначение тега и дубликат Release запрещены. Веса модели остаются внешними.

После создания сценарий повторно читает Release через `gh release view` и требует точный тег, `isDraft=false`, `isPrerelease=false`, а также наличие ZIP и файла `.sha256` среди assets.

Профиль публикации намеренно поддерживает только Public: процедура Release и README badge рассчитаны на публичный `Gendalf71/GemmaM5-1-FullStack`. Сценарий после создания и после настройки повторно проверяет точное `nameWithOwner`, visibility, archived state, description и ветку `main`.

## Граница повторной проверки распаковки

Unit-suite выполняется на исходном дереве до упаковки. После безопасной распаковки сценарий повторяет все статические gates с `--skip-unit-tests`: точный manifest и safe-ZIP validator доказывают тождество выпущенных файлов, поэтому длительные unit checks не дублируются в той же CI-задаче. Независимый финальный аудит версии 1.1.240 дополнительно повторил все 91 unit check и на чисто распакованном архиве.
