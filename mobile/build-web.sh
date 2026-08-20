#!/bin/sh
# Gather the arcade's pages into www/, which is what gets wrapped into the
# phone apps. Everything the app needs travels with it; only the games
# themselves come from the server.
#
# The pages ask for /static/..., and Capacitor serves www/ at the root, so the
# folder is kept exactly as it is on the website and nothing needs rewriting.
set -e
cd "$(dirname "$0")"

rm -rf www
mkdir -p www/static
cp -R ../static/. www/static/
cp ../static/index.html www/index.html
cp ../static/manifest.webmanifest www/manifest.webmanifest

# the service worker belongs to the website; inside the app the files are
# already on the device and it would only get in the way
rm -f www/static/sw.js

echo "www/ built:"
find www -type f | wc -l | xargs echo "  files:"
