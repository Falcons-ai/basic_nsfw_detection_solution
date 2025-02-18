#!/bin/bash

# Define project root directory
PROJECT_ROOT="NSFW_Tutorial"

# Define folder structure
DIRECTORIES=(
    "$PROJECT_ROOT/media"
    "$PROJECT_ROOT/templates"
    "$PROJECT_ROOT/static/css"
    "$PROJECT_ROOT/static/js"
)

# Define blank files to create
FILES=(
    "$PROJECT_ROOT/app.py"
    "$PROJECT_ROOT/detect_nsfw.py"
    "$PROJECT_ROOT/requirements.txt"
    "$PROJECT_ROOT/templates/index.html"
    "$PROJECT_ROOT/templates/feed.html"
    "$PROJECT_ROOT/static/css/style.css"
    "$PROJECT_ROOT/static/css/bootstrap.min.css"
    "$PROJECT_ROOT/static/js/bootstrap.bundle.min.js"
)

# Create directories
echo "Creating project directories..."
for dir in "${DIRECTORIES[@]}"; do
    mkdir -p "$dir"
    echo "Created: $dir"
done

# Create blank files
echo "Creating blank project files..."
for file in "${FILES[@]}"; do
    touch "$file"
    echo "Created: $file"
done

# Write default content to requirements.txt
cat <<EOL > "$PROJECT_ROOT/requirements.txt"
flask
transformers
torch
pillow
EOL
echo "Added dependencies to requirements.txt"

echo "Project structure setup complete!"

