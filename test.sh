#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
TEST_HOME=$(mktemp -d)
trap 'rm -rf -- "$TEST_HOME"' EXIT
run() {
  env -i HOME="$TEST_HOME" PATH="$PATH" LANG=C.UTF-8 PYTHONDONTWRITEBYTECODE=1 GIT_CONFIG_NOSYSTEM=1 GIT_TERMINAL_PROMPT=0 "$@"
}
run python3 -m unittest discover -s tests -p "test_*.py"
run bash -n examples/quickstart.sh scripts/install.sh scripts/update.sh scripts/rollback.sh scripts/status.sh scripts/uninstall.sh
