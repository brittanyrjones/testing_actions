#!/usr/bin/env bash

set -e -o pipefail

MAIN_BRANCH="main"

# Function to display usage
usage() {
    echo "Usage: $0 <bump_type> <release_type>"
    echo "  bump_type: major, minor, or patch"
    echo "  release_type: rc, beta, or stable"
    exit 1
}

# Function to get commit messages in a structured format
get_commit_messages() {
    local since_tag=$1
    if [[ -z "$since_tag" ]]; then
        git log --reverse --format="%h %s%n%b" | while read -r line; do
            if [[ $line =~ ^[a-f0-9]{7} ]]; then
                echo "- $line"
            elif [[ -n "$line" ]]; then
                echo "  $line"
            fi
        done
    else
        git log --reverse --format="%h %s%n%b" "${since_tag}..HEAD" | while read -r line; do
            if [[ $line =~ ^[a-f0-9]{7} ]]; then
                echo "- $line"
            elif [[ -n "$line" ]]; then
                echo "  $line"
            fi
        done
    fi
}

# Function to categorize changes
categorize_changes() {
    local changes=$1
    local added=""
    local changed=""
    local deprecated=""
    local removed=""
    local fixed=""
    local security=""

    while IFS= read -r line; do
        if [[ $line =~ ^-[[:space:]]*[a-f0-9]{7}[[:space:]]*[Aa]dd ]]; then
            added+="$line"$'\n'
        elif [[ $line =~ ^-[[:space:]]*[a-f0-9]{7}[[:space:]]*[Cc]hange ]]; then
            changed+="$line"$'\n'
        elif [[ $line =~ ^-[[:space:]]*[a-f0-9]{7}[[:space:]]*[Dd]eprecate ]]; then
            deprecated+="$line"$'\n'
        elif [[ $line =~ ^-[[:space:]]*[a-f0-9]{7}[[:space:]]*[Rr]emove ]]; then
            removed+="$line"$'\n'
        elif [[ $line =~ ^-[[:space:]]*[a-f0-9]{7}[[:space:]]*[Ff]ix ]]; then
            fixed+="$line"$'\n'
        elif [[ $line =~ ^-[[:space:]]*[a-f0-9]{7}[[:space:]]*[Ss]ecurity ]]; then
            security+="$line"$'\n'
        fi
    done <<< "$changes"

    echo "### Added"$'\n'"$added"
    echo "### Changed"$'\n'"$changed"
    echo "### Deprecated"$'\n'"$deprecated"
    echo "### Removed"$'\n'"$removed"
    echo "### Fixed"$'\n'"$fixed"
    echo "### Security"$'\n'"$security"
}

# Function to update README.md with latest version and release notes
update_readme() {
    local version=$1
    local changes=$2
    local readme_file="README.md"
    
    # Check if README.md exists
    if [ ! -f "$readme_file" ]; then
        echo "Error: README.md not found"
        exit 1
    fi

    # Create a temporary file for the new content
    {
        # Copy the header section (everything before the first ##)
        sed -n '1,/^##/p' "$readme_file" | sed '$d'
        
        # Add version information
        echo "## Version $version"
        echo ""
        echo "### Latest Changes"
        echo ""
        echo "$changes"
        echo ""
        
        # Add the rest of the file (everything after the first ##)
        sed -n '/^##/,$p' "$readme_file" | sed '1d'
    } > "${readme_file}.new"
    
    mv "${readme_file}.new" "$readme_file"
}

# Function to ensure pyproject.toml has proper documentation settings
check_pyproject_docs() {
    local pyproject_file="pyproject.toml"
    
    # Check if pyproject.toml exists
    if [ ! -f "$pyproject_file" ]; then
        echo "Error: pyproject.toml not found"
        exit 1
    }

    # Check for long description configuration
    if ! grep -q "long-description" "$pyproject_file"; then
        echo "Warning: long-description not configured in pyproject.toml"
        echo "Add the following to your [project] section:"
        echo 'long-description = { file = "README.md", content-type = "text/markdown" }'
    fi

    # Check for documentation URL
    if ! grep -q "documentation" "$pyproject_file"; then
        echo "Warning: documentation URL not configured in pyproject.toml"
        echo "Add the following to your [project.urls] section:"
        echo 'documentation = "https://your-package.readthedocs.io/"'
    fi
}

# Check if required arguments are provided
if [ "$#" -ne 2 ]; then
    usage
fi

BUMP_TYPE=$1
RELEASE_TYPE=$2

# Validate bump type
if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo "Error: bump_type must be one of: major, minor, patch"
    usage
fi

# Validate release type
if [[ ! "$RELEASE_TYPE" =~ ^(rc|beta|stable)$ ]]; then
    echo "Error: release_type must be one of: rc, beta, stable"
    usage
fi

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

# Remove any pre-release suffix for version calculation
BASE_VERSION=$(echo "$CURRENT_VERSION" | sed 's/[a-z].*$//')

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

# Add release type suffix if needed
if [ "$RELEASE_TYPE" = "rc" ]; then
    NEW_VERSION="${NEW_VERSION}rc1"
elif [ "$RELEASE_TYPE" = "beta" ]; then
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

# For beta releases, just create a PR without version changes
if [ "$RELEASE_TYPE" = "beta" ]; then
    # Create an empty commit to establish the branch
    git commit --allow-empty -m "Beta testing branch for v$NEW_VERSION"
    git push origin "$BRANCH_NAME"

    # Create draft PR
    gh pr create \
        --title "Beta Testing v$NEW_VERSION" \
        --body "Beta testing branch for v$NEW_VERSION. No version changes in pyproject.toml as this is a temporary testing branch." \
        --base main \
        --head "$BRANCH_NAME" \
        --draft
    exit 0
fi

# For RC and stable releases, update version and documentation
# Check PyPI documentation requirements
check_pyproject_docs

# Update version in pyproject.toml
sed -i '' "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# Get last published tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# Generate changelog content
CHANGES=$(get_commit_messages "$LAST_TAG")
CATEGORIZED_CHANGES=$(categorize_changes "$CHANGES")

# Update CHANGELOG.md
{
    echo "# Changelog"
    echo ""
    echo "All notable changes to this project will be documented in this file."
    echo ""
    echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
    echo "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."
    echo ""
    echo "## [$NEW_VERSION] - $(date +%Y-%m-%d)"
    echo ""
    echo "$CATEGORIZED_CHANGES"
    echo ""
} > NEW_CHANGELOG.md

# If CHANGELOG.md exists, prepend new content
if [ -f CHANGELOG.md ]; then
    cat CHANGELOG.md >> NEW_CHANGELOG.md
fi
mv NEW_CHANGELOG.md CHANGELOG.md

# Update README.md with version and changes
update_readme "$NEW_VERSION" "$CATEGORIZED_CHANGES"

# Add all files for commit
git add pyproject.toml README.md CHANGELOG.md

# Commit and push changes
git commit -m "Release v$NEW_VERSION: update version and documentation"
git push origin "$BRANCH_NAME"

# Create draft PR with appropriate title based on release type
if [ "$RELEASE_TYPE" = "stable" ]; then
    PR_TITLE="Release v$NEW_VERSION"
    PR_BODY="Release version bump from v$CURRENT_VERSION to v$NEW_VERSION"
else
    PR_TITLE="$RELEASE_TYPE v$NEW_VERSION"
    PR_BODY="$RELEASE_TYPE version bump from v$CURRENT_VERSION to v$NEW_VERSION"
fi

# Create draft PR
gh pr create \
    --title "$PR_TITLE" \
    --body "$PR_BODY" \
    --base main \
    --head "$BRANCH_NAME" \
    --draft

