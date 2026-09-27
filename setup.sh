#!/bin/bash
python3 -m venv venv
./venv/bin/pip install -r platform/requirements.txt
./venv/bin/pip install -r benchmark-requirements.txt
if ! command -v bwrap >/dev/null 2>&1; then
  echo "warning: install bubblewrap (bwrap) to run Parts 2B and 3" >&2
fi
