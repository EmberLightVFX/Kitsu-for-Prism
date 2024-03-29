# -*- coding: utf-8 -*-
#
####################################################
#
# PRISM - Pipeline for animation and VFX projects
#
# www.prism-pipeline.com
#
# contact: contact@prism-pipeline.com
#
####################################################
#
#
# Copyright (C) 2016-2020 Richard Frangenberg
#
# Licensed under GNU GPL-3.0-or-later
#
# This file is part of Prism.
#
# Prism is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Prism is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Prism.  If not, see <https://www.gnu.org/licenses/>.

'''
v1.0.1
Changelog:
* Removed the "Remove empty asset types/empty episodes/sequences"-post check as it could conflict with other projects in Kitsu

v1.0
Changelog:
* First release!

---

Features:
* Sync shots and assets between Kitsu and Prism including frame range, descriptions and thumbnails
* Sync everything or only assigned shots and assets
* Open shots and assets in Kitsu from Prism
* Publish to Kitsu from Renders (If it's an image sequence it will convert it to a temp mov file before uploading and remove the local temp file after)
* Post sync features:
    * Checks if the other side has shots/assets on sync and asks if you want to sync back
    * You can dissable post sync checks in the settings
* When creating a new shot/asset in Prism you can add it directly to Kitsu
* Does work with TV Shows but only Kitsu to Local, not the other way around (folder structure problems atm)

Wanted features:
* Posibility to sync comment and image from Save and comment within DCC apps
* Make publishing videos multiprocessing so the user can use Prism while it's uploading.
    https://stackoverflow.com/questions/18864859/python-executing-multiple-functions-simultaneously

Todo:
* Popup saying that it's uploading data to Kitsu
* Check for updates in createShots() instead of making the new shot or nothing
* Check for updates in createAsset() instead of making the new shot or nothing


----

Notes to EmptyProjectManagers script:
* 'origin.seq' should be 'origin.mediaPlaybacks["shots"]["seq"]:'
    under pbBrowser_getPublishMenu


Fixes:
* # str(shotName) == "no sequence-"
* 'type(shotRange) == list' should be
    'isinstance(shotRange, (list, yaml.comments.CommentedSeq)'
        Also needs: import ruamel.yaml as yaml

'''
# Add UserInterfaces and external_modules to the paths
from Prism_Kitsu_Tools_Functions import printText
import add_external_folders

import os
import tempfile
import shutil
import ruamel.yaml as yaml

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *

from PrismUtils.Decorators import err_catcher_plugin as err_catcher
from Prism_Kitsu_Global_Functions import *
from Prism_Kitsu_Tools_Functions import *
from Prism_Kitsu_Gazu_Functions import *


class Prism_Kitsu_Functions(object):
    def __init__(self, core, plugin):
        self.core = core
        self.plugin = plugin

        self.callbacks = []
        self.registerCallbacks()

        self.project_dict = None
        self.tokens = None
        self.publish_type_dict = None

    # Should plugin be active
    @err_catcher(name=__name__)
    def isActive(self):
        return True

    # Add menus to Assets and Shots menu
    @err_catcher(name=__name__)
    def registerCallbacks(self):
        self.callbacks.append(
            self.core.registerCallback(
                "projectBrowser_getAssetMenu",
                self.projectBrowser_getAssetMenu
            )
        )
        self.callbacks.append(
            self.core.registerCallback(
                "projectBrowser_getShotMenu",
                self.projectBrowser_getShotMenu
            )
        )

    # Run when project has bin changed to another
    @err_catcher(name=__name__)
    def onProjectChanged(self, origin):
        pass

    # Create UI for Settings menus
    @err_catcher(name=__name__)
    def prismSettings_loadUI(self, origin):
        origin.gb_ksuAccount = QGroupBox("Kitsu account")
        lo_ksu = QFormLayout()
        origin.gb_ksuAccount.setLayout(lo_ksu)

        origin.l_ksuUserName = QLabel("Username:       ")
        origin.e_ksuUserName = QLineEdit()
        origin.l_ksuUserPassword = QLabel("Password:")
        origin.e_ksuUserPassword = QLineEdit()
        origin.e_ksuUserPassword.setEchoMode(QLineEdit.Password)

        lo_ksu.addRow(origin.l_ksuUserName, origin.e_ksuUserName)
        lo_ksu.addRow(origin.l_ksuUserPassword, origin.e_ksuUserPassword)

        origin.tabWidgetPage1.layout().insertWidget(1, origin.gb_ksuAccount)
        origin.groupboxes.append(origin.gb_ksuAccount)

        origin.gb_ksuIntegration = QGroupBox("Kitsu integration")
        origin.w_Kitsu = QWidget()
        lo_ksuI = QHBoxLayout()
        lo_ksuI.addWidget(origin.w_Kitsu)
        origin.gb_ksuIntegration.setLayout(lo_ksuI)
        origin.gb_ksuIntegration.setCheckable(True)
        origin.gb_ksuIntegration.setChecked(False)

        lo_ksu2 = QVBoxLayout()
        origin.w_Kitsu.setLayout(lo_ksu2)

        origin.formLayout = QFormLayout()
        origin.l_ksuSite = QLabel("Kitsu site:")
        origin.e_ksuSite = QLineEdit()
        origin.formLayout.setWidget(0, QFormLayout.LabelRole, origin.l_ksuSite)
        origin.formLayout.setWidget(0, QFormLayout.FieldRole, origin.e_ksuSite)

        origin.l_ksuPrjName = QLabel("Project Name:")
        origin.e_ksuPrjName = QLineEdit()
        origin.formLayout.setWidget(
            1, QFormLayout.LabelRole, origin.l_ksuPrjName)
        origin.formLayout.setWidget(
            1, QFormLayout.FieldRole, origin.e_ksuPrjName)

        lo_ksu2.addLayout(origin.formLayout)

        origin.horizontalLayout = QHBoxLayout()
        origin.chb_syncUserTasks = QCheckBox("Only sync user assigned tasks")
        origin.chb_syncUserTasks.setChecked(True)
        origin.horizontalLayout.addWidget(origin.chb_syncUserTasks)
        origin.ignorePostSync = QCheckBox("Ignore post sync checks")
        origin.ignorePostSync.setChecked(False)
        origin.horizontalLayout.addWidget(origin.ignorePostSync)
        origin.setFirstFrameOne = QCheckBox(
            "Set first frame to 1 (if only frames is set)")
        origin.setFirstFrameOne.setChecked(False)
        origin.horizontalLayout.addWidget(origin.setFirstFrameOne)

        lo_ksu2.addLayout(origin.horizontalLayout)

        origin.b_checkLogin = QPushButton("Check login")
        origin.b_checkLogin.clicked.connect(
            lambda: self.check_connection(
                {"ksuSite": origin.e_ksuSite.text(),
                 "ksuUsername": origin.e_ksuUserName.text(),
                 "ksuPw": origin.e_ksuUserPassword.text(),
                 "ksuProjectName": origin.e_ksuPrjName.text()}
            )
        )
        lo_ksu2.addWidget(origin.b_checkLogin)

        origin.stepMappingLayout = QVBoxLayout()
        origin.l_stepMapping = QLabel("Prism and Kitsu Step Mappings")
        origin.l_stepMapping.setMinimumHeight(30)
        origin.stepMappingLayout.addWidget(origin.l_stepMapping)
        origin.tw_steps = QTableWidget()
        origin.tw_steps.setMinimumHeight(250)
        origin.tw_steps.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        origin.tw_steps.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        origin.tw_steps.setColumnCount(2)
        origin.tw_steps.horizontalHeader().setHighlightSections(False)
        origin.tw_steps.horizontalHeader().setStretchLastSection(True)
        origin.tw_steps.verticalHeader().setVisible(False)
        origin.tw_steps.verticalHeader().setHighlightSections(False)
        origin.tw_steps.setHorizontalHeaderLabels(["Prism Step", "Kitsu Step"])
        origin.stepMappingLayout.addWidget(origin.tw_steps)
        lo_ksu2.addLayout(origin.stepMappingLayout)

        origin.w_prjSettings.layout().insertWidget(5, origin.gb_ksuIntegration)
        origin.groupboxes.append(origin.gb_ksuIntegration)

        origin.gb_ksuIntegration.toggled.connect(
            lambda x: self.prismSettings_ksuToggled(origin, x)
        )

    # Load Prism specific settings
    @ err_catcher(name=__name__)
    def check_connection(self, custom_login):
        self.tokens = None
        self.connectToKitsu(custom_login)

    # Load Prism specific settings
    @ err_catcher(name=__name__)
    def prismSettings_loadSettings(self, origin, settings):
        if "kitsu" in settings:
            if "ksuusername" in settings["kitsu"]:
                origin.e_ksuUserName.setText(settings["kitsu"]["ksuusername"])

            if "ksuuserpassword" in settings["kitsu"]:
                origin.e_ksuUserPassword.setText(
                    settings["kitsu"]["ksuuserpassword"])

    # Load Project specific settings
    @ err_catcher(name=__name__)
    def prismSettings_loadPrjSettings(self, origin, settings):
        if "kitsu" in settings:

            if "active" in settings["kitsu"]:
                origin.gb_ksuIntegration.setChecked(
                    settings["kitsu"]["active"])

            if "site" in settings["kitsu"]:
                origin.e_ksuSite.setText(settings["kitsu"]["site"])

            if "projectname" in settings["kitsu"]:
                origin.e_ksuPrjName.setText(settings["kitsu"]["projectname"])

            if "usersync" in settings["kitsu"]:
                origin.chb_syncUserTasks.setChecked(
                    settings["kitsu"]["usersync"])

            if "ignorepostchecks" in settings["kitsu"]:
                origin.ignorePostSync.setChecked(
                    settings["kitsu"]["ignorepostchecks"])

            if "setfirstframeone" in settings["kitsu"]:
                origin.ignorePostSync.setChecked(
                    settings["kitsu"]["setfirstframeone"])

            if "mapping" in settings["kitsu"]:
                stepMapping = settings["kitsu"]["mapping"]
                for prismMap in stepMapping:
                    rows = origin.tw_steps.rowCount()
                    origin.tw_steps.insertRow(rows)
                    prismStepItem = QTableWidgetItem(prismMap)
                    origin.tw_steps.setItem(rows, 0, prismStepItem)
                    kitsuStepItem = QTableWidgetItem(stepMapping[prismMap])
                    origin.tw_steps.setItem(rows, 1, kitsuStepItem)
            else:
                self.populateMappingTable(origin)

        else:

            self.populateMappingTable(origin)

        self.prismSettings_ksuToggled(origin,
                                      origin.gb_ksuIntegration.isChecked())

    # Save Prism specific settings
    @ err_catcher(name=__name__)
    def prismSettings_saveSettings(self, origin, settings):
        if "kitsu" not in settings:
            settings["kitsu"] = {}

        settings["kitsu"]["ksuuseaccount"] = origin.gb_ksuAccount.isChecked()
        settings["kitsu"]["ksuusername"] = origin.e_ksuUserName.text()
        settings["kitsu"]["ksuuserpassword"] = origin.e_ksuUserPassword.text()

    # Save project specific settings
    @ err_catcher(name=__name__)
    def prismSettings_savePrjSettings(self, origin, settings):
        if "kitsu" not in settings:
            settings["kitsu"] = {}

        settings["kitsu"]["active"] = origin.gb_ksuIntegration.isChecked()
        settings["kitsu"]["site"] = origin.e_ksuSite.text()
        settings["kitsu"]["projectname"] = origin.e_ksuPrjName.text()
        settings["kitsu"]["usersync"] = origin.chb_syncUserTasks.isChecked()
        settings["kitsu"]["ignorepostchecks"] = origin.ignorePostSync.isChecked()
        settings["kitsu"]["setfirstframeone"] = origin.setFirstFrameOne.isChecked()

        stepMapping = {}
        rows = origin.tw_steps.rowCount()
        for i in range(rows):
            prismMap = origin.tw_steps.item(i, 0).text()
            kitsuMap = origin.tw_steps.item(i, 1).text()
            stepMapping[prismMap] = kitsuMap
        settings["kitsu"]["mapping"] = stepMapping

    # Toggle visibility of toggle-objects
    @ err_catcher(name=__name__)
    def prismSettings_ksuToggled(self, origin, checked):
        origin.w_Kitsu.setVisible(checked)
        origin.gb_ksuAccount.setVisible(checked)

    # Add objects to Project Brower's Options menu
    @ err_catcher(name=__name__)
    def pbBrowser_getMenu(self, origin):
        ksu = self.core.getConfig("kitsu",
                                  "active",
                                  configPath=self.core.prismIni)

        if ksu:
            ksuMenu = QMenu("Kitsu")

            actksu = QAction("Open Kitsu", origin)
            actksu.triggered.connect(lambda: self.openKitsu("", "project"))
            ksuMenu.addAction(actksu)

            ksuMenu.addSeparator()

            actSSL = QAction("Kitsu assets to local", origin)
            actSSL.triggered.connect(lambda: self.ksuAssetsToLocal(origin))
            ksuMenu.addAction(actSSL)

            actSSL = QAction("Local assets to Kitsu", origin)
            actSSL.triggered.connect(lambda: self.ksuAssetsToKitsu(origin))
            ksuMenu.addAction(actSSL)

            ksuMenu.addSeparator()

            actSSL = QAction("Kitsu shots to local", origin)
            actSSL.triggered.connect(lambda: self.ksuShotsToLocal(origin))
            ksuMenu.addAction(actSSL)

            actLSS = QAction("Local shots to Kitsu", origin)
            actLSS.triggered.connect(lambda: self.ksuShotsToKitsu(origin))
            ksuMenu.addAction(actLSS)

            return ksuMenu

    # The menu when right-clicking on an asset
    @ err_catcher(name=__name__)
    def projectBrowser_getAssetMenu(self,
                                    origin,
                                    assetname,
                                    assetPath,
                                    entityType):

        ksu = self.core.getConfig("kitsu",
                                  "active",
                                  configPath=self.core.prismIni)

        if ksu:
            ksuAct = QAction("Open in Kitsu", origin)
            ksuAct.triggered.connect(
                lambda: self.openKitsu(assetname, "asset"))
            return ksuAct

    # The menu when right-clicking on a shot
    @ err_catcher(name=__name__)
    def projectBrowser_getShotMenu(self, origin, shotname):
        ksu = self.core.getConfig("kitsu",
                                  "active",
                                  configPath=self.core.prismIni)

        if ksu:
            ksuAct = QAction("Open in Kitsu", origin)
            ksuAct.triggered.connect(lambda: self.openKitsu(shotname, "shot"))
            return ksuAct

    # Extra GUI in the create asset window
    @ err_catcher(name=__name__)
    def createAsset_open(self, origin):
        ksu = self.core.getConfig("kitsu",
                                  "active",
                                  configPath=self.core.prismIni)

        if not ksu:
            return

        origin.chb_createInKitsu = QCheckBox("Create asset in Kitsu")
        origin.w_options.layout().insertWidget(0, origin.chb_createInKitsu)
        origin.chb_createInKitsu.setChecked(True)

    # When switching the toggle in the create asset menu
    @ err_catcher(name=__name__)
    def createAsset_typeChanged(self, origin, state):
        if hasattr(origin, "chb_createInKitsu"):
            origin.chb_createInKitsu.setEnabled(state)

    # When created a new asset
    @ err_catcher(name=__name__)
    def assetCreated(self, origin, itemDlg, assetPath):
        if (
            hasattr(itemDlg, "chb_createInKitsu")
            and itemDlg.chb_createInKitsu.isChecked()
        ):
            self.createAssets([assetPath])

    # Add GUI when editing/adding shots
    @ err_catcher(name=__name__)
    def editShot_open(self, origin, shotName):
        # Hack until shotName fix
        # (https://github.com/RichardFrangenberg/Prism/pull/24)
        if shotName is None or str(shotName) == "no sequence-":
            ksu = self.core.getConfig("kitsu",
                                      "active",
                                      configPath=self.core.prismIni)

            if not ksu:
                return

            origin.chb_createInKitsu = QCheckBox("Create shot in Kitsu")
            origin.widget.layout().insertWidget(0, origin.chb_createInKitsu)
            origin.chb_createInKitsu.setChecked(True)

    # Run when editshot ui clises
    @ err_catcher(name=__name__)
    def editShot_closed(self, origin, shotName):
        if (hasattr(origin, "chb_createInKitsu")
                and origin.chb_createInKitsu.isChecked()):
            self.createShots([shotName])

    # When rightclicking on the preview window
    @ err_catcher(name=__name__)
    def pbBrowser_getPublishMenu(self, origin):
        ksu = self.core.getConfig("kitsu",
                                  "active",
                                  configPath=self.core.prismIni)

        if (ksu and origin.mediaPlaybacks["shots"]["seq"]):
            ksuAct = QAction("Publish to Kitsu", origin)
            ksuAct.triggered.connect(lambda: self.ksuPublish(origin))
            return ksuAct

    # Connect to your Kitsu server
    def connectToKitsu(self, custom_login=False):
        if self.tokens is not None:
            return True
        else:
            if custom_login is False:
                ksuSite = self.core.getConfig("kitsu",
                                              "site",
                                              configPath=self.core.prismIni)

                ksuProjectName = self.core.getConfig("kitsu",
                                                     "projectname",
                                                     configPath=self.core.prismIni)
            else:
                ksuSite = custom_login["ksuSite"]
                ksuProjectName = custom_login["ksuProjectName"]

            if (not ksuSite or not ksuProjectName):
                QMessageBox.warning(
                    self.core.messageParent,
                    "Kitsu",
                    "Not all required information for the kitsu integration are configured.\
                    \nPlease check Project Settings.",
                )
                return False

            if custom_login is False:
                ksuUsername = self.core.getConfig("kitsu", "ksuusername")
                ksuPw = self.core.getConfig("kitsu", "ksuuserpassword")
            else:
                ksuUsername = custom_login["ksuUsername"]
                ksuPw = custom_login["ksuPw"]

            if (
                not ksuUsername
                or not ksuPw
            ):
                QMessageBox.warning(
                    self.core.messageParent,
                    "Kitsu",
                    "Not all required information for the kitsu user login are configured.\
                    \nPlease check User settings",
                )
                return False

            try:
                self.project_dict = Connect(self,
                                            ksuSite,
                                            ksuUsername,
                                            ksuPw,
                                            ksuProjectName)

            except Exception as e:
                raise e

            if self.project_dict is None:
                QMessageBox.warning(
                    self.core.messageParent, "Kitsu Sync", "The project \""
                    + ksuProjectName
                    + "\" could not be found in Kitsu."
                )

            return True

    # Publish file to Kitsu

    @ err_catcher(name=__name__)
    def ksuPublish(self, origin):
        connected = self.connectToKitsu()
        if connected is False:
            return

        # Get object
        objectName = os.path.basename(origin.renderBasePath)

        # What type is the object
        if origin.tbw_browser.currentWidget().property("tabType") == "Assets":
            pType = "Asset"
        else:
            pType = "Shot"

        # Get ID from objectName
        if pType == "Asset":
            objectID = getID(self, objectName, "Assetinfo")
        else:
            objectID = getID(self, objectName, "Shotinfo")

        if doEntityExist(objectID) is False:
            QMessageBox.warning(
                self.core.messageParent,
                "Kitsu Publish",
                "This " + pType.lower() + " does not exist on Kitsu.\nPlease sync to Kitsu before publishing."
            )

            # Remove ID that no longer exists from config file
            if objectID is not None:
                if pType == "Asset":
                    removeID(self, objectName, "Assetinfo")
                else:
                    removeID(self, objectName, "Shotinfo")

            return

        # Get task type dict
        self.publish_type_dict, type_status_dict, set_preview, comment_text = getPublishTypeDict(self,
                                                                                                 pType,
                                                                                                 doStatus=True)
        if self.publish_type_dict is None:
            return

        taskName = (origin.curRTask.replace(" (playblast)", "")
                    .replace(" (2d)", "")
                    .replace(" (external)", ""))

        versionName = origin.curRVersion.replace(" (local)", "")
        mediaPlayback = origin.mediaPlaybacks["shots"]

        videoPaths = []
        # Convert to mp4
        temp_folder = None
        if mediaPlayback["prvIsSequence"]:
            temp_folder = tempfile.mkdtemp()
            outputpath = self.convertSeqToVideo(origin, temp_folder)
            videoPaths.append(outputpath)
        else:
            for i in mediaPlayback["seq"]:
                videoPaths.append(os.path.abspath(
                    os.path.join(mediaPlayback["basePath"], i))
                )

        # get user email
        user_email = self.core.getConfig("kitsu",
                                         "ksuusername",
                                         configPath=self.core.userini)

        # Start uploading revisions
        for video_URL in videoPaths:
            uploadRevision(
                objectID,
                video_URL,
                self.publish_type_dict,
                type_status_dict,
                user_email,
                set_preview,
                comment=taskName + " " + versionName + " - " + comment_text
            )

        # Clean up potential temp_folder
        if temp_folder is not None:
            shutil.rmtree(temp_folder)

        QMessageBox.information(
            self.core.messageParent,
            "Kitsu Publish",
            ("'" + taskName + " " + versionName
             + "' was published to "
             + self.publish_type_dict["name"] + " for the " + pType.lower()
             + " '" + objectName + "'")
        )

        # Clear the publishing type dict
        self.publish_type_dict = None

    # Convert footage (code from ProjectBrowser.py
    def convertSeqToVideo(self, origin, temp_folder_name):
        mediaPlayback = origin.mediaPlaybacks["shots"]
        extension = ".mov"

        inputpath = os.path.join(
            mediaPlayback["basePath"], mediaPlayback["seq"][0]
        ).replace("\\", "/")
        inputExt = os.path.splitext(inputpath)[1]

        outputpath = os.path.join(temp_folder_name,
                                  os.path.splitext(mediaPlayback["seq"][0])[0]
                                  + extension)

        if mediaPlayback["prvIsSequence"]:
            inputpath = os.path.splitext(inputpath)[0]
            inputpath = inputpath[:-self.core.framePadding] + \
                "%04d".replace("4", str(self.core.framePadding)) + inputExt

        conversionSettings = {}
        conversionSettings["-c"] = "prores"
        conversionSettings["-profile"] = 2
        conversionSettings["-pix_fmt"] = "yuv422p10le"

        if mediaPlayback["prvIsSequence"]:
            startNum = mediaPlayback["pstart"]
        else:
            startNum = 0
            if inputExt == ".dpx":
                conversionSettings["-start_number"] = None
                conversionSettings["-start_number_out"] = None

        self.core.media.convertMedia(
            inputpath,
            startNum,
            outputpath,
            settings=conversionSettings
        )

        return outputpath

    # Open kitsu and direct the user to the correct page
    def openKitsu(self, obj_name, section):
        connected = self.connectToKitsu()
        if connected is False:
            return

        # As we can't get the project ID before connecting to Kitsu,
        # a blank ID was passed
        if section == "project":
            obj_id = self.project_dict
        else:
            obj_id = getID(self, obj_name, section + "info")

        try:
            ksuSite = GetUrl(obj_id, section)
        except Exception as exc:
            QMessageBox.warning(
                QWidget(),
                "Kitsu Sync",
                "Could not find shot in Kitsu"
            )
            removeID(self, obj_name, section + "info")
            return

        import webbrowser

        webbrowser.open(ksuSite)

    # Download asset info from Kitsu
    @ err_catcher(name=__name__)
    def ksuAssetsToLocal(self, origin):
        connected = self.connectToKitsu()
        if connected is False:
            return

        ksuAssets = GetKitsuAssets(self)

        if ksuAssets is False:
            QMessageBox.warning(
                self.core.messageParent,
                "Kitsu Sync",
                "No assets on Kitsu were found",
            )
            return

        isEpisode = False
        if self.project_dict["production_type"] == "tvshow":
            isEpisode = True

        # Check what assets needs to be created ##
        createdAssets = []
        updatedAssets = []
        configInfo = {}

        for assetData in ksuAssets:
            assetInfo = {}

            # Start by getting the asset type
            assetType = GetAssetType(assetData["entity_type_id"])["name"]
            assetPath = os.path.join(origin.aBasePath, assetType)

            # If project has episodes, get the episode the asset is for
            if assetData["source_id"] is not None:
                assetPath = os.path.join(assetPath,
                                         GetEpisodeName(assetData["source_id"]))
            else:
                if isEpisode:
                    assetPath = os.path.join(assetPath, "Main Pack")

            # Write out ID to config
            assetInfo["objID"] = assetData["id"]

            # Add asset name
            assetPath = os.path.join(assetPath, assetData["name"])

            # Create folder
            if not os.path.isdir(assetPath):
                self.core.entities.createEntity("asset", assetPath)
                createdAssets.append(assetData["name"])

            # Create steps
            tasks = GetTasksForAsset(assetData)
            for task in tasks:
                kitsuStep = task["task_type_name"]
                prismStep = self.getPrismStepFromKitsuStep(kitsuStep)
                self.core.entities.createStep(prismStep, "asset", assetPath, createCat=False)
                self.core.entities.createCategory("asset", assetPath, prismStep, kitsuStep)

            # Process thumbnail
            tmbID, created, updated = DownloadThumbnail(self,
                                                        assetData["name"],
                                                        assetData["preview_file_id"],
                                                        "Assetinfo")
            if tmbID == "":
                removeID(self, assetData["name"], "assetinfo")
            elif tmbID is not False:
                assetInfo["thumbnailID"] = tmbID

            if (assetData["name"] not in createdAssets
                    and assetData["name"] not in updatedAssets):

                if created:
                    createdAssets.append(assetData["name"])
                elif updated:
                    updatedAssets.append(assetData["name"])

            # Write description
            desc, created, updated = DownloadDescription(self,
                                                         assetData["name"],
                                                         assetData["description"],
                                                         "assetinfo")
            if desc is not False:
                assetInfo["description"] = desc

            if (assetData["name"] not in createdAssets
                    and assetData["name"] not in updatedAssets):
                if created:
                    createdAssets.append(assetData["name"])
                elif updated:
                    updatedAssets.append(assetData["name"])

            # Add info to config array
            configInfo[assetData["name"]] = assetInfo

        if len(configInfo) > 0:
            # Write information
            self.core.setConfig(data=configInfo, config="assetinfo")

        # Check and report what assets got added or updated ##
        ReportUpdateInfo(self, createdAssets, updatedAssets, "assets")

        # Check if we should do reverse sync
        ignore_post_checks = self.core.getConfig("kitsu",
                                                 "ignorepostchecks",
                                                 configPath=self.core.prismIni)

        if ignore_post_checks is False:

            # Find not uploaded assets
            self.core.entities.refreshOmittedEntities()
            assets = self.core.entities.getAssetPaths()
            assetnames = []
            for asset in assets:
                asset_name = os.path.basename(asset)

                if (not asset_name.startswith(
                        "_") and asset_name not in self.core.entities.omittedEntities["asset"]):
                    assetnames.append(asset_name)

            localAssets = []
            for localName in assetnames:
                localID = getID(self, localName, "Assetinfo")
                if localID is None:
                    localAssets.append(localName)

            if len(localAssets) > 0:
                msg = QMessageBox(
                    QMessageBox.Question,
                    "Kitsu Sync",
                    "Some local assets don't exist on Kitsu:\n"
                    + "\n".join(localAssets),
                    parent=self.core.messageParent,
                )
                msg.addButton("Hide local assets", QMessageBox.YesRole)
                msg.addButton("Add assets to Kitsu", QMessageBox.YesRole)
                msg.addButton("Do nothing", QMessageBox.YesRole)
                msg.addButton("Don't ask again", QMessageBox.YesRole)
                action = msg.exec_()

                if action == 0:
                    noAccess = []
                    for i in localAssets:
                        dstname = os.path.join(origin.aBasePath, "_" + i)
                        if not os.path.isdir(dstname):
                            try:
                                os.rename(
                                    os.path.join(
                                        origin.aBasePath,
                                        i
                                    ),
                                    dstname
                                )
                            except Exception:
                                noAccess.append(i)

                    if len(noAccess) > 0:
                        msgString = "Acces denied for:\n\n"

                        for i in noAccess:
                            msgString += i + "\n"

                        QMessageBox.warning(
                            self.core.messageParent, "Hide Shots", msgString
                        )
                elif action == 1:
                    created_assets, updated_assets, self.createAssets(
                        localAssets)
                    # Report what shots got added or updated
                    ReportUpdateInfo(self, localAssets,
                                     updated_assets, "assets")
                elif action == 3:
                    QMessageBox.information(
                        self.core.messageParent,
                        "Kitsu",
                        "You can undo this by unchecking \"Ignore post checks\" in the settings.",
                    )
                    self.core.setConfig("kitsu",
                                        "ignorepostchecks",
                                        True,
                                        configPath=self.core.prismIni)

        origin.refreshAHierarchy()

    # Upload asset info to Kitsu
    @ err_catcher(name=__name__)
    def ksuAssetsToKitsu(self, origin):
        assets = self.core.entities.getAssetPaths()

        createdAssets = []
        updatedAssets = []
        # Create the asset
        createdAssets, updatedAssets = self.createAssets(assets)
        self.createAssetTasks(assets)

        # Report what shots got added or updated
        ReportUpdateInfo(self, createdAssets, updatedAssets, "assets")

        # Check if we should do reverse sync
        ignore_post_checks = self.core.getConfig("kitsu",
                                                 "ignorepostchecks",
                                                 configPath=self.core.prismIni)

        if ignore_post_checks is False:

            # Time to check if Kitsu has some assets we don't have
            # Get kitsu assets
            ksuAssets = GetKitsuAssets(self)
            if ksuAssets is not False:
                externalAssets = []
                # Process all shots ##
                for asset in ksuAssets:
                    localID = getID(self, asset["name"], "Assetinfo")
                    if localID is None:
                        externalAssets.append(asset["name"])

                if len(externalAssets) > 0:
                    msg = QMessageBox(
                        QMessageBox.Question,
                        "Kitsu Sync",
                        "Some Kitsu shots don't exist locally:\n"
                        + "\n".join(externalAssets),
                        parent=self.core.messageParent,
                    )
                    msg.addButton("Sync Kitsu assets", QMessageBox.YesRole)
                    msg.addButton("Do nothing", QMessageBox.YesRole)
                    action = msg.exec_()

                    if action == 0:
                        self.ksuAssetsToLocal(origin)

    # Download shot info from Kitsu
    @ err_catcher(name=__name__)
    def ksuShotsToLocal(self, origin):
        ksuShots = GetKitsuShots(self)

        if ksuShots is False:
            QMessageBox.warning(
                self.core.messageParent,
                "Kitsu Sync",
                "No shots on Kitsu were found",
            )
            return

        createdShots = []
        updatedShots = []
        configInfo = {}
        # Process all shots ##
        for shotData in ksuShots:
            shotInfo = {}

            # Create shot folders ##
            shotName = shotData["sequence_name"] + "-" + shotData["name"]

            # Add episode name if exists
            if "episode_name" in shotData:
                shotName = shotData["episode_name"] + "." + shotName

            # Create folder if it doesn't exist
            if not os.path.isdir(os.path.join(origin.sBasePath, shotName)):
                self.core.entities.createEntity("shot", shotName)

                createdShots.append(shotName)

                shotInfo["objID"] = shotData["id"]

            # Create steps
            tasks = GetTasksForShot(shotData)
            for task in tasks:
                kitsuStep = task["task_type_name"]
                prismStep = self.getPrismStepFromKitsuStep(kitsuStep)
                self.core.entities.createStep(prismStep, "shot", shotName, createCat=False)
                self.core.entities.createCategory("shot", shotName, prismStep, kitsuStep)

            # As Kitsu allows you to write only one of the start frame and
            # end frame we need to check them induvidually
            frame_nudge = int(self.core.getConfig("kitsu",
                                                  "setFirstFrameOne",
                                                  configPath=self.core.prismIni) is True)
            nb_frames = None
            if shotData["nb_frames"] is not None:
                nb_frames = int(shotData["nb_frames"])
            frame_in = None
            frame_out = None
            if shotData["data"] is not None:
                if "frame_in" in shotData["data"]:
                    frame_in = int(shotData["data"]["frame_in"])
                if "frame_out" in shotData["data"]:
                    frame_out = int(shotData["data"]["frame_out"])

            if frame_in is not None:
                if frame_out is None:
                    frame_out = frame_in + nb_frames
            elif nb_frames is not None:
                frame_in = frame_nudge
                frame_out = nb_frames - 1 + frame_nudge

            if frame_in is not None and frame_out is not None:
                shotRange = self.core.getConfig("shotRanges",
                                                shotName,
                                                config="shotinfo")

                prv_frame_in = None
                prv_frame_out = None

                if (isinstance(shotRange, (list, yaml.comments.CommentedSeq))
                        and len(shotRange) == 2):
                    prv_frame_in = int(shotRange[0])
                    prv_frame_out = int(shotRange[1])

                if (frame_in != prv_frame_in or frame_out != prv_frame_out):
                    # Update to be connected to shot-name instead of shotRange
                    self.core.setConfig(
                        "shotRanges",
                        shotName,
                        [frame_in, frame_out],
                        config="shotinfo"
                    )

                if (
                    shotName not in createdShots
                    and shotName not in updatedShots
                    and (frame_in != prv_frame_in
                         or frame_out != prv_frame_out)
                ):
                    updatedShots.append(shotName)

            # Process thumbnail ##
            tmbID, created, updated = DownloadThumbnail(self,
                                                        shotName,
                                                        shotData["preview_file_id"],
                                                        "Shotinfo")
            if tmbID == "":
                removeID(self, shotName, "assetinfo")
            elif tmbID is not None:
                shotInfo["thumbnailID"] = tmbID

            if (
                shotName not in createdShots
                and shotName not in updatedShots
            ):
                if created:
                    createdShots.append(shotName)
                elif updated:
                    updatedShots.append(shotName)

            # Add info to config array
            configInfo[shotName] = shotInfo

        if len(configInfo) > 0:
            # Write information
            self.core.setConfig(data=configInfo, config="shotinfo")

        # Report what shots got added or updated
        ReportUpdateInfo(self, createdShots, updatedShots, "shots")

        # Check if we should do reverse sync
        ignore_post_checks = self.core.getConfig("kitsu",
                                                 "ignorepostchecks",
                                                 configPath=self.core.prismIni)

        if ignore_post_checks is False:

            # Check for shots that does not exist on Kitsu ##
            for i in os.walk(origin.sBasePath):
                foldercont = i
                break

            shotnames = []
            for shot_name in foldercont[1]:
                if (not shot_name.startswith(
                        "_") and shot_name not in self.core.entities.omittedEntities["shot"]):
                    shotnames.append(shot_name)

            localShots = []
            for localName in shotnames:
                localID = getID(self, localName, "shotinfo")
                if localID is None:
                    localShots.append(localName)

            if len(localShots) > 0:
                msg = QMessageBox(
                    QMessageBox.Question,
                    "Kitsu Sync",
                    "Some local shots don't exist on Kitsu:\n"
                    + "\n".join(localShots),
                    parent=self.core.messageParent,
                )
                msg.addButton("Hide local shots", QMessageBox.YesRole)
                msg.addButton("Add shots to Kitsu", QMessageBox.YesRole)
                msg.addButton("Do nothing", QMessageBox.YesRole)
                msg.addButton("Don't ask again", QMessageBox.YesRole)
                action = msg.exec_()

                if action == 0:
                    noAccess = []
                    for i in localShots:
                        dstname = os.path.join(origin.sBasePath, "_" + i)
                        if not os.path.isdir(dstname):
                            try:
                                os.rename(
                                    os.path.join(
                                        origin.sBasePath,
                                        i
                                    ),
                                    dstname
                                )
                            except Exception:
                                noAccess.append(i)

                    if len(noAccess) > 0:
                        msgString = "Acces denied for:\n\n"

                        for i in noAccess:
                            msgString += i + "\n"

                        QMessageBox.warning(
                            self.core.messageParent, "Hide Shots", msgString
                        )
                elif action == 1:
                    created_shots, updated_shots = self.createShots(localShots)
                    # Report what shots got added or updated
                    ReportUpdateInfo(self, created_shots,
                                     updated_shots, "shots")
                elif action == 3:
                    QMessageBox.information(
                        self.core.messageParent,
                        "Kitsu",
                        "You can undo this by unchecking \"Ignore post checks\" in the settings.",
                    )
                    self.core.setConfig("kitsu",
                                        "ignorepostchecks",
                                        True,
                                        configPath=self.core.prismIni)

        origin.refreshShots()

    # Upload shot info from Kitsu
    @ err_catcher(name=__name__)
    def ksuShotsToKitsu(self, origin):
        for i in os.walk(origin.sBasePath):
            foldercont = i
            break

        self.core.entities.refreshOmittedEntities()

        shot_names = []
        for shot_name in foldercont[1]:
            if (not shot_name.startswith(
                    "_") and shot_name not in self.core.entities.omittedEntities["shot"]):
                shot_names.append(shot_name)

        created_shots, updated_shots = self.createShots(shot_names)
        self.createShotTasks(shot_names)

        # Report what shots got added or updated
        ReportUpdateInfo(self, created_shots, updated_shots, "shots")

        # Check if we should do reverse sync
        ignore_post_checks = self.core.getConfig("kitsu",
                                                 "ignorepostchecks",
                                                 configPath=self.core.prismIni)

        if ignore_post_checks is False:

            # Time to check if Kitsu has some shots we don't have
            # Get kitsu shots
            ksuShots = GetKitsuShots(self)

            if ksuShots is not False:
                externalShots = []
                # Process all shots ##
                for shotData in ksuShots:
                    # Create shot folders ##
                    shotName = shotData["sequence_name"] + \
                        "-" + shotData["name"]

                    # Add episode name if exists
                    if "episode_name" in shotData:
                        shotName = shotData["episode_name"] + "." + shotName

                    localID = getID(self, shotName, "Shotinfo")
                    if localID is None:
                        externalShots.append(shotName)

                if len(externalShots) > 0:
                    msg = QMessageBox(
                        QMessageBox.Question,
                        "Kitsu Sync",
                        "Some Kitsu shots don't exist locally:\n"
                        + "\n".join(externalShots),
                        parent=self.core.messageParent,
                    )
                    msg.addButton("Sync Kitsu shots", QMessageBox.YesRole)
                    msg.addButton("Do nothing", QMessageBox.YesRole)
                    action = msg.exec_()

                    if action == 0:
                        self.ksuShotsToLocal(origin)

    @ err_catcher(name=__name__)
    def onProjectBrowserClose(self, origin):
        pass

    @ err_catcher(name=__name__)
    def onSetProjectStartup(self, origin):
        pass

    @ err_catcher(name=__name__)
    def createAssets(self, assets):
        connected = self.connectToKitsu()
        if connected is False:
            return [], []

        created_assets = []
        updated_assets = []
        configInfo = {}
        for asset_location in assets:
            assetInfo = {}
            # Remove pre-folder path and remove first character
            # before os.sep split and remove last object as it's
            # the name of the asset
            aBasePath = self.core.getAssetPath()
            asset_location = asset_location.replace(aBasePath, "")

            splits = asset_location[1:].split(os.sep)[:-1]

            # If not in any subfolder, assign to the empty asset-type
            if len(splits) == 0:
                splits.append("")

            asset_name = os.path.basename(asset_location)
            asset_type_name = splits[0]

            asset_description = self.core.getConfig(asset_name,
                                                    "description",
                                                    config="assetinfo")

            # If asset has subfolders, add to asset_description

            if len(splits) > 1:
                if asset_description is not None:
                    asset_description = " - " + str(asset_description)
                else:
                    asset_description = ""

                asset_description = "/".join(splits[1:]) + \
                    str(asset_description)

            # Get preview image
            previewImgPath = os.path.join(os.path.dirname(self.core.prismIni),
                                          "Assetinfo",
                                          "%s_preview.jpg" % asset_name,
                                          )
            thumbnailURL = previewImgPath if os.path.isfile(
                previewImgPath) else None

            asset_type_dict, created_asset_type = createKitsuAssetType(
                asset_type_name)

            asset_dict, created_asset = createKitsuAsset(self.project_dict,
                                                         asset_type_dict,
                                                         asset_name,
                                                         asset_description,
                                                         extra_data={},
                                                         episode=None)

            # Add thumbnail if preview image exists
            if thumbnailURL is not None and created_asset:
                while True:
                    # Get task type dict
                    if self.publish_type_dict is None:
                        self.publish_type_dict = getPublishTypeDict(
                            self, "Asset")
                        if self.publish_type_dict is None:
                            if created_asset:
                                RemoveAsset(asset_dict)
                            if created_asset_type:
                                RemoveAssetType(asset_type_dict)
                            break

                    user_email = self.core.getConfig("kitsu",
                                                     "ksuusername",
                                                     configPath=self.core.userini)

                    # Ask user to pick task to add thumbnail to
                    thumbnail_id = uploadThumbnail(
                        asset_dict["id"],
                        thumbnailURL,
                        self.publish_type_dict,
                        user_email
                    )
                    assetInfo["thumbnailID"] = thumbnail_id
                    break

            # Write out ID to config
            if created_asset:
                assetInfo["objID"] = asset_dict["id"]
                created_assets.append(asset_name)
                # Add info to config array
                configInfo[asset_name] = assetInfo

        if len(configInfo) > 0:
            # Write information
            self.core.setConfig(data=configInfo, config="assetinfo")

        # Clear the publishing type dict
        self.publish_type_dict = None

        return created_assets, updated_assets

    @ err_catcher(name=__name__)
    def createAssetTasks(self, assets):
        connected = self.connectToKitsu()
        if connected is False:
            return

        for asset_location in assets:
            # Remove pre-folder path and remove first character
            # before os.sep split and remove last object as it's
            # the name of the asset
            aBasePath = self.core.getAssetPath()
            assetPath = asset_location.replace(aBasePath, "")

            splits = assetPath[1:].split(os.sep)[:-1]

            # If not in any subfolder, assign to the empty asset-type
            if len(splits) == 0:
                splits.append("")

            asset_name = os.path.basename(assetPath)
            asset_dict = GetAssetByName(self.project_dict, asset_name)
            taskTypes = getTaskTypes(asset_dict)
            taskTypeNames = [x['name'] for x in taskTypes]
            allTaskTypes = getTaskTypes()

            scenepath = self.core.getEntityPath(entity="step", asset=assetPath)
            for root, folders, files in os.walk(scenepath):
                for step in folders:
                    kitsuStep = self.getKitsuStepFromPrismStep(step)
                    if kitsuStep not in taskTypeNames:
                        task_type = next((x for x in allTaskTypes if x['name'] == kitsuStep), None)
                        createKitsuTask(asset_dict, task_type)
                break

        return

    @ err_catcher(name=__name__)
    def createShots(self, shots):
        connected = self.connectToKitsu()
        if connected is False:
            return [], []

        created_shots = []
        updated_shots = []
        configInfo = {}
        for shot_name in shots:
            shotInfo = {}
            # Get range
            shotRanges = self.core.getConfig("shotRanges",
                                             shot_name,
                                             config="shotinfo"
                                             )

            # Get preview image
            previewImgPath = os.path.join(os.path.dirname(self.core.prismIni),
                                          "Shotinfo",
                                          "%s_preview.jpg" % shot_name,
                                          )

            # Split names
            shotName, seqName = self.core.entities.splitShotname(shot_name)
            if self.project_dict["production_type"] == "tvshow":
                epName, seqName = seqName.split(".", 1)
            else:
                epName = None

            thumbnailURL = previewImgPath if os.path.isfile(
                previewImgPath) else None

            episode_dict, created_ep = createKitsuEpisode(self.project_dict,
                                                          epName)
            sequence_dict, created_seq = createKitsuSequence(self.project_dict,
                                                             seqName,
                                                             episode_dict)
            shot_dict, created_shot = createKitsuShot(self.project_dict,
                                                      sequence_dict,
                                                      shotName,
                                                      shotRanges)

            # Add thumbnail if preview image exists
            if thumbnailURL is not None and created_shot:
                while True:
                    # Get task type dict
                    if self.publish_type_dict is None:
                        self.publish_type_dict = getPublishTypeDict(self,
                                                                    "Shot")
                        if self.publish_type_dict is None:
                            if created_shot:
                                RemoveShot(shot_dict)
                                created_shot = False
                            if created_seq:
                                RemoveSequence(sequence_dict)
                            if created_ep:
                                RemoveEpisode(episode_dict)
                            break

                    user_email = self.core.getConfig("kitsu",
                                                     "ksuusername",
                                                     configPath=self.core.userini)

                    # Ask user to pick task to add thumbnail to
                    thumbnail_id = uploadThumbnail(
                        shot_dict["id"],
                        thumbnailURL,
                        self.publish_type_dict,
                        user_email
                    )
                    shotInfo["thumbnailID"] = thumbnail_id
                    break

            # Write out ID to config
            if created_shot:
                shotInfo["objID"] = shot_dict["id"]
                created_shots.append(shot_name)
                # Add info to config array
                configInfo[shot_name] = shotInfo

        if len(configInfo) > 0:
            # Write information
            self.core.setConfig(data=configInfo, config="shotinfo")

        # Clear the publishing type dict
        self.publish_type_dict = None

        return created_shots, updated_shots


    @ err_catcher(name=__name__)
    def createShotTasks(self, shots):
        connected = self.connectToKitsu()
        if connected is False:
            return

        for shot_name in shots:
            # Split names
            shotName, seqName = self.core.entities.splitShotname(shot_name)
            if self.project_dict["production_type"] == "tvshow":
                seqPart = seqName
                epName, seqName = seqName.split(".", 1)
            else:
                seqPart = seqName
                epName = None

            episode_dict = GetEpisodeByName(self.project_dict, epName) if epName else None
            sequence_dict = GetSequenceByName(self.project_dict, seqName, episode_dict)
            shot_dict = GetShotByName(sequence_dict, shotName)
            taskTypes = getTaskTypes(shot_dict)
            taskTypeNames = [x['name'] for x in taskTypes]
            allTaskTypes = getTaskTypes()

            scenepath = self.core.getEntityPath(entity="step", shot=shotName, sequence=seqPart)
            for root, folders, files in os.walk(scenepath):
                for step in folders:
                    kitsuStep = self.getKitsuStepFromPrismStep(step)
                    if kitsuStep not in taskTypeNames:
                        task_type = next((x for x in allTaskTypes if x['name'] == kitsuStep), None)
                        createKitsuTask(shot_dict, task_type)
                break
        return


    def populateMappingTable(self, origin):
        for step in self.core.getConfig(
            "globals", "pipeline_steps", configPath=self.core.prismIni, dft={}
        ):
            rows = origin.tw_steps.rowCount()
            origin.tw_steps.insertRow(rows)
            prismStepItem = QTableWidgetItem(step)
            origin.tw_steps.setItem(rows, 0, prismStepItem)


    def getKitsuStepFromPrismStep(self, step):
        for prismStep, kitsuStep in self.core.getConfig(
            "kitsu", "mapping", configPath=self.core.prismIni, dft={}
        ).items():
            if step == prismStep:
                return kitsuStep
        return None


    def getPrismStepFromKitsuStep(self, step):
        for prismStep, kitsuStep in self.core.getConfig(
            "kitsu", "mapping", configPath=self.core.prismIni, dft={}
        ).items():
            if step == kitsuStep:
                return prismStep
        return None
