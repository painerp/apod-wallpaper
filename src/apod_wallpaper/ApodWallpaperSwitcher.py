#!/usr/bin/env python3
import argparse
import os
import threading

import questionary
import tkinter as tk
from PIL import ImageTk, Image, ImageFile

from .ApodWallpaper import apod_wallpaper
from .systems.helpers import load_settings, save_settings, get_manager, generate_colorscheme


class ImageGrid:
    def __init__(self, image_folder):
        self.image_folder = image_folder
        self.image_labels = []
        self.images = []
        self.cached_images = {}
        self.selected_image = None
        self.current_page = 0
        self.max_rows = 4
        self.max_columns = 4
        self.max_images = self.max_rows * self.max_columns

        self.image_size = 150

        self.root = tk.Tk()
        self.root.title("Wallpaper Chooser")
        self.root.geometry("648x648")
        self.root.bind("<Left>", self.previous_page)
        self.root.bind("<Right>", self.next_page)

        self.create_grid()

        threading.Thread(target=self.cache_next_pages).start()

        self.root.mainloop()

    def create_grid(self):
        self.images = self.get_images_from_folder()

        total_pages = (len(self.images) + self.max_images - 1) // self.max_images
        self.current_page = min(self.current_page, total_pages - 1)

        start_index = self.current_page * self.max_images
        end_index = start_index + self.max_images
        page_images = self.images[start_index:end_index]

        row_num = 0
        col_num = 0

        for image_path in page_images:
            if image_path in self.cached_images:
                cached_img = self.cached_images[image_path]
                photo = ImageTk.PhotoImage(cached_img)
            else:
                img = Image.open(image_path)
                img.thumbnail((200, 200))
                cropped_img = self.crop_to_fit(img, self.image_size, self.image_size)
                self.cached_images[image_path] = cropped_img
                photo = ImageTk.PhotoImage(cropped_img)

            image_label = tk.Label(self.root, image=photo)
            image_label.image = photo
            image_label.grid(row=row_num, column=col_num, padx=5, pady=5)
            image_label.bind("<Button-1>", lambda event, path=image_path: self.image_clicked(path))

            self.image_labels.append(image_label)

            col_num += 1
            if col_num >= self.max_columns:
                col_num = 0
                row_num += 1

        self.root.update_idletasks()

    def get_images_from_folder(self):
        image_files = []
        for file_name in os.listdir(self.image_folder):
            file_path = os.path.join(self.image_folder, file_name)
            if os.path.isfile(file_path) and file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                image_files.append(file_path)
        return image_files

    def crop_to_fit(self, image, width, height):
        aspect_ratio = min(width / image.width, height / image.height)
        new_width = int(image.width * aspect_ratio)
        new_height = int(image.height * aspect_ratio)
        resized_image = image.resize((new_width, new_height), Image.LANCZOS)

        x = (new_width - width) // 2
        y = (new_height - height) // 2
        cropped_image = resized_image.crop((x, y, x + width, y + height))

        return cropped_image

    def image_clicked(self, path):
        self.selected_image = path
        self.root.destroy()

    def previous_page(self, _):
        if self.current_page > 0:
            self.current_page -= 1
            self.clear_grid()
            self.create_grid()

    def next_page(self, _):
        if (self.current_page + 1) * self.max_images < len(self.images):
            self.current_page += 1
            self.clear_grid()
            self.create_grid()
            threading.Thread(target=self.cache_next_pages).start()

    def clear_grid(self):
        for label in self.image_labels:
            label.grid_forget()
            label.destroy()
        self.image_labels = []

    def cache_next_pages(self, amount: int = 1):
        start_index = (self.current_page + 1) * self.max_images
        end_index = start_index + (self.max_images * amount)

        if len(self.cached_images.keys()) >= len(self.images):
            return

        for index in range(start_index, end_index):
            if index >= len(self.images):
                break

            image_path = self.images[index]
            if image_path not in self.cached_images:
                img = Image.open(image_path)
                img.thumbnail((200, 200))
                cropped_img = self.crop_to_fit(img, self.image_size, self.image_size)
                self.cached_images[image_path] = cropped_img


def set_wallpaper(image: str, pywal: bool = False, wallust: bool = False) -> None:
    # set wallpaper
    manager = get_manager()
    for screen in manager.get_screens():
        manager.set_wallpaper(image, screen)

    # apply pywal or wallust
    if not generate_colorscheme(image, pywal, wallust):
        manager.notify("Wallpaper", "Failed to apply colorscheme")

    # notify user
    manager.notify("Wallpaper changed", "Wallpaper changed to " + image)


def apod_wallpaper_switcher(imagefolder: str = "", reapply: bool = False, pywal: bool = False, wallust: bool = False, multimonitor: bool = False) -> None:
    settings_file = os.path.join(os.path.expanduser("~"), ".config", "apodwallpaper", "switcher.json")

    if not os.path.isdir(os.path.dirname(settings_file)):
        os.makedirs(os.path.dirname(settings_file))

    if reapply:
        if not os.path.isfile(settings_file):
            print("no settings file found, please run without -r first")
            exit(1)
        settings = load_settings(settings_file)
        if settings["mode"] == "apod":
            apod_wallpaper(pywal=settings["pywal"], wallust=settings["wallust"], use_config=True)
        elif settings["mode"] == "image" and settings["image"] != "":
            if not os.path.isfile(settings["image"]):
                print("image not found")
                exit(1)
            set_wallpaper(settings["image"], settings["pywal"], settings["wallust"])
        return

    choices = ["use apod", "choose from apod", "choose from others"]
    answer = questionary.select("Do you want to manually set a wallpaper or use apod images?", choices=choices).ask()

    image_path = ""
    if answer == choices[0]:
        # use apod
        save_settings(settings_file, {"mode": "apod", "image": "", "multimonitor": multimonitor, "pywal": pywal, "wallust": wallust})
        apod_wallpaper(pywal=pywal, wallust=wallust, use_config=True)
        return
    elif answer == choices[1]:
        if imagefolder == "":
            image_path = os.path.realpath(os.path.join(os.path.expanduser("~"), "Pictures", "Apod"))
        else:
            image_path = imagefolder
    elif answer == choices[2]:
        if imagefolder == "":
            image_path = os.path.realpath(os.path.join(os.path.expanduser("~"), "Pictures", "Wallpapers"))
        else:
            image_path = imagefolder

    while not os.path.isdir(image_path):
        image_path = questionary.path("Please enter the path to your images", only_directories=True).ask()
    image_grid = ImageGrid(image_path)
    print("Selected image:", image_grid.selected_image)

    if image_grid.selected_image is not None:
        ImageFile.LOAD_TRUNCATED_IMAGES = True

        # save settings to file
        save_settings(settings_file, {
            "mode": "image",
            "image": image_grid.selected_image,
            "multimonitor": False,
            "pywal": pywal,
            "wallust": wallust
        })

        set_wallpaper(image_grid.selected_image, pywal, wallust)


def main():
    parser = argparse.ArgumentParser(description='handles wallpapers')
    parser.add_argument('-i', '--imagefolder', default="", help='folder to grab images from')
    parser.add_argument('-r', '--reapply', help="reapplies the last chosen settings", action='store_true')
    parser.add_argument('-p', '--pywal', help="enable pywal support", action='store_true')
    parser.add_argument('-w', '--wallust', help="enable wallust support", action='store_true')
    args = parser.parse_args()

    apod_wallpaper_switcher(args.imagefolder, args.reapply, args.pywal, args.wallust)


if __name__ == '__main__':
    main()
