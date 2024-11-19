from .Systems import Systems
import json
import os
import shutil


class Hyprland(Systems):
    def get_screens(self) -> list:
        monitors = []
        # get active screens
        active_monitors = json.loads(os.popen("hyprctl monitors -j").read())
        # sort by x and y position so that the screens are in the correct order
        active_monitors.sort(key=lambda x: (x["x"], x["y"]))
        for monitor in active_monitors:
            monitors.append(monitor["name"])
        return monitors

    def set_wallpaper(self, path: str, screen: str) -> None:
        if shutil.which("swww") is not None:
            os.popen("swww img " + path + " -o " + screen + " -t grow").read()
        else:
            value = os.popen("hyprctl hyprpaper preload \"" + path + "\"").read()
            if "ok" in value and not value.lower().startswith("couldn't connect to"):
                os.popen("hyprctl hyprpaper wallpaper \"" + screen + "," + path + "\"").read()
                os.popen("hyprctl hyprpaper unload unused").read()
            else:
                print("Error setting wallpaper:", value)

    def notify(self, title: str, message: str, image: str = "") -> None:
        if shutil.which("notify-send") is not None:
            os.system("notify-send -a '" + title + "' '" + message + "'" + (
                " -i " + image if image != "" else ""))
