import os
import datetime
from tkinter.messagebox import askyesno


class FileCreator:
    def __init__(self, settings, gui):
        self._settings = settings
        self._gui = gui

    def filter_files(self):
        output = []
        for match in self._settings.get_matches():
            characters = match["info"]["participants"]
            for participant in characters:
                if participant["puuid"] == self._settings.get_me()["puuid"]:
                    if (
                        self._gui.role_dict[self._settings.get_lane()]
                        == participant["teamPosition"]
                        or self._settings.get_lane() == "any"
                    ):
                        if (
                            self._gui.match_type_dict[self._settings.get_type()]
                            == participant["win"]
                            or self._settings.get_type() == "both"
                        ):
                            kd = (participant["kills"] + participant["assists"]) / max(
                                1, participant["deaths"]
                            )
                            participant["kd"] = kd
                            participant.pop("perks", False)
                            if kd >= self._settings.get_kd():
                                participant["gameDuration"] = match["info"][
                                    "gameDuration"
                                ]
                                participant["gameMode"] = match["info"]["gameMode"]
                                participant["gameName"] = match["info"]["gameName"]
                                participant["gameStartTimestamp"] = match["info"][
                                    "gameStartTimestamp"
                                ]
                                participant["gameType"] = match["info"]["gameType"]
                                participant["gameVersion"] = match["info"][
                                    "gameVersion"
                                ]
                                participant["queueId"] = match["info"]["queueId"]
                                output.append(participant)
        return output

    def create_files(self):
        if self._settings.get_path() == "":
            return "You need to chose output folder before creating files!"
        output = self.filter_files()
        if not output:
            return "No matches with your filtering criteria were found, load more matches/change filtering."
        answer = askyesno(
            "Confirmation",
            message="Are you sure you want to output "
            + str(len(output))
            + " files into:\n"
            + self._settings.get_path()
            + "\n??",
        )
        if answer:
            for i in range(len(output)):
                curr_date = datetime.datetime.now()
                name = (
                    "file_"
                    + str(i + 1)
                    + "_"
                    + str(curr_date.day)
                    + "."
                    + str(curr_date.month)
                    + "."
                    + str(curr_date.year)
                    + ".txt"
                )
                complete_path = os.path.join(self._settings.get_path(), name)
                with open(complete_path, "w") as file:
                    items = list(output[i].items())
                    items.sort(key=lambda t: t[0])
                    for j in range(len(output[i])):
                        if items[j][0] == "challenges":
                            second_dict = output[i]["challenges"]
                            second_items = list(second_dict.items())
                            file.write("challenges:\n")
                            for k in range(len(second_items)):
                                file.write(
                                    "\t"
                                    + second_items[k][0]
                                    + ": "
                                    + str(second_items[k][1])
                                    + "\n"
                                )
                        else:
                            file.write(items[j][0] + ": " + str(items[j][1]) + "\n")
            return "Outputted files to folder: " + self._settings.get_path()
        else:
            return "The output of files have been aborted."
