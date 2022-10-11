#!/usr/bin/env bash
set -e
NOTES_VERSION=0.0.1

FULL_PATH_TO_SCRIPT="$(realpath "$0")"
SCRIPT_DIRECTORY="$(dirname "$FULL_PATH_TO_SCRIPT")"
PROJECT_BASE="$(realpath "$SCRIPT_DIRECTORY/..")"
cd $PROJECT_BASE
docker build $PROJECT_BASE -t jleobernard/pynotes:$NOTES_VERSION
docker login
docker push jleobernard/pynotes:$NOTES_VERSION
#docker logout