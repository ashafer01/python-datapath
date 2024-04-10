#!/bin/bash

set -xeo pipefail

python3 -m venv /venv
set +x
source /venv/bin/activate
echo "VIRTUAL_ENV=$VIRTUAL_ENV"
set -x
pip3 install --upgrade pip

pip3 install -r build-requirements.txt
pip3 install .
python3 -m unittest -v
pylint -E datapath setup.py docs.py
python3 docs.py

rm -rf dist/*

python3 setup.py sdist
python3 setup.py bdist_wheel

twine check dist/*
