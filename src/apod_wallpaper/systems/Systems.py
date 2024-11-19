from abc import ABC, abstractmethod


class Systems(ABC):
    @abstractmethod
    def get_screens(self) -> list:
        pass

    @abstractmethod
    def set_wallpaper(self, path: str, screen: str) -> None:
        pass

    @abstractmethod
    def notify(self, title: str, message: str, image: str = "") -> None:
        pass
