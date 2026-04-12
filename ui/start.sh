#!/bin/bash
cd "$(dirname "$0")"
# Create venv and install deps if needed
[ ! -d ".venv" ] && uv venv .venv --python /usr/bin/python3 --quiet
uv pip install -q -r requirements.txt --python .venv/bin/python
echo "Starting Team Claude UI → http://localhost:8000"
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
