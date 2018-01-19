#!/usr/bin/python

# from boto.s3.connection import S3Connection
import ConfigParser
import hashlib
import json
import sys
import os
from sys import argv

# Defaults
# Config file location, home directory by default
configFile = '~/Documents/development/repos/aws-tools/.aws_tools.cfg'
configFile = os.path.expanduser(configFile)

config = ConfigParser.ConfigParser()
config.readfp(open(configFile))

# AWS Credentials from config file
aws_access_key = config.get("awsCredentials", 'accessKey')
aws_secret_key = config.get("awsCredentials", 'accessSecret')

# log_file = config.get("log", "logPath")


def md5_check(path, key):
    """Check key's local MD5 sum against the s3's"""
    md5 = get_md5(path + str(key.name))
    etag = key.etag.strip('"').strip("'")
    if etag != md5:
        return False
    else:
        return True


def get_md5(filename):
    """Return filename's MD5 sum"""
    try:
        f = open(filename, 'rb')
        mhash = hashlib.md5()
        while True:
            data = f.read(10240)
            if len(data) == 0:
                break
            mhash.update(data)
        return mhash.hexdigest()
    except IOError:
        print("MD5 ERROR File does not exist: %s" % filename)


def check_path_exists(path):
    """Return True if path exists else print error & exit"""
    if os.path.exists(path):
        return True
    else:
        print("Error: Path does not exist! %s" % path)
        sys.exit(1)


def get_arguments():
    argumentsDict = {}
    argumentsDict["source"] = {}
    argumentsDict["destination"] = {}
    # Get source bucket and or destination
    try:
        objectSource = argv[1].split(":")
        if len(objectSource) == 2:
            if check_path_exists(objectSource[1]):
                argumentsDict["source"] = {"bucket": objectSource[0], "object": objectSource[1]}
        elif len(objectSource) == 1:
            if check_path_exists(objectSource[0]):
                argumentsDict["source"] = {"object": objectSource[0]}
        else:
            print("ERROR: too many split values on source")
    except IndexError:
        print("%s Requires two arguments to run, source not defined!" % argv[0])
        sys.exit(1)
    # Get destination bucket and or source
    try:
        objectDestination = argv[2].split(":")
        if len(objectDestination) == 2:
            if check_path_exists(objectDestination[1]):
                argumentsDict["destination"] = {"bucket": objectDestination[0], "object": objectDestination[1]}
        elif len(objectDestination) == 1:
            if check_path_exists(objectDestination[0]):
                argumentsDict["destination"] = {"object": objectDestination[0]}
        else:
            print("ERROR: too many split values on destination")
    except IndexError:
        print("%s Requires two arguments to run, destination not defined!" % argv[0])
        sys.exit(1)
    return argumentsDict


def main():

    testDict = get_arguments()

    # conn = S3Connection(aws_access_key, aws_secret_key)

    if "bucket" in testDict["source"]:
        print("Bucket for source is %s" % testDict["source"]["bucket"])
    else:
        print("Source has no specified bucket")

    print(json.dumps(testDict, indent=2))


if __name__ == "__main__":
    main()
