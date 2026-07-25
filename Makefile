.DEFAULT_GOAL := verify
.PHONY: all test verify review-matrix version-check inventory preflight install download estimate load load-clean server status stop auth-check smoke benchmark-check environment provenance hardware-report fullstack assets-check package release-check cli-check sources-check sources-live assurance-check

all: verify preflight estimate

test:
	./scripts/run_repository_test_shards.sh

review-matrix:
	python3 scripts/generate_iteration_matrix.py --verify "docs/audit/iteration-matrix-$$(cat VERSION).json"

version-check:
	python3 scripts/verify_version_references.py

verify:
	./scripts/verify_repo.sh

inventory:
	./scripts/verify_git_inventory.sh --require-clean

preflight:
	./scripts/preflight.sh

install:
	./scripts/install_lm_studio.sh

download:
	./scripts/download_model.sh

estimate:
	./scripts/estimate_model.sh 8192

load:
	./scripts/load_model.sh --execute --context 8192

load-clean:
	./scripts/load_model.sh --execute --context 8192 --unload-others

server:
	./scripts/start_server.sh

status:
	./scripts/status.sh

auth-check:
	./scripts/verify_api_auth.sh

stop:
	./scripts/stop_server.sh

smoke:
	python3 tests/api_smoke_test.py --model gemma4-local

benchmark-check:
	python3 scripts/validate_benchmark.py benchmarks/m5-air-24gb.template.json --expected-repository-version "$$(cat VERSION)"

environment:
	./scripts/collect_environment.sh

provenance:
	./scripts/capture_model_provenance.sh

hardware-report:
	./scripts/capture_hardware_report.sh

fullstack:
	python3 examples/fullstack_acceptance.py

assets-check:
	python3 scripts/validate_png_assets.py docs/assets/assets-manifest.json

package:
	./scripts/build_release.sh

release-check:
	./scripts/create_github_release.sh

cli-check:
	./scripts/verify_lms_cli_contract.sh


sources-check:
	python3 scripts/verify_external_sources.py

sources-live:
	python3 scripts/verify_external_sources.py --live

assurance-check:
	python3 scripts/validate_release_assurance.py
