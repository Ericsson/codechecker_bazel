#!/bin/env bash

if [ -z "$PATCH_DIR" ]; then
    # PATCH_DIR not set
    exit 1
fi

TEMP_JSON_FILE=$(mktemp)
find "$PATCH_DIR" -maxdepth 1 -mindepth 1 -type d ! -name \
    "templates" -print0 | while IFS= read -r -d $'\0' PROJECT_FOLDER; do
    
    # Extract project name from folder name
    PROJECT_NAME=$(basename "$PROJECT_FOLDER")
    jq -n -c \
        --arg name "$PROJECT_NAME" \
        --arg folder "$PROJECT_FOLDER" \
        '{ name: $name, folder: $folder }' >> "$TEMP_JSON_FILE"
done
if [ -s "$TEMP_JSON_FILE" ]; then
FINAL_MATRIX_JSON="[$(paste -s -d ',' "$TEMP_JSON_FILE")]"
else
FINAL_MATRIX_JSON="[]"
fi
echo "matrix_json=$FINAL_MATRIX_JSON"
