#!/bin/bash
set -euo pipefail
IFS=$' \n\t'
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

function create_folder() {
    echo "creating and clearing $1..."
    mkdir -p "$1"
    touch "$1/dummy"
    rm $1/*
}

function mdtopdf() {
    for file in "$@"; do
        file_name="${file##*/}"
        file_no_extension="${file%.*}"
        echo "converting $file_name to pdf..."
        pandoc $file -o "$file_no_extension.pdf"
    done
}

create_folder "$DIR/out/students"
create_folder "$DIR/out/comparison"
create_folder "$DIR/out/gephi"

echo "loading data, creating markdown..."
cd $DIR
python3 "$DIR/main.py"

mdtopdf $DIR/out/students/*

echo "all done, enjoy!"
