#!/bin/bash

# Include a offline-version.txt file to decide which offline storage version to download.
# In order to include the current version type `main` inside offline-version.txt

CONFIG=${PWD}/offline-version.txt
BUCKET_NAME=gs://task-search-bucket

INDEX_PATH="indexes"
TASK_DATASETS_PATH="task_datasets"


if [[ ! -f $CONFIG ]] 
then
    echo "File $CONFIG does not exist."
    echo "This file should contain the snapshot id of the version you want to download."
    echo "To pull the main version, write 'main' inside offline-version.txt."
    exit 1
fi

SNAPSHOT_ID=`cat ${CONFIG}`
echo "Snapshot ID: $SNAPSHOT_ID"

REMOTE_VERSIONS=`gsutil ls "${BUCKET_NAME}/offline/"`

REMOTE_EXISTS=false
for VERSION in $REMOTE_VERSIONS
do
    if [[ "$VERSION" == *"$SNAPSHOT_ID"* ]]; then
        REMOTE_EXISTS=true
    fi
done
if [ $REMOTE_EXISTS = false ]; then
    echo "Could not find remote snapchot with ID: $SNAPSHOT_ID"
    exit 1
fi

echo "Are you sure you want to delete ${LOCAL_FOLDER_PATH}? [Y/n]"
read -r -p "Are you sure? [y/N] " response
case "$response" in
    [yY][eE][sS]|[yY]) 
        echo "Deleting local offline directory..."
        rm -r ${PWD}/${INDEX_PATH}
        rm -r ${PWD}/${TASK_DATASETS_PATH}
        ;;
    *)
        exit 0
        ;;
esac

echo "Downloading files..."
gsutil -m cp ${BUCKET_NAME}/offline/${SNAPSHOT_ID}*/offline.zip ${PWD}/offline.zip
unzip ${PWD}/offline.zip -d ${PWD}
rm ${PWD}/offline.zip
echo "Download successful!"