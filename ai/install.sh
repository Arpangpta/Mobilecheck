#!/data/data/com.termux/files/usr/bin/bash
# Installs phone-ai (llama.cpp + a small model) next to phone-server. Run in Termux:
#   curl -fsSL https://raw.githubusercontent.com/Arpangpta/Mobilecheck/room-sensor/ai/install.sh | bash
set -e
RAW="https://raw.githubusercontent.com/Arpangpta/Mobilecheck/room-sensor"
echo "== Installing llama.cpp and tools (a few minutes) =="
yes | pkg install llama-cpp jq curl termux-api >/dev/null 2>&1 || pkg install -y llama-cpp jq curl termux-api
curl -fsSL "$RAW/ai/phone-ai" -o "$PREFIX/bin/phone-ai"
curl -fsSL "$RAW/server/phone-server" -o "$PREFIX/bin/phone-server"   # newer phone-server knows about /ai/
chmod +x "$PREFIX/bin/phone-ai" "$PREFIX/bin/phone-server"
mkdir -p "$HOME/.phone-ai/www"
curl -fsSL "$RAW/ai/www/index.html" -o "$HOME/.phone-ai/www/index.html"
echo
echo "== Installed! =="
echo "Start the AI (first time downloads the model, ~400 MB):   phone-ai start"
echo "See all commands:                                          phone-ai"
