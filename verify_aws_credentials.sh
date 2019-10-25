#!/bin/bash

IFS='
'

FILE=$1

if [ -z "$FILE" ]; then
    echo "File to parse needed!"
    exit 1
fi

n=0
e=0

for creds in $(cat "$FILE")
do
  ACCOUNT_NAME=$(echo $creds | awk '{print $1}')
  ACCOUNT_ID=$(echo $creds | awk '{print $2}')
  AWS_ACCESS_KEY_ID=$(echo -n $creds | awk '{print $3}' | base64 -d)
  if [ "$AWS_ACCESS_KEY_ID" = "" ]; then
      echo "ERROR: $ACCOUNT_NAME has no credentials"
      continue
  fi
  export AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID"
  export AWS_SECRET_ACCESS_KEY=$(echo -n $creds | awk '{print $4}' | base64 -d)
  aws sts get-caller-identity --region=us-east-1 > /dev/null 2>&1
  if [ $? != 0 ]; then
     echo "ERROR: $ACCOUNT_NAME credentials are invalid"
     ./aws-assume-role-cli.sh -a "$ACCOUNT_ID" -n "$ACCOUNT_NAME" -p staging1new
     ((e++))
  else 
    echo "Account: $ACCOUNT_NAME OK"
  fi
  # if [ $n = 10 ]; then
  #     break
  # fi
  ((n++))
  unset AWS_ACCESS_KEY_ID
  unset AWS_SECRET_ACCESS_KEY
  ACCOUNT_NAME=""
  ACCOUNT_ID=""
  AWS_ACCESS_KEY_ID=""
  AWS_SECRET_ACCESS_KEY=""
done

echo "$n OK accounts"
echo "$e ERROR accounts"

