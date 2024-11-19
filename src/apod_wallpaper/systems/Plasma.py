from .Systems import Systems
from pydbus import SessionBus


class Plasma(Systems):
    def __init__(self) -> None:
        self.bus = SessionBus()
        self.plasma = self.bus.get('org.kde.plasmashell')
        # self.plasma = dbus.Interface(dbus.SessionBus().get_object('org.kde.plasmashell', '/PlasmaShell'),
        #                              dbus_interface='org.kde.PlasmaShell')

    def get_screens(self) -> list:
        return self.plasma.evaluateScript(
            "let d = desktops(); let screens=[]; for (i=0;i<d.length;i++) {if (d[i].screen >= 0) {"
            "screens.push(d[i].screen);}} print(screens);").split(",")

    # https://github.com/pashazz/ksetwallpaper
    def set_wallpaper(self, path: str, screen: int = None) -> None:
        jscript = "let allDesktops = desktops(); for (i=0;i<allDesktops.length;i++) {d = allDesktops[i];"

        if screen is not None:
            jscript += "if (d.screen == " + str(screen) + ") {"

        jscript += "d.wallpaperPlugin = 'org.kde.image';" \
                   "d.currentConfigGroup = Array('Wallpaper', 'org.kde.image', 'General');" \
                   "d.writeConfig('Image', 'file://" + path + "');}"

        if screen is not None:
            jscript += "}"

        self.plasma.evaluateScript(jscript)

    def notify(self, title: str, message: str, image: str = "", urgency: int = 0, timeout: int = 5000) -> None:
        # notify_dbus = dbus.Interface(
        #     dbus.SessionBus().get_object(notifications, "/" + notifications.replace(".", "/")), notifications)
        notify_dbus = self.bus.get("org.freedesktop.Notifications")
        notify_dbus.Notify("info", 0, image, title, message, [], {"urgency": urgency}, timeout)
        notify_dbus.Quit()
