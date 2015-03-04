import os
import sys
import time
import boto.ec2
import argparse
import ConfigParser
from datetime import datetime


def return_region(region_name):
    """
        Return region object
    """
    return boto.ec2.get_region(region_name)


def update_progress(progress):
    barLength = 100 # Modify this to change the length of the progress bar
    status = ""
    if not isinstance(progress, int):
        progress = 0
        status = "error: progress var must be int\r\n"
    block = progress
    if not progress == float(100):
        text = "\rPercent: [{0}] {1}%".format("#"*block + "-"*(barLength-block), progress)
    else:
        text = "\rPercent: [{0}] {1}% {2}".format("#"*block + "-"*(barLength-block), progress, "Complete..\r\n")
    sys.stdout.write(text)
    sys.stdout.flush()


def get_instance_id_from_instance_name(conn, instance_name):
    """
        Return instance object from "name" tag
    """
    try:
        _instance = conn.get_all_reservations(filters={"tag:Name": instance_name})[0].instances[0]
    except IndexError:
        print("No instnace with name: %s\n try -l to list instance names" % instance_name)
        sys.exit(1)
    return instance_name, _instance


def get_volumes_from_instance(conn, instance_id):
    """
        Return a volume instance
    """
    _volumes = conn.get_all_volumes()
    _attached_volumes = []
    for volume in _volumes:
        if volume.attach_data.instance_id == instance_id:
            _attached_volumes.append(volume)
    return _attached_volumes


def create_snapshot(conn, instance=None, snapshot_name=None, volume_id=None, progress=None):
    """
        Create snapshot using instance name or volume id
        Appends datetime (UTC) to instance name
    """
    # TODO: for command line usage present a progress bar
    # TODO: Tag snapshots with a name
    _datetime = datetime.utcnow().strftime("%Y-%m-%d-%H:%M:%S")
    # Create snapshot for each attached volume

    def snapshot_volume(_volume, _snapshot_name=None):
        if not _snapshot_name:
            _snapshot_name = "%s_%s_%s" % (_volume.id, _volume.attach_data.device, _datetime)
        else:
            _snapshot_name = "%s_%s_%s" % (_snapshot_name, _volume.attach_data.device, _datetime)
        snapshot = conn.create_snapshot(_volume.id, description=_snapshot_name)
        snapshot.add_tag("Name", _snapshot_name)
        print("Started creating snapshot: %s" % snapshot)
        if progress:
            while not snapshot.status == "completed":
                snapshot.update()
                if not snapshot.progress == "":
                    update_progress(int(snapshot.progress.strip("%")))
                time.sleep(1)
    if volume_id:
        _volume = conn.get_all_volumes([volume_id])
        snapshot_volume(_volume[0], snapshot_name)
    else:
        # TODO: These volumes for the same instance are going to have the same snapshot name - append device
        _volumes = get_volumes_from_instance(conn, instance.id)
        for volume in _volumes:
            # Get device name for volume snapshot
            #_device = volume.attach_data.device
            snapshot_volume(volume, snapshot_name)


def get_instance_tags(instance_id):
    _tags = conn.get_all_tags({'resource-id': instance_id})
    for tag in _tags:
        if not tag.name.startswith('aws:'):
            print("Instance Tags: %s: %s" % (tag.name, tag.value))

def set_resource_tag(resource_id):
    pass


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
    # Diagnostics
    parser.add_argument("--progress", "-p", action="store_true")
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
        print("Warning: No configuration file: %s\n" % config_file)

    # Set region
    if arguments.region:
        arguments.region = return_region(arguments.region)
    else:
        print("No region name")
        region_name = ""

    # Make EC2 Connection
    conn = boto.ec2.EC2Connection(aws_access_key_id=arguments.access_id, aws_secret_access_key=arguments.secret_key, region=arguments.region)

    # Volume id OR instance name must be specified
    if not arguments.volume_id and not arguments.instance_name:
        print("Error: %s: Volume ID (-i) or Instance Name (-n) must be specified.\n" % sys.argv[0].split("/")[-1])
        print(parser.print_help())
        sys.exit(1)
    if arguments.volume_id and arguments.instance_name:
        print("Error: %s: Volume ID (-i) or Instance Name (-n) only must be specified.\n" % sys.argv[0].split("/")[-1])
        print(parser.print_help())
        sys.exit(1)

    # Create snapshot
    if arguments.snapshot_create:
        if arguments.instance_name:
            print("Create snapshot from instance name: %s" % arguments.instance_name)
            instance_tuple = get_instance_id_from_instance_name(conn, arguments.instance_name)
            create_snapshot(conn, instance=instance_tuple[1], snapshot_name=instance_tuple[0], progress=arguments.progress)
        if arguments.volume_id:
            print("Create snapshot from volume id: %s" % arguments.volume_id)
            create_snapshot(conn, volume_id=arguments.volume_id, progress=arguments.progress)
    else:
        print("Not creating snapshot")



    # Possibly name snapshots monthly: weekly: daily: fortnightly:

    if arguments.instance_name:
        instance_name = arguments.instance_name
    else:
        print("No instance name")
        instance_name = ""


    # instance_tuple = get_instance_id_from_instance_name(conn, instance_name)

    # create_snapshot(conn, instance_tuple)
    # get_instance_tags(instance_tuple[1].id)

    #create_snapshot(conn, instance_tuple)


