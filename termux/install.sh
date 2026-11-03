#!/data/data/com.termux/files/usr/bin/bash
# Installs the Termux room sensor. Run:
#   curl -fsSL https://raw.githubusercontent.com/Arpangpta/Mobilecheck/room-sensor/termux/install.sh | bash
set -e
BASE="https://raw.githubusercontent.com/Arpangpta/Mobilecheck/room-sensor/termux"
echo "== Installing Python and Termux:API tools (a few minutes) =="
yes | pkg install python termux-api curl >/dev/null 2>&1 || pkg install -y python termux-api curl
mkdir -p "$HOME/room-sensor"
curl -fsSL "$BASE/sensor.py" -o "$HOME/room-sensor/sensor.py"
curl -fsSL "$BASE/room-sensor" -o "$PREFIX/bin/room-sensor"
chmod +x "$PREFIX/bin/room-sensor"
python "$HOME/room-sensor/sensor.py" none >/dev/null 2>&1 || true   # creates config + key
echo
echo "== Installed! Next steps =="
echo "1) room-sensor url PASTE_YOUR_EXEC_URL"
echo "2) room-sensor test"
echo "3) room-sensor start"
echo "Type  room-sensor  to see all commands."
