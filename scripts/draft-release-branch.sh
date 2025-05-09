#!/usr/bin/env bash

set -e -o pipefail

# Function to display usage
usage() {
    echo "Usage: $0 <bump_type> <release_type> [version]"
    echo "  bump_type: major, minor, or patch"
    echo "  release_type: beta or stable"
    echo "  version: optional specific version (e.g., 0.3.24-beta)"
    exit 1
}

# Check if required arguments are provided
if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
    usage
fi

BUMP_TYPE=$1
RELEASE_TYPE=$2
SPECIFIC_VERSION=$3

# Validate bump type
if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo "Error: bump_type must be one of: major, minor, patch"
    usage
fi

# Validate release type
if [[ ! "$RELEASE_TYPE" =~ ^(beta|stable)$ ]]; then
    echo "Error: release_type must be one of: beta, stable"
    usage
fi

# Get current version from pyproject.toml or use specific version
if [ -n "$SPECIFIC_VERSION" ]; then
    CURRENT_VERSION=$SPECIFIC_VERSION
else
    CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
fi

echo "Current version: $CURRENT_VERSION"
echo "Bump type: $BUMP_TYPE"
echo "Release type: $RELEASE_TYPE"

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "Error: GitHub CLI (gh) is not installed"
    exit 1
fi

# Check if user is authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo "Error: Not authenticated with GitHub. Please run 'gh auth login'"
    exit 1
fi

# Trigger the workflow
echo "Triggering release branch workflow..."
gh workflow run draft-release-branch.yml \
    -f previous_version="$CURRENT_VERSION" \
    -f release_type="$RELEASE_TYPE" \
    -f bump_type="$BUMP_TYPE"

echo "Workflow triggered! Check GitHub Actions for progress."

# Create an empty commit for non-stable releases
if [ "$RELEASE_TYPE" != "stable" ]; then
    git commit --allow-empty -m "Release v$CURRENT_VERSION"
else
    # For stable releases, commit changelog and version updates
    git add CHANGELOG.md pyproject.toml
    git commit -m "Release v$CURRENT_VERSION"
fi

