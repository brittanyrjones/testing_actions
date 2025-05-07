#!/usr/bin/env bash

set -e -o pipefail

MAIN_BRANCH="main"

# Function to display usage
usage() {
    echo "Usage: $0 <bump_type> <beta>"
    echo "  bump_type: major, minor, or patch"
    echo "  beta: true or false"
    exit 1
}

# Check if required arguments are provided
if [ "$#" -ne 2 ]; then
    usage
fi

BUMP_TYPE=$1
BETA=$2

# Validate bump type
if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo "Error: bump_type must be one of: major, minor, patch"
    usage
fi

# Validate beta value
if [[ ! "$BETA" =~ ^(true|false)$ ]]; then
    echo "Error: beta must be true or false"
    usage
fi

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

# Remove any beta suffix for version calculation
BASE_VERSION=$(echo "$CURRENT_VERSION" | sed 's/beta.*$//')

# Split version into components
IFS='.' read -r -a VERSION_PARTS <<< "$BASE_VERSION"
MAJOR="${VERSION_PARTS[0]}"
MINOR="${VERSION_PARTS[1]}"
PATCH="${VERSION_PARTS[2]}"

# Generate new version based on bump type
case "$BUMP_TYPE" in
    major)
        NEW_VERSION="$((MAJOR + 1)).0.0"
        ;;
    minor)
        NEW_VERSION="$MAJOR.$((MINOR + 1)).0"
        ;;
    patch)
        NEW_VERSION="$MAJOR.$MINOR.$((PATCH + 1))"
        ;;
esac

# Add beta suffix if needed
if [ "$BETA" = "true" ]; then
    NEW_VERSION="${NEW_VERSION}beta"
fi

echo "Current version: $CURRENT_VERSION"
echo "New version: $NEW_VERSION"

# Check if we're on the main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "$MAIN_BRANCH" && "$CURRENT_BRANCH" != "heads/$MAIN_BRANCH" ]]; then
    echo "Error: Must be on $MAIN_BRANCH branch"
    exit 1
fi

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

# Create new branch
BRANCH_NAME="release-v$NEW_VERSION"
git checkout -b "$BRANCH_NAME"

# Update version in pyproject.toml
sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Only perform release-specific steps if not a beta release
if [ "$BETA" = "false" ]; then
    # Get last published tag
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

    # Generate changelog
    if [[ -z "$LAST_TAG" ]]; then
        # If no previous tag, get all commits
        RELEASE_NOTES=$(git log --graph --format="%h %s")
    else
        # Get commits between last tag and current tag
        RELEASE_NOTES=$(git log --graph --format="%h %s" "${LAST_TAG}..HEAD")
    fi

    # Update CHANGELOG.md
    {
        echo "## $NEW_VERSION"
        echo ""
        echo "### Changes since ${LAST_TAG:-initial release}"
        echo ""
        echo "$RELEASE_NOTES"
        echo ""
    } > NEW_CHANGELOG.md

    # Insert after the first line (# Changelog)
    awk 'NR==1{print; system("cat NEW_CHANGELOG.md"); next} 1' CHANGELOG.md > CHANGELOG.md.tmp
    mv CHANGELOG.md.tmp CHANGELOG.md
    rm NEW_CHANGELOG.md

    # Add applink file for this release
    echo "Release $NEW_VERSION" > "releasenotes/heroku_applink/v$NEW_VERSION"

    # Append release info to README.md
    echo "- Released $NEW_VERSION" >> README.md

    # Extract release notes for this version
    mkdir -p releasenotes/heroku_applink
    awk "/^## $NEW_VERSION/ {flag=1; next} /^## / {flag=0} flag" CHANGELOG.md > "releasenotes/heroku_applink/v$NEW_VERSION.md"

    # Append release notes to releasenotes/README.md
    mkdir -p releasenotes
    echo -e "\n## Release $NEW_VERSION\n" >> releasenotes/README.md
    cat "releasenotes/heroku_applink/v$NEW_VERSION.md" >> releasenotes/README.md

    # Add all files for commit
    git add pyproject.toml CHANGELOG.md README.md "releasenotes/heroku_applink/v$NEW_VERSION" releasenotes/README.md "releasenotes/heroku_applink/v$NEW_VERSION.md"

        # Commit and push changes
    git commit -m "Release v$NEW_VERSION: update pyproject, changelog, applink, and releasenotes"
    git push origin "$BRANCH_NAME"

    # Create draft PR
    gh pr create \
        --title "Release v$NEW_VERSION" \
        --body "Release version bump from v$CURRENT_VERSION to v$NEW_VERSION" \
        --base main \
        --head "$BRANCH_NAME" \
        --draft 

else
    # For beta releases, add all files
    git add .
    # Commit and push changes
    git commit -m "Pre-release v$NEW_VERSION"
    git push origin "$BRANCH_NAME"

    # Create draft PR
    gh pr create \
        --title "Pre-release v$NEW_VERSION" \
        --body "Pre-release version bump from v$CURRENT_VERSION to v$NEW_VERSION" \
        --base main \
        --head "$BRANCH_NAME" \
        --draft 
fi

