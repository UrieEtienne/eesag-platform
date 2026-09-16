#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
if [ ! -d "venv" ]; then python3.12 -m venv venv; fi
source venv/bin/activate
python -m pip install -r backend/requirements.txt
python backend/manage.py makemigrations churches core accounts
python backend/manage.py migrate
python backend/manage.py check
cd frontend
npm install
npm run build
echo "EESAG v26 : installation et vérifications terminées."
