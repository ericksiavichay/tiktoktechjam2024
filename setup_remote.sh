#!/bin/bash

# Only tested on runpod.io servers

apt install bash
# Change to the backend directory 
cd backend || exit
echo "Please enter your civit AI API key: "
read -r CIVIT_AI_API_KEY
export CIVIT_AI_API_KEY=$CIVIT_AI_API_KEY
curl -L -H "Content-Type: application/json" -H "Authorization: Bearer $CIVIT_AI_API_KEY" -o inpaint.safetensors "https://civitai.com/api/download/models/267129"

# Upgrade pip
pip install --upgrade pip
pip install --ignore-installed blinker
# Install Python dependencies from remote.txt
pip install -r remote.txt

pip uninstall -y transformers
pip install transformers
# Change back to the root directory
cd ..

# Create .env files at the root of frontend and backend directories
cat <<EOL > backend/.env
LOCAL_BACKEND_PORT=5001
LOCAL_HOST=http://localhost
SERVER=local
EOL

cat <<EOL > frontend/.env
REACT_APP_LOCAL_BACKEND_PORT=5001
REACT_APP_LOCAL_HOST=http://localhost
REACT_APP_REMOTE_HOST=http://dummyurl.com
EOL

mkdir movies


curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
	| tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
	&& echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
	| tee /etc/apt/sources.list.d/ngrok.list \
	&& apt update \
	&& apt install ngrok

apt -y install vim

# create ngrok auth token env variable
echo "Please enter your ngrok auth token: "
read -r NGROK_AUTH_TOKEN
export NGROK_AUTH_TOKEN=$NGROK_AUTH_TOKEN
ngrok config add-authtoken $NGROK_AUTH_TOKEN

echo "Setup complete. Make sure to update your LOCAL FRONTEND and BACKEND .env and your REMOTE BACKEND .env files."
