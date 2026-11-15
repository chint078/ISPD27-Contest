#!/bin/bash
# Check if image is ready
docker image inspect udxs/ispd27:v2 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "IMAGE_READY"
else
    echo "IMAGE_PENDING"
fi
