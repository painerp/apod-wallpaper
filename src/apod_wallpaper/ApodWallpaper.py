#!/usr/bin/env python3
import argparse
import os.path
import glob
import requests
from datetime import date, timedelta, datetime
from .systems.helpers import load_settings, save_settings, get_manager, download_image, test_connection, generate_colorscheme


def get_nasa_image(folder: str, img_date: date = date.today(), random: bool = False):
    params = {'api_key': 'DEMO_KEY'}
    if random:
        params.update({'count': 1})
    else:
        params.update({'date': img_date.strftime('%Y-%m-%d')})

    r = requests.get("https://api.nasa.gov/planetary/apod", params=params)
    if r.status_code == 200:
        info = r.json()
        if random and len(info) > 0:
            info = info[0]
        if "media_type" in info and "image" in info["media_type"]:
            file_name = date.fromisoformat(info["date"]).strftime("%d-%m-%Y")
            if not glob.glob(folder + file_name + ".*"):
                if "hdurl" in info:
                    return download_image(info["hdurl"], folder + file_name)
                elif "url" in info:
                    return download_image(info["url"], folder + file_name)
    else:
        print("failed getting image from nasa, status code:", r.status_code)


def apod_wallpaper(save_folder: str = "", multi_monitor: bool = False, random: bool = False, pywal: bool = False,
                   wallust: bool = False, use_config: bool = False):
    settings_file = os.path.join(os.path.expanduser("~"), ".config", "apodwallpaper", "config.json")

    if not os.path.isdir(os.path.dirname(settings_file)):
        os.makedirs(os.path.dirname(settings_file))

    if use_config:
        if not os.path.isfile(settings_file):
            print("no settings file found, please run apod wallpaper first to generate settings")
            exit(1)
        settings = load_settings(settings_file)
        save_folder = settings["save_folder"]
        multi_monitor = settings["multi_monitor"]
        random = settings["random"]
        pywal = True if pywal else settings["pywal"]
        wallust = True if wallust else settings["wallust"]

    if save_folder == "":
        save_folder = os.path.expanduser("~") + "/Pictures/"
        if os.path.isdir(save_folder):
            save_folder += "Apod/"
            if not os.path.isdir(save_folder):
                os.mkdir(save_folder)
        else:
            print("no savefolder folder found")
            exit(1)
    elif not save_folder.endswith("/"):
        save_folder += "/"

    if not os.path.exists(save_folder):
        print("savefolder does not exist")
        exit(1)

    manager = get_manager()
    if manager is None:
        print("failed getting manager")
        exit(1)

    images = []
    connection = test_connection()
    img_date = date.today()
    if datetime.utcnow().hour - 6 < 0:
        img_date -= timedelta(days=1)
    for screen in manager.get_screens():
        image = None
        while image is None or not os.path.isfile(image):
            possible_name = save_folder + img_date.strftime("%d-%m-%Y") + ".*"
            if glob.glob(possible_name):
                image = glob.glob(possible_name)[0]
            if connection and (random or image is None or not os.path.isfile(image)):
                image = get_nasa_image(folder=save_folder, img_date=img_date, random=random)
            if image is None or multi_monitor or not connection:
                img_date -= timedelta(days=1)
                if img_date < date.today() - timedelta(days=365):
                    print("not enough images found")
                    exit(1)
        print("setting screen", str(screen) + ":", image)
        manager.set_wallpaper(path=image, screen=screen)
        images.append(image)

    if len(images) > 0:
        if not generate_colorscheme(images[0], pywal, wallust):
            manager.notify("ApodWallpaper", "failed generating colorscheme")

        if os.path.islink(os.path.abspath(__file__)):
            nasa_icon = os.path.dirname(os.readlink(os.path.abspath(__file__))) + "/nasa.svg"
        else:
            nasa_icon = os.path.dirname(os.path.abspath(__file__)) + "/nasa.svg"

        if not os.path.isfile(nasa_icon):
            nasa_icon = ""
        manager.notify("ApodWallpaper", "updated to newest apod image", nasa_icon)

    save_settings(settings_file, {
        "save_folder": save_folder,
        "multi_monitor": multi_monitor,
        "random": random,
        "pywal": pywal,
        "wallust": wallust
    })


def main():
    parser = argparse.ArgumentParser(description='gets latest nasa apod image and sets it as a wallpaper in kde')
    parser.add_argument('-s', '--savefolder', default="", help='folder to save the images to')
    parser.add_argument('-m', '--multimonitor', help="to show yesterdays image on second screen and so on",
                        action='store_true')
    parser.add_argument('-r', '--random', help="get a random image", action='store_true')
    parser.add_argument('-p', '--pywal', help="enable pywal support", action='store_true')
    parser.add_argument('-w', '--wallust', help="enable wallust support", action='store_true')
    args = parser.parse_args()

    apod_wallpaper(args.savefolder, args.multimonitor, args.random, args.pywal, args.wallust)


if __name__ == '__main__':
    main()
