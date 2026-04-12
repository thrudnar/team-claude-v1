#!/bin/bash
# new-project.sh — Charter a new project
# Usage: ./new-project.sh "Project Name" "One-line description"
#
# Creates the project directory structure and registers it in the DB.
# Managed by Thoth.

set -e

if [ -z "$1" ]; then
  echo "Usage: ./new-project.sh \"Project Name\" \"Description\""
  exit 1
fi

NAME="$1"
DESC="${2:-}"
DIR="Projects/$NAME"
DB="team.db"

cd "$(dirname "$0")"

# Create directory structure
mkdir -p "$DIR/context"

# Create brief template if it doesn't exist
if [ ! -f "$DIR/brief.md" ]; then
cat > "$DIR/brief.md" <<EOF
# $NAME — Project Brief

## Objective


## Scope


## Background

See \`context/\` for supporting materials.

## Constraints & Notes


## Team
<!-- Populated by Adama as team members are assigned -->
EOF
fi

# Register in DB
sqlite3 "$DB" "
  INSERT INTO projects (name, description, status, created_at)
  VALUES ('$NAME', '$DESC', 'active', datetime('now'));
"

PROJECT_ID=$(sqlite3 "$DB" "SELECT id FROM projects WHERE name='$NAME' ORDER BY id DESC LIMIT 1;")

echo "✓ Project '$NAME' created (DB id: $PROJECT_ID)"
echo "  Directory: $DIR/"
echo "  Brief:     $DIR/brief.md"
echo "  Context:   $DIR/context/"
echo ""
echo "  Next: fill out $DIR/brief.md and drop any background files into $DIR/context/"
