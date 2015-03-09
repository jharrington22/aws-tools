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
    """
        Progress bar to be used with create_snapshot()
    """
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
    return {"Name": instance_name, "instance": _instance}


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


def create_snapshot(conn, instance_id=None, volume_id=None, instance_name=None, snapshot_name=None, progress=None, description_format=None, retention=None):
    """
        Create snapshot using instance name or volume id
        Appends datetime (UTC) to instance name
        instance = instance object
        volume_id = Volume ID
        instance_name = Name of instance (Tag: Name)
        snapshot_name = Name for snapshot
        progress = progress bar (not used yet)
        description_format = enables retention
        retention = dict with retention period and delta
    """
    _datetime = datetime.utcnow().strftime("%Y-%m-%d-%H:%M:%S")
    # Create snapshot for each attached volume
    def progress_output(snapshot):
        while not snapshot.status == "completed":
            snapshot.update()
            if not snapshot.progress == "":
                update_progress(int(snapshot.progress.strip("%")))
            time.sleep(1)
    def snapshot_volume(_volume, _identifier, _snapshot_name=None):
        """
            _volume = volume instance
            _identifier = Always set either volume_id, instance_id, instance_name
            _snapshot_name = Set if specified on command line
        """
        if not _snapshot_name:
            # Description format enables snapshot retention
            if description_format:
                _description_format = description_format.split("_")
                _description = _description_format[0] + "_" + retention["period"] + "_" + _identifier + "_" + _volume.attach_data.device + "_" + _datetime
                # Remove time for snapshot name
                _snapshot_name = "_".join(_description.split("_")[:4])
            else:
                _snapshot_name = "%s_%s_%s" % (_identifier, _volume.attach_data.device, _datetime)
                _description = "%s_%s_%s" % (_identifier, _volume.attach_data.device, _datetime)
        else:
            if description_format:
                _description_format = description_format.split("_")
                _description = _description_format[0] + "_" + retention["period"] + "_" + _snapshot_name + "_" + _volume.attach_data.device + "_" + _datetime
            else:
                _description = _snapshot_name
        # Create snapshot
        snapshot = conn.create_snapshot(_volume.id, description=_description)
        # TODO: Do i need to wait here?
        time.sleep(5)
        # Add snapshot name
        snapshot.add_tag("Name", _snapshot_name)
        print("Started creating snapshot: %s" % snapshot)
        if progress:
            progress_output(snapshot)
    # Create snapshot
    if volume_id:
        try:
            _volume = conn.get_all_volumes([volume_id])
        except boto.exception.EC2ResponseError:
            print("ERROR: No Volume ID: %s" % volume_id)
            sys.exit(1)
        identifier = volume_id
        snapshot_volume(_volume[0], identifier, snapshot_name)
    elif instance_id:
        try:
            instance = conn.get_only_instances([instance_id])[0]
        except boto.exception.EC2ResponseError:
            print("ERROR: No Instance ID: %s" % instance_id)
            sys.exit(1)
        _volumes = get_volumes_from_instance(conn, instance.id)
        identifier = instance.id
        for volume in _volumes:
            snapshot_volume(volume, identifier, snapshot_name)
    elif instance_name:
        instance_dict = get_instance_id_from_instance_name(conn, arguments.instance_name)
        _volumes = get_volumes_from_instance(conn, instance_dict["instance"].id)
        identifier = instance_name
        for volume in _volumes:
            snapshot_volume(volume, identifier, snapshot_name)
    else:
        print("Not enough arguments for create_snapshot()")
        sys.exit(1)
    # Run backup retention
    if description_format:
        snapshot_retention(description_format, identifier, retention)


def list_instance_details(verbose=False, instance_name=None):
    """
    Returns a tag or dict containing instance details
    Name - Tag: Name
    ID - Instance ID
    Volumes - List of volume IDs
    """
    if instance_name:
        _reservations = conn.get_all_reservations(filters={"tag:Name": instance_name})
    else:
        _reservations = conn.get_all_reservations()
    for reservation in _reservations:
        tag = get_instance_tags(reservation.instances[0].id)
        if verbose:
            instance_dict = {
                "Name": tag["Name"],
                "ID": reservation.instances[0].id,
                "Volumes": get_volumes_from_instance(conn, reservation.instances[0].id)
            }
            yield instance_dict
        else:
            # get_instance_id_from_instance_name(conn, tag["Name"])
            yield tag


def snapshot_retention(description_format, identifier, retention):
    """````
    identifier = snapshot_name or volume id
    retention = dict of period and delta
    """
    def date_compare(snap1, snap2):
        """ Sort snapshots oldest to newest """
        if snap1.start_time < snap2.start_time:
            return -1
        elif snap1.start_time == snap2.start_time:
            return 0
        return 1
    snapshots = conn.get_all_snapshots()
    del_snapshots = []
    for snapshot in snapshots:
        if snapshot.description.startswith("aws-tools"):
            # Build a dictionary with retention period and instance details
            retention_details = dict(zip(description_format.split("_"), snapshot.description.split("_")))
            if retention_details["PERIOD"] == retention["period"] and retention_details["INSTANCE"] == identifier:
                del_snapshots.append(snapshot)
    del_snapshots.sort(date_compare)
    # delete the first x snapshots leaving the retention amount.
    # list [ old -> new ]
    # Delete none if there are not enough snapshots
    if len(del_snapshots) > retention[retention["period"]]:
        delete = len(del_snapshots) - retention[retention["period"]]
    else:
        delete = 0
    print("Snapshots available to delete: %s, Number of snapshots to keep: %s, Number of snapshots to delete: %s") % (len(del_snapshots), retention[retention["period"]], delete)
    print("Available snapshots to delete (ID's): %s" % del_snapshots)
    print("Deleting snapshots..")
    for i in range(delete):
        del_snapshots[i].delete()
        print("\tDeleted: %s" % del_snapshots[i])


def get_instance_tags(instance_id):
    _tags = conn.get_all_tags({'resource-id': instance_id})
    for tag in _tags:
        if not tag.name.startswith('aws:'):
            return {tag.name: tag.value}


if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(description="EC2 snapshot tool", usage='%(prog)s [options]')
    # Authentication Arguments
    parser.add_argument("--access-id", "-a", action="store")
    parser.add_argument("--secret-key", "-s", action="store")
    # Retention arguments
    parser.add_argument("--hours", action="store")
    parser.add_argument("--days", "-d", action="store")
    parser.add_argument("--weeks", "-w", action="store")
    parser.add_argument("--months", "-m", action="store")
    # Instance identification
    parser.add_argument("--volume-id", "-i", action="store")
    parser.add_argument("--instance-id", action="store")
    parser.add_argument("--instance-name", "-n", action="store")
    parser.add_argument("--region", "-r", action="store")
    # Snapshot options
    parser.add_argument("--snapshot-create", "-c", action="store_true")
    parser.add_argument("--snapshot-name", action="store")
    parser.add_argument("--snapshot-delete", action="store_true")
    parser.add_argument("--snapshot-info", action="store_true")
    # Diagnostics
    parser.add_argument("--list-instances", "-l", action="store_true")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--progress", "-p", action="store_true")
    arguments = parser.parse_args()

    # Load local config file location if it exists
    # Prefers command line arguments to config file if specified
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

    if arguments.list_instances:
        for instance_dict in list_instance_details(instance_name=arguments.instance_name, verbose=arguments.verbose):
            if arguments.verbose:
                for key in instance_dict.keys():
                    if key == "Volumes":
                        for volume in instance_dict[key]:
                            print "Volume: %s, Device: %s" % (volume.id, volume.attach_data.device)
                    else:
                        print "%s: %s" % (key, instance_dict[key])
            else:
                print instance_dict["Name"]
        sys.exit(0)

    # Volume id OR instance name must be specified
    if not arguments.volume_id and not arguments.instance_name and not arguments.instance_id:
        print("Error: %s: Volume ID (--volume-id), Instance ID (--instance-id) or Instance Name (-n) must be specified.\n" % sys.argv[0].split("/")[-1])
        #print(parser.print_help())
        #sys.exit(1)

    # Create snapshot
    if arguments.snapshot_create:
        # Setup retention
        if arguments.hours:
            # Hourly retention is enabled
            retention = {"period": "hourly", "hourly": int(arguments.hours)}
            retention_format = 'aws-tools_PERIOD_INSTANCE_DEVICE_TIME'
        elif arguments.days:
            # Daily Retention is enabled
            retention = {"period": "days", "days": arguments.days}
            retention_format = 'aws-tools_PERIOD_INSTANCE_DEVICE_TIME'
        elif arguments.weeks:
            # Weekly retention is enabled
            retention = {"period": "weeks", "weeks": arguments.days}
            retention_format = 'aws-tools_PERIOD_INSTANCE_DEVICE_TIME'
        elif arguments.months:
            # Monthly retention is enabled
            retention = {"period": "months", "months": arguments.days}
            retention_format = 'aws-tools_PERIOD_INSTANCE_DEVICE_TIME'
        else:
            retention_format = None
            retention = None
        if arguments.instance_name:
            print("Create snapshot from instance name: %s" % arguments.instance_name)
            # Create snapshot with retention
            create_snapshot(conn,
                            instance_name=arguments.instance_name,
                            description_format=retention_format,
                            retention=retention
                            )
        if arguments.volume_id:
            print("Create snapshot from volume id: %s" % arguments.volume_id)
            create_snapshot(conn,
                            volume_id=arguments.volume_id,
                            description_format=retention_format,
                            retention=retention
                            )
        if arguments.instance_id:
            print("Create snapshot from volume id: %s" % arguments.instance_id)
            create_snapshot(conn,
                            instance_id=arguments.instance_id,
                            description_format=retention_format,
                            retention=retention
                            )
    else:
        print("Not creating snapshot")
