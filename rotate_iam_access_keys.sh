#!/bin/bash

usage() {
    cat <<EOF
    usage: $0 [ OPTION ]
    Options
    -u         AWS IAM user name (Required)
    -p         AWS Profile, leave blank for none
    -r         AWS Region leave blank for default us-east-1
EOF
}

if ( ! getopts ":u:p:r:h" opt); then
    echo ""
    echo "    $0 requries an argument!"
    usage
    exit 1 
fi

while getopts ":u:p:r:h" opt; do
    case $opt in
        u)
            AWS_IAM_USER="$OPTARG" >&2
            ;;
        p)
            AWS_DEFAULT_PROFILE="$OPTARG" >&2
            ;;
        r)
            AWS_DEFAULT_REGION="$OPTARG" >&2
            ;;
        h)
            echo "Invalid option: -$OPTARG" >&2
            usage
            exit 1
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            exit 1
            ;;
        :)
            echo "$0 Requires an argument" >&2
            usage
            exit 1
            ;;
        esac
    done


if [ -z "$AWS_IAM_USER" ]; then
	usage
fi

if [ -z "$AWS_DEFAULT_REGION" ]; then
	export AWS_DEFAULT_REGION="us-east-1"
else
	export AWS_DEFAULT_REGION=$AWS_DEFAULT_REGION
fi

if ! [ -z "$AWS_DEFAULT_REGION" ]; then
	export AWS_PROFILE=$AWS_DEFAULT_PROFILE
fi

#cat staging1new-accounts-list.json | jq -r --arg AWS_ACCOUNT_ID_ARG "$ACC_ID" '.Accounts[] | select(.Id==$AWS_ACCOUNT_ID_ARG)'
IAM_USER=$(aws iam list-users | jq --arg AWS_IAM_USER "$AWS_IAM_USER" '.Users[] | select(.UserName==$AWS_IAM_USER) | .UserName' | tr -d '"' )

if [ "$IAM_USER" = "$AWS_IAM_USER" ]; then
    echo "User $IAM_USER exists deleting access keys"
    for access_key in $(aws iam list-access-keys --user-name "$IAM_USER" | jq -r '.AccessKeyMetadata[].AccessKeyId')
    do
        aws iam delete-access-key --user-name "$IAM_USER" --access-key "$access_key"
    done
    aws iam create-access-key --user-name "$IAM_USER"
	echo "Rotated access keys for $IAM_USER"
else 
    echo "Can't find IAM user: $AWS_IAM_USER"
fi
