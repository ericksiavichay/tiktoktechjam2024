#!/bin/bash

# Change to the backend directory and download the SAM model checkpoint
cd backend || exit
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth

# Upgrade pip
pip install --upgrade pip

pip install --ignore-installed blinker

# Install Python dependencies from remote.txt
pip install -r remote.txt
# Change back to the root directory
cd ..



# Create .env file at the root of the project
cat <<EOL > .env
LOCAL_BACKEND_PORT=5001
LOCAL_HOST=http://localhost
REMOTE_HOST=http://dummyurl.com
SERVER=local
EOL

mkdir movies

apt update
apt install snap
snap install ngrok

# create ngrok auth token env variable
echo "Please enter your ngrok auth token: "
read -r NGROK_AUTH_TOKEN
export NGROK_AUTH_TOKEN=$NGROK_AUTH_TOKEN
ngrok config add-authtoken $NGROK_AUTH_TOKEN

echo "Setup complete. Please edit the .env file to configure your settings."
