#!/bin/bash

set -xeo pipefail

python3 -m venv /venv
set +x
source /venv/bin/activate
echo "VIRTUAL_ENV=$VIRTUAL_ENV"
set -x

pip3 install --upgrade pip
pip3 install /dist/*.whl
cd /repo
python3 -m unittest -v
