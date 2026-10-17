#!/bin/sh
# Push the committed project to a Hugging Face Docker Space.
#   deploy/push_to_hf.sh <your-hf-username> [space-name]
# Create the Space first on huggingface.co (SDK: Docker, template: Blank). When git asks for a
# password, paste a Hugging Face access token with "write" permission (Settings -> Access Tokens).
# Only COMMITTED files are pushed, so commit first.
set -e
HF_USER="$1"; SPACE="${2:-bouncer}"
[ -z "$HF_USER" ] && { echo "usage: deploy/push_to_hf.sh <hf-username> [space-name]"; exit 1; }
REPO=$(git rev-parse --show-toplevel)
TMP=$(mktemp -d)
git -C "$REPO" archive HEAD | tar -x -C "$TMP"
# Hugging Face reads Space settings from a YAML header at the top of README.md
{ printf -- '---\ntitle: Bouncer\nemoji: 🛡️\ncolorFrom: red\ncolorTo: gray\nsdk: docker\napp_port: 7860\npinned: false\n---\n\n'
  cat "$TMP/README.md"; } > "$TMP/README.hf" && mv "$TMP/README.hf" "$TMP/README.md"
cd "$TMP"
git init -q -b main && git add -A && git commit -qm "Deploy Bouncer"
git push --force "https://huggingface.co/spaces/$HF_USER/$SPACE" main
echo "Pushed. Build logs: https://huggingface.co/spaces/$HF_USER/$SPACE  (app: https://$HF_USER-$SPACE.hf.space)"
rm -rf "$TMP"
