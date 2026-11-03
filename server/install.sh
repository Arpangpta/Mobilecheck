#!/data/data/com.termux/files/usr/bin/bash
# Installs phone-server. Run in Termux:
#   curl -fsSL https://raw.githubusercontent.com/Arpangpta/Mobilecheck/room-sensor/server/install.sh | bash
set -e
echo "== Installing nginx, Cloudflare tunnel and tools (a few minutes) =="
yes | pkg install nginx cloudflared git jq termux-api resolv-conf curl >/dev/null 2>&1 \
  || pkg install -y nginx cloudflared git jq termux-api resolv-conf curl
curl -fsSL https://raw.githubusercontent.com/Arpangpta/Mobilecheck/room-sensor/server/phone-server -o "$PREFIX/bin/phone-server"
chmod +x "$PREFIX/bin/phone-server"
if ! grep -q "^portfolio	" "$HOME/.phone-server/sites.tsv" 2>/dev/null; then
  phone-server add portfolio https://github.com/Arpangpta/Mobilecheck.git room-sensor sites/portfolio
fi
echo
echo "== Installed! =="
echo "Start your website with:   phone-server start"
echo "See all commands:          phone-server"
