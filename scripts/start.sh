#! /bin/bash

set -e

DIR=$(realpath "$(dirname "$0")")
cd $DIR/..

set -o allexport
source ./.env
set +o allexport

uvicorn app.main:app --reload
