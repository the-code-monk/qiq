"""Qiq configuration"""

__version__ = "0.0.2"

# python imports
import platform

# pip imports
from colorama import init, Fore, Back, Style

# Initialize colorama
init(autoreset=True)

# Different paths and files required for qiq
QIQ_DIR = "qiq"
QIQ_VENV_DIR = ".qiq"
QIQ_CONFIG_DIR = "qiq-config"
QIQ_CACHE_DIR = "qiq-cache"
QIQ_PACKAGES_DIR = "qiq-packages"
QIQ_REQ_TIME_TXT_FILE = "req_time.txt"
QIQ_INI_FILE = "qiq.ini"

if platform.system() == "Windows":
    QIQ_IMPORTER_FILE = "windows.json"
elif platform.system() == "Linux":
    QIQ_IMPORTER_FILE = "linux.json"
elif platform.system() == "Darwin":
    QIQ_IMPORTER_FILE = "darwin.json"
else:
    raise NotImplementedError(
        f"Steno's hotkey sender isn't implemented for {platform.system()!r} yet "
        "(Windows and Linux are supported)."
    )

# colorama colors
RED = Fore.RED
GREEN = Fore.GREEN
YELLOW = Fore.YELLOW
CYAN = Fore.CYAN
BLUE = Fore.BLUE
MAGENTA = Fore.MAGENTA
ORANGE = '\033[38;5;208m'
RESET = Style.RESET_ALL