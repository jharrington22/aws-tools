#!/bin/bash

usage() {
    cat <<EOF
    usage: $0 [ OPTION ]
    Options
    -a         AWS Account ID (10 digit int)
    -s         AWS Assume role session name (Can be arbitrary, blank will create session name "assumeRoleScript")
    -p         AWS Profile, leave blank for none
    -r         AWS Region leave blank for default us-east-1
EOF
}

if ( ! getopts ":a:s:p:r:h" opt); then
    echo ""
    echo "    $0 requries an argument!"
    usage
    exit 1 
fi

while getopts ":a:s:p:r:h" opt; do
    case $opt in
        a)
            AWS_ACCOUNT_ID="$OPTARG" >&2
            ;;
        p)
            AWS_DEFAULT_PROFILE="$OPTARG" >&2
            ;;
        s)
            AWS_SESSION_NAME="$OPTARG" >&2
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


AWS_STS_SESSION_NAME="$USER"

if [ -z "$AWS_ACCOUNT_ID" ]; then
	usage
    exit 1
fi

if [ -z "$AWS_DEFAULT_REGION" ]; then
	AWS_DEFAULT_REGION="us-east-1"
fi

if [ -z "$AWS_DEFAULT_REGION" ]; then
	AWS_SESSION_NAME="assumeRoleScript"
fi

# Assume role
AWS_ASSUME_ROLE=$(aws sts assume-role --role-arn arn:aws:iam::"${AWS_ACCOUNT_ID}":role/OrganizationAccountAccessRole --role-session-name ${AWS_STS_SESSION_NAME} --profile="${AWS_DEFAULT_PROFILE}")

AWS_ACCESS_KEY_ID=$(echo "$AWS_ASSUME_ROLE" | jq -r '.Credentials.AccessKeyId')
AWS_SECRET_ACCESS_KEY=$(echo "$AWS_ASSUME_ROLE" | jq -r '.Credentials.SecretAccessKey')
AWS_SESSION_TOKEN=$(echo "$AWS_ASSUME_ROLE" | jq -r '.Credentials.SessionToken')

export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY
export AWS_SESSION_TOKEN

aws sts get-caller-identity
