import os
import boto.ec2
import ConfigParser
from datetime import datetime


def return_region(region_name):
    """
        Return region object
    """
    return boto.ec2.get_region(region_name)


def get_instance_id_from_instance_name(conn, instance_name):
    """
        Return instance object from "name" tag
    """
    _instance = conn.get_all_reservations(filters={"tag:Name":instance_name})[0].instances[0]
    return instance_name, _instance


def get_volume_from_instance_id(conn, instance_id):
    """
        Return tuple of volume information attached to instance id
        Each volume returned is a list
        ["volume-id", "device", "type", "size"]
    """
    _volumes = conn.get_all_volumes()
    _attached_volumes = []
    for volume in _volumes:
        if volume.attach_data.instance_id == instance_id:
            _attached_volumes.append(volume)
    return _attached_volumes


def create_snapshot(conn, instance_tuple):
    """
        Create snapshot of each volume attached to instance_id
        Appends datetime (UTC) to instance name
    """
    _datetime = datetime.utcnow().strftime("%Y-%m-%d-%H:%M:%S")
    _volumes = get_volume_from_instance_id(conn, instance_tuple[1].id)
    # Create snapshot for each attached volume
    for volume in _volumes:
        # Get device name for volume snapshot
        _device = volume.attach_data.device
        _instance_name = "%s_%s_%s" % (volume.id, _device, _datetime)
        conn.create_snapshot(volume[0], _instance_name)


def get_instance_tags(instance_id):
    _tags = conn.get_all_tags({'resource-id': instance_id})
    for tag in _tags:
        if not tag.name.startswith('aws:'):
            print tag.name, tag.value


if __name__ == "__main__":
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
    region_name = ""

    region = return_region(region_name)

    # Make EC2 Connection
    conn = boto.ec2.EC2Connection(aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region=region)

    # Possibly name snapshots monthly: weekly: daily: fortnightly:

    instance_name = ""
    instance_tuple = get_instance_id_from_instance_name(conn, instance_name)

    # create_snapshot(conn, instance_tuple)
    get_instance_tags(instance_tuple[1].id)

    #create_snapshot(conn, instance_tuple)


