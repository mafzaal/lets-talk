#!/bin/bash
# Script to build vector store locally
# Usage: ./scripts/build-vector-store.sh [--force-recreate]
#
# Environment variables that can be set:
#   FORCE_RECREATE   - Set to "true" to force recreation of the vector store
#   OUTPUT_DIR       - Directory to save stats and artifacts (default: ./artifacts)
#   USE_CHUNKING     - Set to "false" to disable document chunking
#   SHOULD_SAVE_STATS - Set to "false" to disable saving document statistics

# Parse command line arguments
FORCE_RECREATE=""
if [[ "$1" == "--force-recreate" ]]; then
  FORCE_RECREATE="--force-recreate"
fi

# Set output directory for artifacts (use environment variable if set)
OUTPUT_DIR=${OUTPUT_DIR:-"./artifacts"}
mkdir -p $OUTPUT_DIR

echo "Building vector store with output to $OUTPUT_DIR"
echo "Force recreate: ${FORCE_RECREATE:-false}"

# Run pipeline in CI mode
python py-src/pipeline.py $FORCE_RECREATE --ci --output-dir $OUTPUT_DIR

# Check if successful
if [ $? -eq 0 ]; then
  echo "Build successful!"
  
  # Create a zip of the vector store
  if [ -d "./db/vector_store_4" ]; then
    echo "Creating vector store zip file in $OUTPUT_DIR"
    cd db
    zip -r ../$OUTPUT_DIR/vector_store.zip vector_store_4
    cd ..
    echo "Vector store zip created at $OUTPUT_DIR/vector_store.zip"
  fi
  
  echo "Artifacts available in $OUTPUT_DIR:"
  ls -la $OUTPUT_DIR
else
  echo "Build failed!"
  exit 1
fi
