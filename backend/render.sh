#!/usr/bin/env bash
set -e

pip install -r requirements.txt

curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh

mkdir -p ./bin
mv tectonic ./bin/tectonic
chmod +x ./bin/tectonic
