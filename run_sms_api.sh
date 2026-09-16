#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/sms_api"
source .venv/bin/activate
exec uvicorn main:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8010}" --reload
