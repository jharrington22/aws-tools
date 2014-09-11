#!/usr/bin/python

import os
import boto
import ConfigParser
from boto import glacier

# Config file location, home directory by default
configFile = '~/.aws_tools.cfg'
configFile = os.path.expanduser(configFile)

config = ConfigParser.ConfigParser()
config.readfp(open(configFile))

# AWS Credentials from config file
aws_access_key = config.get("awsCredentials", 'accessKey')
aws_secret_key = config.get("awsCredentials", 'accessSecret')

# Vault name
vaultName = ""

# SNS Topic
snsTopic = ""

regions = glacier.regions()

glacier_connection = boto.glacier.layer2.Layer2(aws_access_key, aws_secret_key, region=regions[2])

print glacier_connection.list_vaults()

vault = glacier_connection.get_vault(vaultName)

print "Vault"
print vault

file = ""

#print vault.upload_archive(file)


#print vault.retrieve_inventory(sns_topic=snsTopic)
#vault = glacier_connection.create_vault("")

#print vault
