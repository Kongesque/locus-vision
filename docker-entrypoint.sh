#!/bin/sh
set -e

DATA_DIR=/app/backend/data

# Seed data directory on first run (volume is empty)
mkdir -p "$DATA_DIR/models" "$DATA_DIR/videos" "$DATA_DIR/archives" "$DATA_DIR/logs"

# Copy coco_classes.json if missing (image has a backup copy)
if [ ! -f "$DATA_DIR/coco_classes.json" ] && [ -f /app/backend/coco_classes.seed.json ]; then
    cp /app/backend/coco_classes.seed.json "$DATA_DIR/coco_classes.json"
fi

# Auto-generate JWT secret on first run if not set or left as placeholder
SECRET_FILE="$DATA_DIR/.jwt_secret"
if [ -z "$LOCUS_JWT_SECRET" ] || [ "$LOCUS_JWT_SECRET" = "change-me-use-openssl-rand-hex-32" ]; then
    if [ -f "$SECRET_FILE" ]; then
        export LOCUS_JWT_SECRET=$(cat "$SECRET_FILE")
    else
        export LOCUS_JWT_SECRET=$(openssl rand -hex 32)
        echo "$LOCUS_JWT_SECRET" > "$SECRET_FILE"
        chmod 600 "$SECRET_FILE"
        echo "[LocusVision] Generated new JWT secret and saved to $SECRET_FILE"
    fi
fi

exec "$@"
