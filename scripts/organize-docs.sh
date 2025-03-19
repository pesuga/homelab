#!/bin/bash

# Script to organize documentation files in the homelab repository
# This script will:
# 1. Archive deprecated documentation files
# 2. Rename documentation files to follow a consistent naming convention
# 3. Create a docs/archive directory if it doesn't exist

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
DOCS_DIR="$REPO_ROOT/docs"
ARCHIVE_DIR="$DOCS_DIR/archive"

# Create archive directory if it doesn't exist
mkdir -p "$ARCHIVE_DIR"

# Function to archive a file
archive_file() {
    local file="$1"
    local basename=$(basename "$file")
    echo "Archiving $basename to archive directory..."
    mv "$file" "$ARCHIVE_DIR/$basename"
}

# Function to rename a file
rename_file() {
    local old_path="$1"
    local new_name="$2"
    local new_path="$DOCS_DIR/$new_name"
    echo "Renaming $(basename "$old_path") to $new_name..."
    mv "$old_path" "$new_path"
}

# Archive deprecated files
echo "Archiving deprecated documentation files..."
[ -f "$DOCS_DIR/SUBDOMAIN_SETUP.md" ] && archive_file "$DOCS_DIR/SUBDOMAIN_SETUP.md"
[ -f "$DOCS_DIR/todo_list.md" ] && archive_file "$DOCS_DIR/todo_list.md"

# Rename files to follow consistent naming convention
echo "Renaming documentation files to follow consistent naming convention..."
[ -f "$DOCS_DIR/FLUX_SETUP.md" ] && rename_file "$DOCS_DIR/FLUX_SETUP.md" "flux_setup.md"
[ -f "$DOCS_DIR/K3S_SETUP.md" ] && rename_file "$DOCS_DIR/K3S_SETUP.md" "k3s_setup.md"
[ -f "$DOCS_DIR/SETUP.md" ] && rename_file "$DOCS_DIR/SETUP.md" "setup.md"

echo "Documentation organization complete!"
echo "Archived files can be found in $ARCHIVE_DIR"
