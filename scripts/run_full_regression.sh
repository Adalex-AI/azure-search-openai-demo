#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "== Backend tests (pytest, excluding e2e) =="
python -m pytest -m "not e2e"

echo "== Frontend unit tests (vitest) =="
pushd app/frontend >/dev/null
npm test -- --run
popd >/dev/null

if [[ "${SKIP_E2E:-}" != "1" ]]; then
  echo "== E2E tests (pytest + playwright) =="
  python -m pytest -m "e2e"
else
  echo "== Skipping E2E tests (SKIP_E2E=1) =="
fi

if [[ "${SKIP_INTEGRATION:-}" != "1" ]]; then
  echo "== Integration script (test_integration.sh) =="
  ./test_integration.sh
else
  echo "== Skipping integration script (SKIP_INTEGRATION=1) =="
fi

echo "✅ Full regression run completed"
