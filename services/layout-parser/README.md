# layout-parser Docker Setup

This guide explains how to set up and manage a layout-parser Docker container.


## Initial Setup

1. Create a history file:
```bash
touch ~/.bash_history_layout-parser
```

2. Create and run the layout-parser container:
```bash
sudo docker run -it --gpus all \
    --name layout-parser \
    -v $PWD:/layout-parser \
    -v ~/.bash_history_layout-parser:/root/.bash_history \
    pytorch/pytorch:2.2.1-cuda12.1-cudnn8-devel bash
```

### Starting the Services

1. **Inside Docker Container**
```bash
# Add NVIDIA GPG key
apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub

# Update package list and install curl
apt-get update
apt-get install -y curl git

# Install Rust and Cargo
curl -LsSf https://astral.sh/uv/install.sh | sh

# Source the cargo environment
source $HOME/.local/bin/env

cd /layout-parser

# For General OCR processing
uv run main.py
```

# Container Management

### Starting the Container
```bash
sudo docker start -i layout-parser  
```

### Stopping and Cleaning Up
```bash
# Exit the container
exit

# Stop container (run this after exiting)
sudo docker stop layout-parser

# Optional: Remove the container and volume (run this after exiting)
sudo docker rm -v layout-parser
```

