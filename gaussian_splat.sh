#!/bin/bash

# Check if filename argument is provided
if [ $# -eq 0 ]; then
    echo "Please provide an input video file"
    echo "Usage: $0 <video_file> [fps]"
    exit 1
fi

INPUT_FILE=$1
# Set default FPS if not provided
FPS=${2:-2}
# Extract filename without extension
FILENAME=$(basename "$INPUT_FILE" | sed 's/\.[^.]*$//')

# Create unique directories for this run
DATA_DIR="data_${FILENAME}"
MODEL_DIR="model_${FILENAME}"

rm -rf "${DATA_DIR}/input"
rm -rf "${MODEL_DIR}"
mkdir -p "${DATA_DIR}/input"

ffmpeg -i "$INPUT_FILE" -vf fps=${FPS} "${DATA_DIR}/input/frame_%04d.png"

python gaussian-splatting/convert.py -s "${DATA_DIR}"

python gaussian-splatting/train.py -s "${DATA_DIR}" -m "${MODEL_DIR}" --iterations 7000

tar -czvf "${MODEL_DIR}.tar.gz" "${MODEL_DIR}"
