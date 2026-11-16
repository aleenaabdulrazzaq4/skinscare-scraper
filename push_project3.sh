#!/usr/bin/env bash
# Usage: ./push_project3.sh YOUR_GITHUB_USERNAME
# First create an EMPTY repo named audience-behaviour-engine on github.com (no README, no license).
set -e
U="${1:?Give your GitHub username, e.g. ./push_project3.sh aleenaabdulrazzaq4}"
cd "$(dirname "$0")/audience-behaviour-engine"
git config user.name  "$(git config --global user.name  || echo 'Your Name')"
git config user.email "$(git config --global user.email || echo 'you@example.com')"
git remote remove origin 2>/dev/null || true
git remote add origin "https://github.com/$U/audience-behaviour-engine.git"
git push -u origin main
echo "Done: https://github.com/$U/audience-behaviour-engine"
