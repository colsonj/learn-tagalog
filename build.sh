#!/usr/bin/env bash
# Build TagTrain: validates curriculum, then produces the Windows exe (and a Linux binary for local testing).
set -euo pipefail
cd "$(dirname "$0")"

python3 validate.py

mkdir -p dist
echo "Building Windows amd64…"
GOOS=windows GOARCH=amd64 go build -trimpath -ldflags "-s -w -H windowsgui" -o dist/TagTrain.exe .
echo "Building Linux (for local testing)…"
go build -trimpath -ldflags "-s -w" -o dist/tagtrain-linux .
ls -lh dist/
