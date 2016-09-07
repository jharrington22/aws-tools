from boto.ec2.connection import EC2Connection

import boto.ec2
import json
import argparse
import sys


# TODO: Argparse regions / all regions
def get_instance_names_and_eips(_conn):
    def get_instance_tags(_conn, _instance_id):
        # Retrieve all instance tags
        _tags = _conn.get_all_tags({'resource-id': _instance_id})
        for tag in _tags:
            if not tag.name.startswith('aws:'):
                return {tag.name: tag.value}
    # Get all public elastic IP addresses
    try:
        eips = _conn.get_all_addresses()
    except boto.exception.EC2ResponseError:
        print "Cant retrieve IPs from %s region" % region
        sys.exit(1)
    # Create dict
    instances = {"Not assigned": []}
    instances_private = {"Not assigned": []}
    for eip in eips:
        if not eip.instance_id:
            instances["Not assigned"].append(eip.public_ip)
        else:
            tags = get_instance_tags(_conn, eip.instance_id)
            if tags["Name"]:
                name = tags["Name"]
            else:
                name = eip.instance_id
            if not name in instances:
                instances[name] = [eip.public_ip]
                try:
                    instances_private[name] = [eip.private]
                except AttributeError:
                    pass
            else:
                instances[name].append(eip.public_ip)
    return instances


def list_regions(region_name=None):
    if region_name:
        return boto.ec2.get_region(region_name)
    else:
        return boto.ec2.regions()


if __name__ == "__main__":
    # Argument Parser
    parser = argparse.ArgumentParser(description="Get Elastic IP List", usage='%(prog)s [options]')
    parser.add_argument("--region", "-r", action="store", help="Specify a region to return all EIPs for [Optional]")
    parser.add_argument("--all", "-a", action="store", help="Return EIPs from all regions [Optional]")
    arguments = parser.parse_args()

    inaccessable_regions = ["us-gov-west-1", "cn-north-1"]

    for region in list_regions():
        print region.name
        # Connect to region
        if region.name in inaccessable_regions:
            print "Bad region: %s" % region
        else:
            conn = EC2Connection(region=region)

            print json.dumps(get_instance_names_and_eips(conn), indent=2)
