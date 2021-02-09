import os
import sys
import TaskPicker

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from Prism_Kitsu_Gazu_Functions import *


@err_catcher(name=__name__)
def ReportUpdateInfo(self, created, updated, type):
    # Check and report what got added or updated ##
    if len(created) > 0 or len(updated) > 0:
        msgString = ""
        created.sort()
        updated.sort()

        if len(created) > 0:
            msgString += "The following " + type + " were created:\n\n"

            for i in created:
                msgString += str(i) + "\n"

        if len(created) > 0 and len(updated) > 0:
            msgString += "\n\n"

        if len(updated) > 0:
            msgString += "The following " + type + " were updated:\n\n"

            for i in updated:
                msgString += str(i) + "\n"
    else:
        msgString = "No " + type + " were created or updated."

    QMessageBox.information(self.core.messageParent, "Kitsu Sync", msgString)


def DownloadDescription(self, name, description, configName):
    local_description = self.core.getConfig(
        name,
        "description",
        config=configName
    )

    if description != local_description:
        if local_description is None:  # Description got created
            return description, True, False
        else:  # Description got edited
            return description, False, True

    return False, False, False


def saveID(self, name, id, info_location):
    oldID = getID(self, name, info_location)
    if oldID != id:
        self.core.setConfig(
            cat=name,
            param="objID",
            val=id,
            config=info_location.lower()
        )


def removeID(self, name, info_location):
    self.core.setConfig(
        cat=name,
        param="objID",
        delete=True,
        config=info_location.lower()
    )
    self.core.setConfig(
        cat=name,
        param="thumbnailID",
        delete=True,
        config=info_location.lower()
    )


def getID(self, name, info_location):
    obj_id = self.core.getConfig(cat=name,
                                 param="objID",
                                 config=info_location.lower())

    return obj_id


def saveThumbnailID(self, name, id, info_location):
    oldID = getID(self, name, info_location)
    if oldID != id:
        self.core.setConfig(
            name,
            "thumbnailID",
            id,
            config=info_location.lower()
        )


def RemoveCanceled(entities):
    nonCanceled = []
    for entity in entities:
        if not entity["canceled"]:
            nonCanceled.append(entity)
    return nonCanceled


# Get Kitsu shots
def GetKitsuShots(self):
    connected = self.connectToKitsu()
    if connected is False:
        return False

    ksuShots = []

    # Check if only should get user assigned objects
    user_sync = self.core.getConfig("kitsu",
                                    "usersync",
                                    configPath=self.core.prismIni)

    # Check if tv show, meaning we're also dealing with episodes
    if self.project_dict["production_type"] == "tvshow":
        episodes = GetEpisodes(self.project_dict, user=user_sync)
        for episode in episodes:
            sequences = GetSequences(
                episode, "from_episode", user=user_sync)

            for sequence in sequences:
                shots = GetShots(sequence, "from_sequence", user=user_sync)

                for shot in shots:
                    shot["episode_name"] = episode["name"]
                    ksuShots.append(shot)

    else:  # meaning feature or short film
        sequences = GetSequences(
            self.project_dict, "from_project", user=user_sync)

        for sequence in sequences:
            shots = GetShots(sequence, "from_sequence", user=user_sync)

            for shot in shots:
                ksuShots.append(shot)

    if len(ksuShots) == 0:
        return False

    ksuShots = RemoveCanceled(ksuShots)

    return ksuShots


# Get Kitsu shots
def GetKitsuAssets(self):
    connected = self.connectToKitsu()
    if connected is False:
        return False

    assetTypes = GetAssetTypes()
    ksuAssets = []

    # Check if only should get user assigned objects
    user_sync = self.core.getConfig("kitsu",
                                    "usersync",
                                    configPath=self.core.prismIni)
    for assetType in assetTypes:
        assets = GetAssets(self.project_dict, assetType, user=user_sync)
        for asset in assets:
            ksuAssets.append(asset)
    if len(ksuAssets) == 0:
        return False
    ksuAssets = RemoveCanceled(ksuAssets)

    return ksuAssets


def getPublishTypeDict(self, pType, doStatus=False):
    """
    Get task types
    Get task statses
    """
    taskTypes_dict = getTaskTypes()

    taskTypes = []
    for taskType in taskTypes_dict:
        if taskType["for_shots"] == (pType == "Shot"):
            taskTypes.append(taskType)

    taskStatuses = gazu.task.all_task_statuses()

    tp = TaskPicker.TaskPicker(core=self.core,
                               taskTypes_dicts=taskTypes,
                               taskStatuses_dicts=taskStatuses,
                               doStatus=doStatus)
    tp.exec_()

    if tp.picked_data is None:
        QMessageBox.warning(
            self.core.messageParent,
            "Kitsu Publish",
            "Publishing canceled"
        )

    return tp.picked_data
