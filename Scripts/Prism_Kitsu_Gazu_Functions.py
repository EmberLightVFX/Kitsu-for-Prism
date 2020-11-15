import os
import gazu

try:
    from PySide2.QtCore import *
    from PySide2.QtGui import *
    from PySide2.QtWidgets import *
except:
    from PySide.QtCore import *
    from PySide.QtGui import *


from Prism_Kitsu_Tools_Functions import *


def Connect(self, host, user, password, projectName):
    """Log-in dialog to Kitsu"""

    # Connect to server
    if self.tokens is None:
        try:
            host = removeLastSlash(host)
            host = host + "/api"
            gazu.set_host(host)
            if not gazu.client.host_is_up():
                raise ConnectionError(
                    "Could not connect to the server. Is the host URL correct?"
                )
        except Exception as exc:
            QMessageBox.warning(QWidget(), str("Kitsu Error"), str(exc))
            return "Connection error"

        # Login
        try:
            self.tokens = gazu.log_in(user, password)

        except:
            message = (
                "Login verification failed.\n"
                "Please ensure your username and "
                "password for Kitsu are correct.\n"
            )

            QMessageBox.warning(QWidget(), str("Kitsu Error"), str(message))
            return "Connection error"

    QMessageBox.warning(QWidget(), str("Kitsu Logged in"), str("Logged in"))

    # Lastly, get the project dict and return it
    project_dict = gazu.project.get_project_by_name(projectName)
    return project_dict


def removeLastSlash(adress):
    if adress[-1:] == "/":
        adress = adress[:-1]

    return adress


def GetUrl(obj_id, section):

    # Get projAdress
    if section == "project":
        url = gazu.project.get_project_url(obj_id, "shots")
    elif section == "shot":
        obj_dict = gazu.shot.get_shot(obj_id)
        url = gazu.shot.get_shot_url(obj_dict)
    elif section == "asset":
        obj_dict = gazu.asset.get_asset(obj_id)
        url = gazu.asset.get_asset_url(obj_dict)

    return url


def GetEpisodes(project_dict, user=False):
    if user:
        episodes = gazu.user.all_episodes_for_project(project_dict)
    else:
        episodes = gazu.shot.all_episodes_for_project(project_dict)

    return episodes


def RemoveEpisode(episode_dict):
    return gazu.shot.remove_episode(episode_dict)


def GetSequences(dict, where="from_project", user=False):
    sequences = None
    if user:
        if where == "from_project":
            sequences = gazu.user.all_sequences_for_project(dict)
        else:
            sequences = gazu.user.all_sequences_for_episode(dict)
    else:
        if where == "from_project":
            sequences = gazu.shot.all_sequences_for_project(dict)
        else:
            sequences = gazu.shot.all_sequences_for_episode(dict)

    return sequences


def RemoveSequence(sequence_dict):
    return gazu.shot.remove_sequence(sequence_dict)


def GetShots(dict, where="from_sequence", user=False, getCanceled=False):
    shots = None

    if user:
        if where == "from_sequence":
            shots = gazu.user.all_shots_for_sequence(dict)
            # Add sequence name as it isn't given from user-catch
            for shot in shots:
                shot.update({'sequence_name': dict["name"]})
        else:
            shots = gazu.user.all_shots_for_project(dict)
    else:
        if where == "from_sequence":
            shots = gazu.shot.all_shots_for_sequence(dict)
        else:
            shots = gazu.shot.all_shots_for_project(dict)

    return shots


def RemoveShot(shot_dict):
    return gazu.shot.remove_shot(shot_dict)


def GetAssets(proj_dict, asset_type, user=False, getCanceled=False):
    if user:
        assets = gazu.user.all_assets_for_asset_type_and_project(
            proj_dict,
            asset_type)
    else:
        assets = gazu.asset.all_assets_for_project_and_type(
            proj_dict,
            asset_type)

    return assets


def RemoveAsset(asset_dict):
    return gazu.asset.remove_asset(asset_dict)


def GetAssetType(asset_type_id, user=False):
    assetType = gazu.asset.get_asset_type(asset_type_id)
    return assetType


def RemoveAssetType(asset_type_dict):
    return gazu.asset.remove_asset_type(asset_type_dict)


def GetAssetTypes():
    return gazu.asset.all_asset_types()


def GetEntity(id):
    entity = gazu.entity.get_entity(id)
    return entity


def GetEpisodeName(ep_id):
    epDict = gazu.entity.get_entity(ep_id)["name"]
    return epDict


# returns created, updated
def DownloadThumbnail(self, name, preview_file_id, folder_name):
    local_preview_id = self.core.getConfig(
        name, "thumbnailID", config=folder_name.lower()
    )

    if preview_file_id != local_preview_id:
        previewImgPath = os.path.join(
            os.path.dirname(self.core.prismIni),
            folder_name,
            "%s_preview" % name,
        )
        if preview_file_id is None:  # Thumbnail removed
            os.remove(previewImgPath + ".jpg")
            return "", False, True  # File updated

        else:  # Thumbnail added or changed
            file_exists = os.path.exists(previewImgPath + ".jpg")
            if file_exists is False or preview_file_id != local_preview_id:
                # Download the file
                extension = (gazu.files.get_preview_file(preview_file_id)
                             ["extension"])
                thumbnailPath = previewImgPath + "." + extension
                # Make path if it doesn't exist yet
                mkdir_p(
                    os.path.join(
                        os.path.dirname(self.core.prismIni),
                        folder_name
                    )
                )
                gazu.files.download_preview_file_thumbnail(
                    preview_file_id, thumbnailPath)
                # If not jpg, convert it
                if os.path.splitext(thumbnailPath)[1] != ".jpg":
                    # Get image data
                    pixmap = self.core.media.getPixmapFromPath(thumbnailPath)
                    # Save the image as a jpg
                    self.core.media.savePixmap(pixmap, previewImgPath + ".jpg")
                    # Delete old file
                    os.remove(thumbnailPath)

            if file_exists:  # If file got updated
                return preview_file_id, False, True
            else:  # If file didn't exist
                return preview_file_id, True, False

    return False, False, False


def createKitsuEpisode(project_dict, episode_name):
    """
    returns
        Episode dict
        If created new episode
    """
    if episode_name is None:
        return None, False

    episode_dict = gazu.shot.get_episode_by_name(project_dict, episode_name)
    if episode_dict is None:
        episode_dict = gazu.shot.new_episode(project_dict, episode_name)
        return episode_dict, True
    else:
        return episode_dict, False


def createKitsuSequence(project_dict, sequence_name, episode_dict):
    """
    returns
        Project dict
        If created new sequence
    """

    if episode_dict is None:
        sequence_dict = gazu.shot.get_sequence_by_name(project_dict,
                                                       sequence_name)
    else:
        sequence_dict = gazu.shot.get_sequence_by_name(project_dict,
                                                       sequence_name,
                                                       episode_dict)

    if sequence_dict is None:
        if episode_dict is None:
            sequence_dict = gazu.shot.new_sequence(project_dict,
                                                   sequence_name)
        else:
            sequence_dict = gazu.shot.new_sequence(project_dict,
                                                   sequence_name,
                                                   episode_dicts)
        return sequence_dict, True

    else:
        return sequence_dict, False


def createKitsuShot(project_dict, sequence_dict, shot_name, ranges):
    """
    returns
        Shot dict
        If created new shot
    """
    shot_dict = gazu.shot.get_shot_by_name(sequence_dict, shot_name)

    if shot_dict is None:
        if ranges is not None:
            shot_dict = gazu.shot.new_shot(project=project_dict,
                                           sequence=sequence_dict,
                                           name=shot_name,
                                           nb_frames=ranges[1] - ranges[0],
                                           frame_in=ranges[0],
                                           frame_out=ranges[1],
                                           data={})
        else:
            shot_dict = gazu.shot.new_shot(project=project_dict,
                                           sequence=sequence_dict,
                                           name=shot_name,
                                           data={})
        return shot_dict, True
    else:
        return shot_dict, False


def createKitsuAssetType(name):
    asset_type_dict = gazu.asset.get_asset_type_by_name(name)
    if asset_type_dict is None:
        asset_type_dict = gazu.asset.new_asset_type(name)
        return asset_type_dict, True
    else:
        return asset_type_dict, False


def createKitsuAsset(project_dict,
                     asset_type_dict,
                     asset_name,
                     asset_description,
                     extra_data={},
                     episode=None):
    """
    returns
        asset dict
        If created new asset
    """
    asset_dict = gazu.asset.get_asset_by_name(project_dict, asset_name)

    if asset_dict is None:
        asset_dict = gazu.asset.new_asset(
            project_dict,
            asset_type_dict,
            asset_name,
            asset_description,
            extra_data,
            episode
        )
        return asset_dict, True
    else:
        return asset_dict, False


def uploadThumbnail(entity_id, thumbnail_URL, task_type_dict, user_Email):
    preview_dict = uploadRevision(entity_id,
                                  thumbnail_URL,
                                  task_type_dict,
                                  user_Email)
    gazu.task.set_main_preview(preview_dict)
    entity_dict = gazu.entity.get_entity(entity_id)
    return entity_dict["preview_file_id"]


def uploadRevision(entity_id,
                   thumbnail_URL,
                   task_type_dict,
                   user_Email,
                   comment=""):

    entity_dict = gazu.entity.get_entity(entity_id)
    person_dict = gazu.person.get_person_by_email(user_Email)
    task_dict = gazu.task.get_task_by_name(entity_dict, task_type_dict)
    if task_dict is None:
        task_dict = gazu.task.new_task(entity_dict, task_type_dict)

    task_status = gazu.task.get_task_status(task_dict)
    comment_dict = addComment(task_dict,
                              task_status,
                              comment=comment,
                              person=person_dict)

    preview_dict = gazu.task.add_preview(task_dict,
                                         comment_dict,
                                         thumbnail_URL)

    return preview_dict


def addComment(task, task_status="todo", comment="", person=None):
    if not isinstance(task_status, dict):
        if task_status is None:
            task_status = "todo"
        task_status = gazu.task.get_task_status_by_short_name(task_status)
    if person is not None:
        person = gazu.person.get_person_by_email(person)

    comment_dict = gazu.task.add_comment(task, task_status, comment, person)

    return comment_dict


def getTaskTypes(dict=None):
    tasks = None
    if dict is None:
        tasks = gazu.task.all_task_types()
    elif dict["type"] == "Episode":
        tasks = gazu.task.all_task_types_for_episode(dict)
    elif dict["type"] == "Sequence":
        tasks = gazu.task.all_task_types_for_sequence(dict)
    elif dict["type"] == "Scene":
        tasks = gazu.task.all_task_types_for_scene(dict)
    elif dict["type"] == "Shot":
        tasks = gazu.task.all_task_types_for_shot(dict)
    elif dict["type"] == "Asset":
        tasks = gazu.task.all_task_types_for_asset(dict)
    else:
        tasks = gazu.task.all_task_types()

    return tasks
