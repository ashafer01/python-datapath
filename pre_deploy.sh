#!/bin/bash

set -xeo pipefail

rm -rf build dist *.egg-info

build_version='3.10'
docker pull "python:$build_version"
docker run -it --rm -v "$PWD:/repo" -w /repo "python:$build_version" '/repo/build.sh'

for version in '3.10' '3.11' '3.12'; do
    docker pull "python:$version"
    docker run -it --rm -v "$PWD/dist:/dist" -v "$PWD/test:/repo/test" -w /repo "python:$version" '/repo/test/docker_test.sh'
done
