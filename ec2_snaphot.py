import os
import boto.ec2
import ConfigParser
from datetime import datetime

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
conn = boto.ec2.EC2Connection(aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region=region)


def get_instance_id_from_instance_name(conn, instance_name):
    """
        Return instance object from "name" tag
    """
    instance = conn.get_all_reservations(filters={"tag:Name":instance_name})[0].instances[0]
    return instance_name, instance


def get_volume_from_instance_id(conn, instance_id):
    """
        Return list of volume attached to instance id
        Each volume returned is a list
        ["volume-id", "attachment", "type", "size"]
    """
    volumes = conn.get_all_volumes()
    attached_volumes = []
    for volume in volumes:
        if volume.attach_data.instance_id == instance_id:
            attached_volumes.append((volume.id, volume.attach_data.device, volume.type, volume.size))
    return attached_volumes


def create_snapshot(conn, instance_tuple):
    """
        Create snapshot of each volume attached to instance_id
        Appends datetime (UTC) to instance name
    """
    _datetime = datetime.utcnow().strftime("%Y-%m-%d-%H:%M:%S")
    _volume_id = get_volume_from_instance_id(conn, instance_tuple[1].id)
    # Create snapshot for each attached volume
    for volume in _volume_id:
        _instance_name = "%s_%s" % (instance_tuple[0], _datetime)
        conn.create_snapshot(volume[0], _instance_name)


# Possibly name snapshots monthly: weekly: daily: fortnightly:

instance_name = ""
instance_tuple = get_instance_id_from_instance_name(conn, instance_name)
instance_id = get_instance_id_from_instance_name(conn, instance_name)


#create_snapshot(conn, instance_tuple)


