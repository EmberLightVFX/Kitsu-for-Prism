# Kitsu for Prism-Pipeline
This plugin lets you sync between Prism-Pipeline and cgwire\'s Kitsu.
Download this repo, rename the folder to Kitsu and place it under your Prism folder/Plugins/ProjectManagers
Restart Prism and any open DCC apps.

To install:
- Download the code in the top right corner
- Unzip the zip file
- Rename the folder to just Kitsu
- Place the folder in your Prism installation folder -> Plugins -> ProjectManagers
- Restart Prism.
Your folder path should look like this: Prism/Plugins/ProjectManagers/Kitsu/Scripts and external_modules folder
If it doesn't the plugin won't load.

Features:
- Sync shots and assets between Kitsu and Prism including frame range, descriptions and thumbnails
- Sync everything or only assigned shots and assets
- Open shots and assets in Kitsu from Prism
- Publish to Kitsu from Renders (If it's an image sequence it will convert it to a temp mov file before uploading and remove the local temp file after)
- Post sync features:
 - Checks for empty asset types, sequences and episodse on sync and asks if you want to delete them
 - Checks if the other side has shots/assets on sync and asks if you want to sync back
 - You can dissable post sync checks in the settings
- When creating a new shot/asset in Prism you can add it directly to Kitsu
- Does work with TV Shows but only Kitsu to Local, not the other way around (folder structure problems atm)

Wanted features:
- Posibility to sync comment and image from Save and comment within DCC apps
- Make publishing videos multiprocessing so the user can use Prism while it's uploading.
- Sync Task Types from Kitsu to Steps in Prism
- Open kitsus task-page from right-clicking on steps/categories

Todo:
- Popup saying when uploading data to Kitsu. Currently it just looks like Prism freezes
- Check for updates in createShots() instead of making the new shot or nothing
- Check for updates in createAsset() instead of making the new shot or nothing

*Note on assets:
Any first folder in the root of the assets folder is the Task Type (Characters/Environment/FX/Props/Custom) and the assets within that folder will be assigned to that task type.
Multiple subdirs isn\'t supported because of this. It\'s the only way I could think of to make it work nice with Kitsu while you still get the task types.*
