import os
import shutil
import socket
import subprocess
import requests
import psutil
import json
from .Hyprland import Hyprland
#from .Plasma import Plasma


def save_settings(file: str, settings: dict) -> None:
    with open(file, 'w') as f:
        json.dump(settings, f, indent=4)


def load_settings(file: str) -> dict:
    with open(file, 'r') as f:
        return json.load(f)


def download_image(url: str, file_path: str = ""):
    res = requests.get(url, stream=True)
    if res.status_code == 200:
        ext = url.split('.')[-1].lower()
        if "content-type" in res.headers:
            ext = res.headers["content-type"].split('/')[-1].lower()
        if ext != "jpg" and ext != "png":
            ext = "jpg"
        with open(file_path + "." + ext, 'wb') as f:
            shutil.copyfileobj(res.raw, f)
            return file_path + "." + ext


def generate_colorscheme(image: str, pywal: bool = False, wallust: bool = False) -> bool:
    if pywal and shutil.which("wal") is not None:
        stdout, stderr = subprocess.Popen(["wal", "-ni", image],
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE).communicate()
        if "Error" in str(stderr):
            print("Error running pywall:", str(stderr))
            return False
    elif wallust and shutil.which("wallust") is not None:
        stdout, stderr = (subprocess.Popen(["wallust", image],
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE).
                          communicate())
        if "Error" in str(stderr):
            print("Error running wallust:", str(stderr))
            return False

    if shutil.which("waybar") is not None and pywal or wallust:
        if "waybar" in (p.name() for p in psutil.process_iter()):
            os.system("killall -SIGUSR2 waybar")
    return True


def test_connection(timeout: int = 5) -> bool:
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=timeout)
        return True
    except Exception as e:
        print("Failed getting Connection:", e)
        return False


def get_manager() -> Hyprland or None:
    session = os.environ.get('XDG_CURRENT_DESKTOP').strip()
    if session == "Hyprland":
        return Hyprland()
    # elif session == "KDE":
    #     return Plasma
    else:
        print("failed finding session:", session)
        return None
