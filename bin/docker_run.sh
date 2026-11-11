#!/usr/bin/env bash
set -euo pipefail
docker run --rm -v "$PWD:/srv/jekyll/" -p "8080:8080" -it h3ct0r-site:latest
