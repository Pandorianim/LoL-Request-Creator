import requests
import pickle
import os
import sys

import pandas as pd

from riotwatcher import LolWatcher, ApiError
from configparser import ConfigParser


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class Settings:
    def __init__(self):
        self._api_key = "2"
        self._lol_watcher = LolWatcher(self._api_key)
        self._region = "eun1"
        self._nick = ""
        self._me = {"region": self._region}
        self._match_list = []
        self._matches = []
        self._current_index = 0
        self._queue = 430
        self._path = ""
        self._available_matches = 0

        self._lane = "any"
        self._minimal_kd = 0
        self._match_type = "both"

    @staticmethod
    def _translate_api_error(
        error,
        response_404,
        response_400="Bad request, check your input.",
        response_401="You are unauthorized, check your api key.",
        response_403="You are forbidden, check your api key/input.",
        response_405="Method not allowed",
        response_415="Unsupported media type for this request.",
        response_500="Internal server error, try again later.",
        response_502="Bad gateway, try again.",
        response_503="Service currently not available, try again later.",
        response_504="Gateway timeout, try again later.",
    ):
        if error.response.status_code == 400:
            return response_400
        elif error.response.status_code == 401:
            return response_401
        elif error.response.status_code == 403:
            return response_403
        elif error.response.status_code == 404:
            return response_404
        elif error.response.status_code == 405:
            return response_405
        elif error.response.status_code == 415:
            return response_415
        elif error.response.status_code == 429:
            return "We should retry in some time (at least 15 seconds)."
        elif error.response.status_code == 500:
            return response_500
        elif error.response.status_code == 502:
            return response_502
        elif error.response.status_code == 503:
            return response_503
        elif error.response.status_code == 504:
            return response_504
        else:
            return "Probably lack of internet/other error."

    def set_min_kd(self, kd):
        try:
            value = float(kd)
            self._minimal_kd = value
            return "Minimal kd set to: " + str(value)
        except ValueError:
            return "Input is not a float, previously set kd remains at: " + str(
                self._minimal_kd
            )

    def set_lane(self, lane):
        self._lane = lane

    def set_match_type(self, match_type):
        self._match_type = match_type

    def set_queue(self, queue):
        self._queue = queue

    def set_api_key(self, api_key):
        self._lol_watcher = LolWatcher(api_key)
        try:
            self._lol_watcher.summoner.by_name("eun1", "pandorianim")
            self._api_key = api_key
        except ApiError as err:
            return self._translate_api_error(
                err,
                "Invalid api key",
                "Invalid api key",
                "Invalid api key",
                "Invalid api key",
                "Invalid api key",
            )
        except requests.exceptions.InvalidHeader:
            return "Invalid input detected, but we handled it ;)"
        except requests.exceptions.ConnectionError:
            return "Request error, check your connection."
        except Exception:
            return "Unknown error, contact the developer."
        return "Api key has been set successfully."

    def set_region(self, region):
        self._region = region

    def set_nick(self, nick):
        try:
            self._me = self._lol_watcher.summoner.by_name(self._region, nick)
            self._nick = nick
            self._me["region"] = self._region
        except ApiError as err:
            return self._translate_api_error(err, "Summoner with that name not found.")
        except requests.exceptions.InvalidHeader:
            return "Invalid input detected, but we handled it ;)"
        except requests.exceptions.ConnectionError:
            return "Request error, check your connection."
        except Exception:
            return "Unknown error, contact the developer."
        return "Summoner name has been set to: " + nick

    def save_config(self, folder):
        if folder == "":
            return "You haven't chosen a directory! Aborting"
        config = ConfigParser()
        config.add_section("main")
        config.set("main", "api_key", self._api_key)
        config.set("main", "region", self._region)
        config.set("main", "nick", self._nick)
        config.set("main", "curr_index", str(self._current_index))
        config.set("main", "queue", str(self._queue))
        config.set("main", "path", self._path)
        config.set("main", "av_matches", str(self._available_matches))
        config.set("main", "lane", self._lane)
        config.set("main", "kd", str(self._minimal_kd))
        config.set("main", "match_type", self._match_type)

        with open(os.path.join(folder, "saved_me"), "wb") as f:
            pickle.dump(self._me, f)
        with open(os.path.join(folder, "saved_match_list"), "wb") as f:
            pickle.dump(self._match_list, f)
        with open(os.path.join(folder, "saved_matches"), "wb") as f:
            pickle.dump(self._matches, f)
        with open(os.path.join(folder, "config.ini"), "w") as configFile:
            config.write(configFile)
        return "Config saved successfully to: " + folder

    def import_config(self, folder):
        if folder == "":
            return "You haven't chosen a directory! Aborting"
        try:
            config = ConfigParser()
            config.read(os.path.join(folder, "config.ini"))
            section = config["main"]

            self._api_key = section["api_key"]
            self._lol_watcher = LolWatcher(self._api_key)
            self._region = section["region"]
            self._nick = section["nick"]
            self._current_index = int(section["curr_index"])
            self._queue = int(section["queue"])
            self._path = section["path"]
            self._available_matches = int(section["av_matches"])
            self._lane = section["lane"]
            self._minimal_kd = float(section["kd"])
            self._match_type = section["match_type"]
            with open(os.path.join(folder, "saved_me"), "rb") as f:
                self._me = pd.read_pickle(f)
            with open(os.path.join(folder, "saved_match_list"), "rb") as f:
                self._match_list = pd.read_pickle(f)
            with open(os.path.join(folder, "saved_matches"), "rb") as f:
                self._matches = pd.read_pickle(f)
            return (
                "Previously saved settings and loaded matches have been loaded."
                + " Check you api key status and provide new one if necessary."
            )
        except KeyError:
            return "Config file not found. Have you chosen right folder?"
        except FileNotFoundError:
            return "Saved files not found. Have you chosen right folder?"
        except Exception:
            return "Unknown error, contact the developer."

    def load_match_list(self):
        if self._api_key == "2":
            return "You need to set api key first!"
        if self._me == "":
            return "You need to provide nick first!"
        try:
            self._match_list = self._lol_watcher.match.matchlist_by_puuid(
                self._region, self._me["puuid"], 0, 100, self._queue
            )
            self._available_matches = len(self._match_list)
            self._matches = []
            self._current_index = 0
        except ApiError as err:
            return self._translate_api_error(
                err, "No matches found for summoner with name:", self._nick
            )
        except requests.exceptions.ConnectionError:
            return "Request error, check your connection."
        except Exception:
            return "Unknown error, contact the developer."
        return (
            "Successfully loaded "
            + str(len(self._match_list))
            + " matches into match list."
        )

    def load_matches_info(self):
        how_many = 0
        if self._available_matches == 0:
            return "There are no matches to load"
        if len(self._match_list) > 0:
            if self._available_matches >= 5:
                how_many = 5
            else:
                how_many = self._available_matches
            for i in range(self._current_index, self._current_index + how_many):
                try:
                    self._matches.append(
                        self._lol_watcher.match.by_id(self._region, self._match_list[i])
                    )
                    self._current_index += 1
                    self._available_matches -= 1
                except ApiError as err:
                    return self._translate_api_error(
                        err, "Match not found in database."
                    )
                except requests.exceptions.ConnectionError:
                    return "Request error, check your connection."
                except Exception:
                    return "Unknown error, contact the developer."
        return "Successfully downloaded " + str(how_many) + " matches information."

    def get_api_key(self):
        return self._api_key

    def get_region(self):
        return self._region

    def get_nick(self):
        return self._nick

    def get_me(self):
        return self._me

    def get_match_list(self):
        return self._match_list

    def get_matches(self):
        return self._matches

    def get_queue(self):
        return self._queue

    def get_path(self):
        return self._path

    def get_av_matches(self):
        return self._available_matches

    def get_lane(self):
        return self._lane

    def get_kd(self):
        return self._minimal_kd

    def get_type(self):
        return self._match_type
