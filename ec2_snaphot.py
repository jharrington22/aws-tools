import os
import sys
import boto.ec2
import argparse
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
    _instance = conn.get_all_reservations(filters={"tag:Name": instance_name})[0].instances[0]
    return instance_name, _instance


def get_volume_from_instance_id(conn, instance_id):
    """
        Return a volume instance
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
    # Argument parser
    parser = argparse.ArgumentParser(description="EC2 snapshot tool", usage='%(prog)s [options]')
    # Authentication Arguments
    parser.add_argument("--access-id", "-a", action="store")
    parser.add_argument("--secret-key", "-s", action="store")
    # Retention arguments
    parser.add_argument("--days", "-d", action="store")
    parser.add_argument("--weeks", "-w", action="store")
    parser.add_argument("--months", "-m", action="store")
    # Instance identification
    parser.add_argument("--volume-id", "-i", action="store")
    parser.add_argument("--instance-name", "-n", action="store")
    parser.add_argument("--region", "-r", action="store")
    # Snapshot options
    parser.add_argument("--snapshot-create", "-c", action="store_true")
    parser.add_argument("--snapshot-name", action="store")
    parser.add_argument("--snapshot-delete", action="store_true")
    parser.add_argument("--snapshot-info", action="store_true")
    arguments = parser.parse_args()

    # TODO: Prefer arguments over config file
    # Load local config file location if it exists
    config_file = '~/.aws_tools.cfg'
    try:
        config_file = os.path.expanduser(config_file)
        config = ConfigParser.ConfigParser()
        config.readfp(open(config_file))
        # AWS Credentials from config file
        if not arguments.access_id:
            arguments.access_id = config.get("awsCredentials", 'accessKey')
        if not arguments.secret_key:
            arguments.secret_key = config.get("awsCredentials", 'accessSecret')
    except IOError:
        print("No configuration file: %s" % config_file)

    # Volume id OR instance name must be specified
    if not arguments.volume_id and not arguments.instance_name:
        print("%s: Volume ID (-i) or Instance Name (-n) must be specified." % sys.argv[0].split("/")[-1])
        print(parser.print_help())
        sys.exit(1)
    if arguments.volume_id and arguments.instance_name:
        print("%s: Volume ID (-i) or Instance Name (-n) only must be specified." % sys.argv[0].split("/")[-1])
        print(parser.print_help())
        sys.exit(1)

    # Create snapshot
    if arguments.snapshot_create:
        if arguments.snapshot_name:
            print("Creating snapshot with name: %s" % arguments.snapshot_name)
        if arguments.volume_id:
            print("Create snapshot from volume id: %s" % arguments.volume_id)
    else:
        print("Not creating snapshot")

    # Test config
    if arguments.region:
        arguments.region = return_region(arguments.region)
    else:
        print("No region name")
        region_name = ""

    # Make EC2 Connection
    conn = boto.ec2.EC2Connection(aws_access_key_id=arguments.access_id, aws_secret_access_key=arguments.secret_key, region=arguments.region)

    # Possibly name snapshots monthly: weekly: daily: fortnightly:

    if arguments.instance_name:
        instance_name = arguments.instance_name
    else:
        print("No instance name")
        instance_name = ""


    instance_tuple = get_instance_id_from_instance_name(conn, instance_name)

    # create_snapshot(conn, instance_tuple)
    get_instance_tags(instance_tuple[1].id)

    #create_snapshot(conn, instance_tuple)


