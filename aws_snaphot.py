import os
import boto.ec2
import ConfigParser


def return_region(region_name):
    """Return region object"""
    return boto.ec2.get_region(region_name)


# Config file location, home directory by default
config_file = '~/.aws_tools.cfg'
config_file = os.path.expanduser(config_file)

config = ConfigParser.ConfigParser()
config.readfp(open(config_file))

# Cache file location, home directory by default
cache_file = '~/.glacier_sync_cache.cfg'
cache_file = os.path.expanduser(cache_file)

# AWS Credentials from config file
AWS_ACCESS_KEY = config.get("awsCredentials", 'accessKey')
AWS_SECRET_ACCESS_KEY = config.get("awsCredentials", 'accessSecret')


# Test config
region_name = "ap-southeast-2"

region = return_region(region_name)

# Make EC2 Connection
conn = boto.ec2.EC2Connection(aws_access_key_id=AWS_ACCESS_KEY,aws_secret_access_key=AWS_SECRET_ACCESS_KEY,region=region)

# List volumes
for reservation in conn.get_all_instances():
    print reservation.instances
    print reservation.instances[0].id

for instance_status in conn.get_all_instance_status():
    print instance_status

print conn.get_all_tags()