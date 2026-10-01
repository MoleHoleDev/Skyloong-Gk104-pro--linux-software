import os
import sys
import shutil
import glob
import subprocess
import re
from typing import Dict, List, Tuple, Any, Optional

UDEV_RULES_CONTENT = """# Skyloong / Semitek GK Series Keyboards (GK104 Pro, GK6X, etc.)
# Allow non-root users access to USB and HIDRAW devices
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
"""

UDEV_RULE_PATH = "/etc/udev/rules.d/99-skyloong.rules"


class SystemChecker:
    """Manages diagnostics, dependencies and installation for Skyloong Linux environment."""

    @staticmethod
    def detect_package_manager() -> Tuple[Optional[str], Optional[str]]:
        """Detect the system's package manager and mono install command."""
        if shutil.which("pacman"):
            return "pacman", "pacman -S --noconfirm mono"
        elif shutil.which("apt-get"):
            return "apt", "apt-get update && apt-get install -y mono-runtime mono-complete"
        elif shutil.which("dnf"):
            return "dnf", "dnf install -y mono-core mono-devel"
        elif shutil.which("zypper"):
            return "zypper", "zypper install -y mono-core"
        return None, None

    @staticmethod
    def check_mono() -> Dict[str, Any]:
        """Check if Mono runtime is installed and working."""
        mono_path = shutil.which("mono")
        if not mono_path:
            return {
                "installed": False,
                "version": None,
                "path": None,
                "description": "Środowisko Mono (wymagane do flashowania profili i mapowania klawiszy przez GK6X)"
            }
        
        try:
            res = subprocess.run(["mono", "--version"], capture_output=True, text=True, timeout=5)
            first_line = res.stdout.split("\n")[0] if res.stdout else "Mono installed"
            return {
                "installed": True,
                "version": first_line,
                "path": mono_path,
                "description": "Środowisko Mono"
            }
        except Exception as e:
            return {
                "installed": True,
                "version": str(e),
                "path": mono_path,
                "description": "Środowisko Mono"
            }

    @staticmethod
    def check_udev_rules() -> Dict[str, Any]:
        """Check if Skyloong udev rules are installed in /etc/udev/rules.d/."""
        rule_files = glob.glob("/etc/udev/rules.d/*skyloong*.rules") + \
                     glob.glob("/etc/udev/rules.d/*gk6x*.rules") + \
                     glob.glob("/usr/lib/udev/rules.d/*skyloong*.rules")

        has_rule = False
        valid_path = None
        for rf in rule_files:
            try:
                content = open(rf, "r").read()
                if "1ea7" in content or "32e3" in content:
                    has_rule = True
                    valid_path = rf
                    break
            except Exception:
                pass

        return {
            "installed": has_rule,
            "path": valid_path if has_rule else UDEV_RULE_PATH,
            "description": "Reguły Udev (uprawnienia zapisu/odczytu USB/hidraw bez roota)"
        }

    @staticmethod
    def check_hidraw_permissions() -> Dict[str, Any]:
        """Check if keyboard hidraw nodes have read/write permissions for current user."""
        skyloong_nodes = []
        accessible_nodes = []
        
        # Check hidraw nodes belonging to 1ea7 / 32e3
        for hid_path in sorted(glob.glob("/sys/class/hidraw/hidraw*")):
            uevent_f = os.path.join(hid_path, "device", "uevent")
            if os.path.exists(uevent_f):
                try:
                    content = open(uevent_f).read()
                    if "1EA7" in content or "1ea7" in content or "32E3" in content or "32e3" in content or "SEMITE" in content or "semite" in content:
                        dev_name = os.path.basename(hid_path)
                        dev_file = f"/dev/{dev_name}"
                        skyloong_nodes.append(dev_file)
                        if os.access(dev_file, os.R_OK | os.W_OK):
                            accessible_nodes.append(dev_file)
                except Exception:
                    pass

        has_access = len(skyloong_nodes) > 0 and (len(accessible_nodes) == len(skyloong_nodes))
        return {
            "found_nodes": skyloong_nodes,
            "accessible_nodes": accessible_nodes,
            "has_access": has_access if skyloong_nodes else True,
            "description": "Dostęp do urządzeń /dev/hidraw"
        }

    @classmethod
    def get_full_diagnostics(cls) -> Dict[str, Any]:
        """Run all diagnostic checks."""
        mono_status = cls.check_mono()
        udev_status = cls.check_udev_rules()
        perm_status = cls.check_hidraw_permissions()
        pkg_mgr, mono_cmd = cls.detect_package_manager()

        all_ok = mono_status["installed"] and udev_status["installed"] and perm_status["has_access"]
        
        missing_items = []
        if not mono_status["installed"]:
            missing_items.append("Mono Runtime")
        if not udev_status["installed"]:
            missing_items.append("Reguły Udev (/etc/udev/rules.d/99-skyloong.rules)")
        if not perm_status["has_access"] and udev_status["installed"]:
            missing_items.append("Uprawnienia do /dev/hidraw (wymagane przeładowanie udev lub ponowne podłączenie USB)")

        return {
            "all_ok": all_ok,
            "mono": mono_status,
            "udev": udev_status,
            "permissions": perm_status,
            "package_manager": pkg_mgr,
            "mono_install_cmd": mono_cmd,
            "missing_items": missing_items
        }

    @classmethod
    def generate_install_script(cls) -> str:
        """Generate a bash script to install all prerequisites and setup udev."""
        pkg_mgr, mono_cmd = cls.detect_package_manager()
        
        script = [
            "#!/bin/bash",
            "set -e",
            "echo '=== Instalacja komponentów Skyloong GK104 Pro ==='",
            ""
        ]
        
        if mono_cmd:
            script.append(f"echo '-> Instalowanie Mono...'")
            script.append(mono_cmd)
        
        script.append("echo '-> Konfigurowanie reguł Udev w /etc/udev/rules.d/99-skyloong.rules...'")
        script.append(f"cat << 'EOF' > {UDEV_RULE_PATH}")
        script.append(UDEV_RULES_CONTENT.strip())
        script.append("EOF")
        
        script.append("echo '-> Przeładowywanie reguł Udev i triggerowanie urządzeń...'")
        script.append("udevadm control --reload-rules || true")
        script.append("udevadm trigger || true")
        
        script.append("echo '=== Sukces! Wszystkie komponenty zostały skonfigurowane ==='")
        return "\n".join(script)

    @classmethod
    def run_installation(cls) -> Tuple[bool, str]:
        """Execute installation using pkexec or sudo."""
        script_content = cls.generate_install_script()
        tmp_script = "/tmp/skyloong_setup.sh"
        try:
            with open(tmp_script, "w", encoding="utf-8") as f:
                f.write(script_content)
            os.chmod(tmp_script, 0o755)

            # Try pkexec first (standard graphical polkit prompt)
            if shutil.which("pkexec"):
                cmd = ["pkexec", "bash", tmp_script]
            elif shutil.which("kdesu"):
                cmd = ["kdesu", f"bash {tmp_script}"]
            elif shutil.which("gksu"):
                cmd = ["gksu", f"bash {tmp_script}"]
            elif shutil.which("sudo"):
                cmd = ["sudo", "bash", tmp_script]
            else:
                return False, "Brak narzędzia do podniesienia uprawnień (pkexec / sudo)."

            res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if res.returncode == 0:
                return True, "Komponenty i uprawnienia zostały pomyślnie zainstalowane!"
            else:
                err = res.stderr or res.stdout
                return False, f"Błąd instalacji (kod {res.returncode}): {err.strip()}"
        except Exception as e:
            return False, f"Wyjątek podczas instalacji: {str(e)}"
        finally:
            if os.path.exists(tmp_script):
                try:
                    os.remove(tmp_script)
                except Exception:
                    pass


if __name__ == "__main__":
    diag = SystemChecker.get_full_diagnostics()
    print("=== Stan środowiska Skyloong ===")
    print("Wszystko gotowe:", diag["all_ok"])
    print("Mono:", diag["mono"])
    print("Udev:", diag["udev"])
    print("Uprawnienia hidraw:", diag["permissions"])
    print("Brakujące elementy:", diag["missing_items"])
    
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        print("\nUruchamianie instalacji...")
        ok, msg = SystemChecker.run_installation()
        print(f"Wynik: ok={ok}, {msg}")
