import time
import os
from tkinter import *
from tkinter import simpledialog, ttk, filedialog
from tkinter.messagebox import showwarning
from mainVariables import Settings
from mainVariables import resource_path
from rateLimiter import RateLimiter
from createFile import FileCreator


class GUI(Frame):
    def __init__(self, master=None):
        super(GUI, self).__init__()
        self._parent = master
        self._settings = Settings()
        self._requests = RateLimiter()
        self._file_creator = FileCreator(self._settings, self)

        self.role_dict = {
            "top": "TOP",
            "mid": "MIDDLE",
            "jungle": "JUNGLE",
            "bot": "BOTTOM",
            "support": "UTILITY",
            "any": "any",
        }

        self.queue_dict = {
            "Summoner's blind": 430,
            "Summoner's draft": 400,
            "Summoner's ranked solo": 420,
            "Summoner's ranked flex": 440,
        }

        self.match_type_dict = {"win": True, "lost": False, "both": "both"}

        self.create_toolbar()
        self.create_menu()
        self.create_status()
        self._parent.columnconfigure(0, weight=0)
        self._parent.columnconfigure(1, weight=0)
        self._parent.columnconfigure(2, weight=0)
        self._parent.columnconfigure(3, weight=0)
        self._parent.columnconfigure(4, weight=0)
        self._parent.rowconfigure(0, weight=0)
        self._parent.rowconfigure(2, weight=0)
        self._parent.rowconfigure(3, weight=0)
        self._parent.rowconfigure(4, weight=0)
        self._parent.rowconfigure(5, weight=0)
        self._parent.rowconfigure(6, weight=0)
        self._parent.rowconfigure(7, weight=0)
        self._parent.rowconfigure(8, weight=1)

        self.run()

    def create_toolbar(self):
        self.toolbar_images = []  # muszą być pamiętane stale
        self.toolbar = Frame(self._parent)

        image = resource_path("images\open_folder.png")
        command = self.provide_output_folder
        image = os.path.join(os.path.dirname(__file__), image)
        try:
            image = PhotoImage(file=image)
            self.toolbar_images.append(image)
            button = Button(self.toolbar, image=image, command=command)
            button.grid(row=0, column=len(self.toolbar_images) - 1)  # KOLEJNE ELEMENTY
        except TclError as err:
            print(err)  # gdy kłopoty z odczytaniem pliku
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky=EW)

    def create_menu(self):
        self.menubar = Menu(self._parent)
        self._parent["menu"] = self.menubar
        file_menu = Menu(self.menubar)
        for label, command, shortcut_text, shortcut in (
            ("Save config", self.save_config, "Ctrl+S", "<Control-s>"),
            ("Import config", self.import_config, "Ctrl+I", "<Control-i>"),
            (
                "Chose output folder",
                self.provide_output_folder,
                "Ctrl+O",
                "<Control-o>",
            ),
            (None, None, None, None),
            ("Quit", self.quit, "Ctrl+Q", "<Control-q>"),
        ):
            if label is None:
                file_menu.add_separator()
            else:
                file_menu.add_command(
                    label=label, underline=0, command=command, accelerator=shortcut_text
                )
                self._parent.bind(shortcut, command)
        self.menubar.add_cascade(label="Settings", menu=file_menu, underline=0)
        pass

    def create_status(self):
        self.status_bar = Label(
            self._parent,
            text="FEEDBACK IS HERE!",
            anchor=W,
            font="Times 14",
        )
        self.status_bar.grid(row=9, column=0, columnspan=6, sticky=EW)

    def set_status(self, txt):
        self.status_bar["text"] = txt

    @staticmethod
    def get_keys_from_value(dic, val):
        return [k for k, v in dic.items() if v == val]

    def quit(self, *args):
        self._parent.destroy()

    def update_region_label(self):
        self._region_label.set("Region: " + self._settings.get_me()["region"])

    def update_loaded_matches(self):
        self._filter_label.set(
            "Filter " + str(len(self._settings.get_matches())) + " matches:"
        )

    def update_summoner(self):
        self._summoner.set("Name: " + self._settings.get_nick())

    def update_key(self):
        if (
            self._settings.set_api_key(self._settings.get_api_key())
            == "Api key has been set successfully."
        ):
            self.api_key_label.set("Api key: valid")
        else:
            self.api_key_label.set("Api key: invalid")

    def update_available_matches(self):
        self.avaliable_matches.set(
            "Matches to load: " + str(self._settings.get_av_matches())
        )

    def update_labels(self):
        self.update_summoner()
        self.update_key()
        self.update_available_matches()
        self.update_loaded_matches()
        self.update_region_label()
        self._match_type.set(self._settings.get_type())
        self._lane.set(self._settings.get_lane())
        self._kd.set(self._settings.get_kd())
        self._region.set(self._settings.get_region())
        self._queue.set(
            self.get_keys_from_value(self.queue_dict, self._settings.get_queue())[0]
        )

    def disable_api_buttons(self):
        self.button_api["state"] = DISABLED
        self.button_username["state"] = DISABLED
        self.button_match_list["state"] = DISABLED
        self.button_load["state"] = DISABLED

    def enable_api_buttons(self):
        self.button_api["state"] = NORMAL
        self.button_username["state"] = NORMAL
        self.button_match_list["state"] = NORMAL
        self.button_load["state"] = NORMAL

    def reset_requests(self):
        self._requests.reset_counter()
        self.enable_api_buttons()

    def add_request(self, number):
        if self._requests.get_counter() == 0:
            self.after(120000, self.reset_requests)
            self._requests.increase_counter(number)
            self.__start_time = time.perf_counter()
        elif self._requests.get_counter() >= 94:
            end_time = time.perf_counter()
            showwarning(
                "REQUESTS WARNING",
                "You have reached your request limit! Api buttons disabled for: "
                + str(round(120 - (end_time - self.__start_time), 2))
                + " seconds",
            )
            self.disable_api_buttons()
        else:
            self._requests.increase_counter(number)

    def save_config(self, event=None):
        response = self._settings.save_config(
            filedialog.askdirectory(
                initialdir="./", title="Select folder where config will be saved."
            )
        )
        self.set_status(response)

    def import_config(self, event=None):
        response = self._settings.import_config(
            filedialog.askdirectory(
                initialdir="./",
                title="Select folder where you have saved previous config.",
            )
        )
        self.update_labels()
        self.set_status(response)

    def provide_api_key(self):
        result = simpledialog.askstring(
            "Input", "Provide your API key", parent=self._parent
        )
        if result is not None and len(result) >= 1:
            self.add_request(1)
            response = self._settings.set_api_key(result)
            self.set_status(response)
            if response == "Api key has been set successfully.":
                self.api_key_label.set("Api key: valid")
        else:
            self.set_status("You haven't provided anything.")

    def provide_name(self):
        result = simpledialog.askstring(
            "Input", "Provide your summoner name", parent=self._parent
        )
        if result is not None and len(result) > 0:
            self.add_request(1)
            response = self._settings.set_nick(result)
            self.set_status(response)
            if response == "Summoner name has been set to: " + result:
                self.update_summoner()
                self.update_region_label()

    def load_match_list(self):
        self.add_request(1)
        response = self._settings.load_match_list()
        self.set_status(response)
        self.update_available_matches()
        self.update_loaded_matches()

    def load_matches(self):
        response = self._settings.load_matches_info()
        self.add_request(5)
        self.set_status(response)
        self.update_available_matches()
        self.update_loaded_matches()

    def provide_output_folder(self, *args):
        directory = filedialog.askdirectory(
            initialdir="./", title="Select folder to output files to"
        )
        if directory != "":
            self.set_status("Successfully set output directory to: " + directory)
        else:
            self.set_status("You haven't chosen output directory.")
        self._settings._path = directory

    def provide_kd(self, *args):
        response = self._settings.set_min_kd(self._kd.get())
        self.set_status(response)

    def create_files(self):
        response = self._file_creator.create_files()
        self.set_status(response)

    def run(self):
        self.api_key_label = StringVar()
        self.api_key_label.set("Api key: invalid")
        api_label = Label(self._parent, textvariable=self.api_key_label, width=20)
        api_label.grid(row=1, column=0, padx=(10, 2))
        self.button_api = Button(
            self._parent, text="Set api key", command=self.provide_api_key
        )
        self.button_api.grid(row=2, column=0, pady=(2, 70), padx=(10, 2))

        queue_label = Label(self._parent, text="Queue type:")
        queue_label.grid(row=1, column=1)
        self._queue = StringVar()
        self._queue.set("Summoner's blind")
        box_queue = ttk.Combobox(self._parent, textvariable=self._queue, width=20)
        box_queue["values"] = list(self.queue_dict.keys())
        box_queue.set("Summoner's blind")
        box_queue.grid(row=2, column=1, pady=(2, 70))
        box_queue.bind(
            "<<ComboboxSelected>>",
            lambda e: self._settings.set_queue(self.queue_dict[self._queue.get()]),
        )
        self._region_label = StringVar()
        self._region_label.set("Region: none")
        Label(self._parent, textvariable=self._region_label, width=20).grid(
            row=1, column=2
        )
        self._region = StringVar()
        self._region.set("eun1")
        box_region = ttk.Combobox(self._parent, textvariable=self._region, width=4)
        box_region["values"] = ("eun1", "euw1", "la1", "la2", "na1", "ru")
        box_region.set("eun1")
        box_region.grid(row=2, column=2, pady=(2, 70))
        box_region.bind(
            "<<ComboboxSelected>>",
            lambda e: self._settings.set_region(self._region.get()),
        )

        self._summoner = StringVar()
        self._summoner.set("Name: none")
        Label(self._parent, textvariable=self._summoner, width=50).grid(row=1, column=4)
        self.button_username = Button(
            self._parent, text="Set ummoner Name", command=self.provide_name
        )
        self.button_username.grid(row=2, column=4, pady=(2, 70))

        self._loaded_matches = StringVar()
        self._loaded_matches.set("0")
        Label(self._parent, text="Load match list").grid(row=3, column=0)
        self.button_match_list = Button(
            self._parent, text="Load", command=self.load_match_list
        )
        self.button_match_list.grid(row=4, column=0, pady=(2, 70), padx=(10, 2))

        self.avaliable_matches = StringVar()
        self.avaliable_matches.set(
            "Matches to load: " + str(self._settings.get_av_matches())
        )
        Label(self._parent, textvariable=self.avaliable_matches).grid(row=5, column=4)
        self.button_load = Button(
            self._parent, text="Load 5 matches.", command=self.load_matches
        )
        self.button_load.grid(row=6, column=4)

        self._filter_label = StringVar()
        self._filter_label.set(
            "Filter " + str(len(self._settings.get_matches())) + " matches:"
        )
        Label(self._parent, textvariable=self._filter_label).grid(row=5, column=1)

        self._match_type = StringVar()
        self._match_type.set("both")
        Label(self._parent, text="Match type:").grid(row=6, column=0)
        box_match_type = ttk.Combobox(
            self._parent, textvariable=self._match_type, width=6
        )
        box_match_type["values"] = ("win", "lost", "both")
        box_match_type.set("both")
        box_match_type.grid(row=7, column=0, pady=(2, 100))
        box_match_type.bind(
            "<<ComboboxSelected>>",
            lambda e: self._settings.set_match_type(self._match_type.get()),
        )

        self._lane = StringVar()
        self._lane.set("any")
        Label(self._parent, text="Your position:").grid(row=6, column=1)
        box_lane = ttk.Combobox(self._parent, textvariable=self._lane, width=8)
        box_lane["values"] = ("top", "jungle", "mid", "bot", "support", "any")
        box_lane.set("any")
        box_lane.grid(row=7, column=1, pady=(2, 100))
        box_lane.bind(
            "<<ComboboxSelected>>",
            lambda e: self._settings.set_lane(self._lane.get()),
        )

        kd_label = Label(self._parent, text="Minimal K/D:")
        kd_label.grid(row=6, column=2)

        self._kd = StringVar()
        self._kd.set("0")
        self._kd.trace_add("write", self.provide_kd)
        field_kd = Entry(self._parent, textvariable=self._kd, width=9)
        field_kd.grid(row=7, column=2, pady=(2, 100))

        button_create_files = Button(
            self._parent,
            text="Create files",
            command=self.create_files,
            font="ms_serif 14",
        )
        button_create_files.grid(row=7, column=2)


if __name__ == "__main__":
    root = Tk("Api program")
    root.title("LoL Request Creator")
    root.geometry("920x640")
    root.option_add("*font", "ms_serif 12")
    root.resizable(True, True)
    root.minsize(920, 540)
    root.iconphoto(False, PhotoImage(file=resource_path("images\logo2.png")))
    style = ttk.Style(root)
    style.theme_use("alt")
    mp = GUI(root)
    mp.mainloop()
