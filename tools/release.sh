#!/usr/bin/env bash
# MatVerse Organism release script.
# Usage: tools/release.sh <version>
# Example: tools/release.sh 3.7.0
#
# This script:
#   1. Verifies the test suite is green
#   2. Verifies the package compiles
#   3. Computes the SHA-256 fingerprint of every artifact
#   4. Tags the commit
#   5. (Optional) Pushes the tag
#   6. (Optional) Triggers a GitHub release
#
# IMPORTANT: this script does NOT auto-publish to Zenodo, Hugging Face,
# or blockchain. Those are operator-authorized operations.

set -euo pipefail

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 3.7.0"
    exit 1
fi

# 1. Verify tests
echo "==> Running test suite"
python3 -m unittest discover -s tests -v 2>&1 | tail -3

# 2. Verify compilation
echo "==> Verifying compilation"
python3 -m compileall -q matverse/ tests/

# 3. Compute fingerprints
echo "==> Computing SHA-256 fingerprints"
mkdir -p validation
find . -type f -not -path "./.git/*" -not -name "*.pyc" \
    -not -path "*/__pycache__/*" -not -path "./validation/mmnb/*" \
    | sort | xargs sha256sum > validation/manifest_sha256.txt
echo "  $(wc -l < validation/manifest_sha256.txt) files fingerprinted"

# 4. Update version in pyproject.toml
echo "==> Updating version markers"
sed -i "s/version = \"[0-9.]*\"/version = \"$VERSION\"/" pyproject.toml
sed -i "s/version: [0-9.]*/version: $VERSION/" CITATION.cff
sed -i "s/MatVerse Organism v[0-9.]*/MatVerse Organism v$VERSION/" \
    CITATION.cff SKILL.md README.md

# 5. Stage the version bump
git add pyproject.toml CITATION.cff SKILL.md README.md CHANGELOG.md \
        validation/manifest_sha256.txt
git status --short

# 6. Commit the version bump
echo "==> Committing version bump"
git commit -m "Bump version to v$VERSION"

# 7. Tag
echo "==> Tagging v$VERSION"
git tag -a "v$VERSION" -m "MatVerse Organism v$VERSION"

# 8. Push (optional; requires --push flag)
if [ "${2:-}" = "--push" ]; then
    echo "==> Pushing tag and commit"
    git push origin "v$VERSION"
    git push
    echo "  Tag pushed. Run 'gh release create v$VERSION' manually to publish."
else
    echo ""
    echo "To publish, run: $0 $VERSION --push"
    echo "Or manually:   git push origin v$VERSION && gh release create v$VERSION"
fi
