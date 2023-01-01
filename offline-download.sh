#!/bin/bash

BUCKET_NAME=gs://task-search-bucket

# $1 - local folder name
# $2 - name of zipped file
download () {

    # Check if remote file exists
    REMOTE_PATH=$BUCKET_NAME/$2.zip
    gsutil -q stat $REMOTE_PATH
    status=$?
    if [[ $status == 1 ]]; then
    echo "Remote file $REMOTE_PATH does not exist..."
    exit 1
    fi
    
    # Download zipped folder and delete local folder if exists
    LOCAL_PATH=$PWD/$1
    mkdir=$PWD/test
    if [ -d "$LOCAL_PATH" ]; then
        echo "Are you sure you want to delete ${LOCAL_PATH}? [Y/n]"
        read -r -p "Are you sure? [y/N] " response
        case "$response" in
            [yY][eE][sS]|[yY]) 
                gsutil -m cp $BUCKET_NAME/$2.zip $PWD/$2.zip
                echo "Deleting local offline directory..."
                rm -r $LOCAL_PATH
                ;;
            *)
                echo "Exiting script..."
                exit 0
                ;;
        esac
    else
        gsutil -m cp $BUCKET_NAME/$2.zip $PWD/$2.zip
    fi

    echo "Unzipping $PWD/$2/ to $LOCAL_PATH "
    unzip ${PWD}/$2.zip -d $PWD/test/

    # Remove zipped file
    rm ${PWD}/$2.zip

}

while getopts 'idta' OPTION; do
  case "$OPTION" in
    i)
      echo "Downloading remote indexes..."
      download indexes indexes
      echo "Successfully downloaded indexes!"
      exit 0
      ;;
    d)
      echo "Downloading remote datasets..."
      download task_datasets task_datasets
      echo "Successfully downloaded datasets!"

      exit 0
      ;;
    t)
      echo "Downloading remote taskgraph objects..."
      download bin taskgraphs 
      echo "Successfully downloaded taskgraphs!"
      exit 0
      ;;
      
    a)
      echo "Downloading remote indexes, remote datasets, and remote taskgraph objects..."
      download indexes indexes
      download task_datasets task_datasets
      download bin taskgraphs
      echo "Successfully downloaded artefacts!"
      exit 0
      ;;
    ?)
      echo "script usage: $(basename \$0) [-i] [-d] [-a]" >&2
      exit 1
      ;;
  esac
done
shift "$(($OPTIND -1))"


# CONFIG=${PWD}/offline-version.txt
# BUCKET_NAME=gs://task-search-bucket

# INDEX_PATH="indexes"
# TASK_DATASETS_PATH="task_datasets"


# SNAPSHOT_ID=`cat ${CONFIG}`
# echo "Snapshot ID: $SNAPSHOT_ID"

# REMOTE_VERSIONS=`gsutil ls "${BUCKET_NAME}/offline/"`

# REMOTE_EXISTS=false
# for VERSION in $REMOTE_VERSIONS
# do
#     if [[ "$VERSION" == *"$SNAPSHOT_ID"* ]]; then
#         REMOTE_EXISTS=true
#     fi
# done
# if [ $REMOTE_EXISTS = false ]; then
#     echo "Could not find remote snapchot with ID: $SNAPSHOT_ID"
#     exit 1
# fi

# echo "Are you sure you want to delete ${LOCAL_FOLDER_PATH}? [Y/n]"
# read -r -p "Are you sure? [y/N] " response
# case "$response" in
#     [yY][eE][sS]|[yY]) 
#         echo "Deleting local offline directory..."
#         rm -r ${PWD}/${INDEX_PATH}
#         rm -r ${PWD}/${TASK_DATASETS_PATH}
#         ;;
#     *)
#         exit 0
#         ;;
# esac

# echo "Downloading files..."
# gsutil -m cp ${BUCKET_NAME}/offline/${SNAPSHOT_ID}*/offline.zip ${PWD}/offline.zip
# unzip ${PWD}/offline.zip -d ${PWD}
# rm ${PWD}/offline.zip
# echo "Download successful!"