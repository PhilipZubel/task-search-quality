#!/bin/bash

# Run ./offline-upload to save the artefacts stored in shared/offline
# -m flag allows storing the artefacts as the main version

BUCKET_NAME=gs://task-search-bucket
VERSION=offline_dev
# check wheather artefacts should be saved as the main version
while getopts ":m" opt; do
  case $opt in
    m)
      echo "Deleting previous main storage..."
      gsutil -q rm -r "${BUCKET_NAME}/main*"
      echo "Saving to main storage..."
      VERSION="main"
      ;;
  esac
done

TIME=`date +%F-%T-%N`
REMOTE_PATH="offline/${VERSION}_${TIME}/"

INDEX_PATH="indexes"
TASK_DATASETS_PATH="task_datasets"

# override the versioning in offline-version.txt before uplaod
if [[ $VERSION == "main" ]]
then
  sudo echo "${VERSION}"> "$LOCAL_FOLDER_PATH/offline-version.txt"
else
  sudo echo "${VERSION}_${TIME}"> "$LOCAL_FOLDER_PATH/offline-version.txt"
fi


# echo "Zipping folders..."
# zip -r offline.zip $INDEX_PATH $TASK_DATASETS_PATH
# # unzip "${LOCAL_FOLDER_PATH}/offline.zip" -d test

# upload file
gsutil -m cp -Z "${PWD}/offline.zip" $BUCKET_NAME/$REMOTE_PATH
rm "${LOCAL_FOLDER_PATH}/offline.zip"

echo ""
echo "Artefacts uploaded to remote path $REMOTE_PATH"
echo "To download the artefacts save the following snapshot id to offline-version.txt inside shared/offline/"
echo ""

if [[ $VERSION == "main" ]]
then
  echo "snapshot id: $VERSION"
else
  echo "snapshot id: ${VERSION}_${TIME}"
fi