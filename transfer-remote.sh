#!/bin/bash

# Run ./offline-upload to save repository artefacts

# -i arg - flag stores indexes/ in the offline bucket
# -d arg - flag stores task_datasets/ in the offline bucket
# -t arg - flag stores bin/ in the offline bucket (taskgraph objects)
# -a arg - flag stores all artefacts in the offline bucket
# arg - either keyword upload or download

BUCKET_NAME=s3://task-search

# $1 - local folder name
# $2 - name of zipped file
upload () {
  echo "UPLOAD started!"
  # Zip contents
  echo "Zipping ${PWD}/$1/"
  zip -r $2.zip $1/
  
  # Remove folder in offline storage
  REMOTE_PATH=$BUCKET_NAME/$2.zip
  # gsutil -q stat $REMOTE_PATH
  status=$(aws s3 ls $REMOTE_PATH)
  if [[ -z $status ]]; then
    echo "Removing $REMOTE_PATH..."
    gsutil -q rm -r $REMOTE_PATH
  fi

  echo "Uploading ${PWD}/$1/ to $REMOTE_PATH"
  # gsutil -m cp -Z $PWD/$2.zip $REMOTE_PATH
  aws s3 cp  $PWD/$2.zip $REMOTE_PATH
  
  # Delete zipped folder
  rm $2.zip
}

download () {
  echo "Downlaod started!"
  # Check if remote file exists
  REMOTE_PATH=$BUCKET_NAME/$2.zip
  # gsutil -q stat $REMOTE_PATH
  status=$(aws s3 ls $REMOTE_PATH)
  if [[ -z $status ]]; then
  echo "Remote file $REMOTE_PATH does not exist..."
  exit 1
  fi
  
  # Download zipped folder and delete local folder if exists
  LOCAL_PATH=$PWD/$1
  mkdir=$PWD
  if [ -d "$LOCAL_PATH" ]; then
      echo "Are you sure you want to delete ${LOCAL_PATH}? [Y/n]"
      read -r -p "Are you sure? [y/N] " response
      case "$response" in
          [yY][eE][sS]|[yY]) 
              aws s3 cp $BUCKET_NAME/$2.zip $PWD/$2.zip
              echo "Deleting local offline directory..."
              rm -r $LOCAL_PATH
              ;;
          *)
              echo "Exiting script..."
              exit 0
              ;;
      esac
  else
      # gsutil -m cp $BUCKET_NAME/$2.zip $PWD/$2.zip
     aws s3 cp $BUCKET_NAME/$2.zip $PWD/$2.zip
  fi

  echo "Unzipping $PWD/$2/ to $LOCAL_PATH "
  unzip ${PWD}/$2.zip -d $PWD/

  # Remove zipped file
  rm ${PWD}/$2.zip
}

transfer () {
  if [[ $3 == "upload" ]]; then
    upload $1 $2
  elif [[ $3 == "download" ]]; then
    download $1 $2
  else
    echo "$3 not a valid argument. Either enter upload or download."
    exit 1
  fi
}


while getopts 'i:d:t:a:' OPTION; do
  case "$OPTION" in
    i)
      echo "Transferring local indexes..."
      transfer indexes indexes ${OPTARG}
      echo "Successfully transfered indexes!"
      exit 0
      ;;
    d)
      echo "Transferring local datasets..."
      transfer task_datasets task_datasets ${OPTARG}
      echo "Successfully transfered datasets!"
      exit 0
      ;;
    t)
      echo "Transferring local taskgraph objects..."
      transfer bin taskgraphs ${OPTARG}
      echo "Successfully transfered taskgraphs!"
      exit 0
      ;;
      
    a)
      echo "Transferring local indexes, local datasets, and local taskgraph objects..."
      transfer indexes indexes ${OPTARG}
      transfer task_datasets task_datasets ${OPTARG}
      transfer bin taskgraphs ${OPTARG}
      echo "Successfully transfered artefacts!"
      exit 0
      ;;
    ?)
      echo "script usage: $(basename \$0) [-i] [-d] [-a]" >&2
      exit 1
      ;;
  esac
done
shift "$(($OPTIND -1))"
