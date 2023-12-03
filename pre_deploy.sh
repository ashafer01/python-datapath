#!/bin/bash

set -xeo pipefail

if [[ -e "$(echo *venv*)" ]]; then
    source *venv*/bin/activate
else
    echo 'no venv found'
    exit 1
fi

python3 -m unittest -v
pylint -E datapath setup.py docs.py
python3 docs.py

python3 setup.py sdist
python3 setup.py bdist_wheel
