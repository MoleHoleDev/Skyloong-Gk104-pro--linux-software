#!/usr/bin/env bash
# Skyloong GK104 Pro & GK6X Environment Setup & Udev Installer
set -e

echo "=========================================================="
echo " Skyloong GK104 Pro — Instalacja komponentów & reguł Udev"
echo "=========================================================="

# Check root / sudo
if [ "$EUID" -ne 0 ]; then
  echo "Przełączanie na uprawnienia administratora..."
  exec sudo "$0" "$@"
fi

# Detect package manager and install mono
if command -v pacman &> /dev/null; then
    echo "-> Wykryto system Arch/CachyOS/Manjaro. Instalowanie mono..."
    pacman -S --noconfirm --needed mono
elif command -v apt-get &> /dev/null; then
    echo "-> Wykryto system Debian/Ubuntu. Instalowanie mono-runtime..."
    apt-get update -qq
    apt-get install -y mono-runtime mono-complete
elif command -v dnf &> /dev/null; then
    echo "-> Wykryto system Fedora/RHEL. Instalowanie mono-core..."
    dnf install -y mono-core mono-devel
elif command -v zypper &> /dev/null; then
    echo "-> Wykryto system openSUSE. Instalowanie mono-core..."
    zypper install -y mono-core
else
    echo "⚠️ Nie rozpoznano menedżera pakietów. Upewnij się, że pakiet 'mono' jest zainstalowany."
fi

# Install udev rules
echo "-> Konfigurowanie reguł udev w /etc/udev/rules.d/99-skyloong.rules..."
cat << 'EOF' > /etc/udev/rules.d/99-skyloong.rules
# Skyloong / Semitek GK Series Keyboards (GK104 Pro, GK6X, etc.)
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="1ea7", MODE="0666", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="32e3", MODE="0666", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="04d9", MODE="0666", TAG+="uaccess"
SUBSYSTEM=="hidraw", ATTRS{idVendor}=="0c45", MODE="0666", TAG+="uaccess"

SUBSYSTEM=="usb", ATTRS{idVendor}=="1ea7", MODE="0666", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="32e3", MODE="0666", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="04d9", MODE="0666", TAG+="uaccess"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0c45", MODE="0666", TAG+="uaccess"

KERNEL=="hidraw*", ATTRS{idVendor}=="1ea7", MODE="0666", TAG+="uaccess"
KERNEL=="hidraw*", ATTRS{idVendor}=="32e3", MODE="0666", TAG+="uaccess"
KERNEL=="hidraw*", ATTRS{idVendor}=="04d9", MODE="0666", TAG+="uaccess"
KERNEL=="hidraw*", ATTRS{idVendor}=="0c45", MODE="0666", TAG+="uaccess"
EOF

# Reload udev
echo "-> Przeładowywanie reguł udev..."
udevadm control --reload-rules
udevadm trigger

echo "=========================================================="
echo "✅ Pomyślnie zainstalowano reguły udev i Mono!"
echo "Jeśli klawiatura jest podłączona, odłącz i podłącz kabel USB"
echo "lub uruchom aplikację Skyloong Studio."
echo "=========================================================="
