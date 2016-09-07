#!/usr/bin/python

import os
import boto
import json
import argparse
import ConfigParser
from boto import glacier
import boto.sdb
from datetime import datetime


# Get parsed arguments
parser = argparse.ArgumentParser(description='AWS Glacier tool')
parser.add_argument('-c', '--check-job', action="store", help="Check specified job ID")
parser.add_argument('-r', action="store_true", dest="retrieve_job_status")
parser.add_argument('-j', action="store", dest="job_id")
parser.add_argument('-v', '--vault-name', action="store", help="Valut name")
parser.add_argument('-l', '--list-inventory', action="store_true", help="List inventory")
parser.add_argument('-s', '--sns-topic', action="store", help="SNS Topic")

args = parser.parse_args()


# Config file location, home directory by default
config_file = '~/.aws_tools.cfg'
config_file = os.path.expanduser(config_file)

config = ConfigParser.ConfigParser()
config.readfp(open(config_file))

# Cache file location, home directory by default
cache_file = '~/.glacier_sync_cache.cfg'
cache_file = os.path.expanduser(cache_file)

# AWS Credentials from config file
aws_access_key = config.get("awsCredentials", 'accessKey')
aws_secret_key = config.get("awsCredentials", 'accessSecret')


def create_job_dict(id, created, status, completed):
    """Returned dict of job id"""
    job_dict = {
        "id": id,
        "created": created,
        "status": status,
        "completed": completed
        }
    return job_dict


def request_vault_inventory(vault, sns_topic, archive_json=None):
    """Request vault inventory list, return False if there is an error"""
    print("Requesting vault %s inventory..." % vault)
    create_date = datetime.now()
    status = False
    completed = False
    try:
        job_id = vault.retrieve_inventory(sns_topic=sns_topic)
        print job_id
        status = "requested"
        job_dict = create_job_dict(job_id, create_date, status, completed)
    except Exception as e:
        print e
        print("error")
        job_dict = False
    return job_dict


def change_job_status(archive_json, job_id, status):
    """Change job status in archive_json"""
    updated = False
    for idx, job in enumerate(archive_json["jobs"]):
        if job_id == job["id"]:
            archive_json["jobs"][idx]["status"] = status
            updated = True
    if updated:
        print("Updated job: %s to %s" % (job_id, status))
    else:
        print("%s doesn't exist in cache")


def get_job_status(instance, job_id, vault_name, archive_json):
    try:
        job_instance = instance.get_job_output(vault_name, job_id)
        job_instance = True
    except Exception as e:
        print e.message
        job_instance = False
        active_jobs = False
        print("%s is no longer active" % job_id)
        if not archive_json is None:
            change_job_status(archive_json, job_id, "complete")
    return job_instance


def get_job(instance, vault_name, job):
    print instance.get_job_output(job, vault_name)


def check_cached_jobs():
    """Check status of job's in cache file"""
    pass

def get_vault(instance, vault_name):
    vault = instance.get_vault(vault_name)
    return vault


def check_job_id(instance, vault_name, job_id=None, archive_json=None):
    """Get Jobs status using layer1 boto connection"""
    active_jobs = False
    if job_id is None:
    # Check job status
        if not archive_json is None:
            for jobs in archive_json["jobs"]:
                if jobs["status"] == "active":
                    active_jobs = True
                    job_id = jobs["id"]
                    job_instance = get_job_status(instance, job_id, vault_name, archive_json)
        else:
            print("No jobs to check")
            job_instance = False
    else:
        job_instance = get_job_status(instance, job_id, vault_name, archive_json)
        if job_instance:
            print("Active job: %s" % job_id)
            active_jobs = True
    if not active_jobs:
        print("This vault has no active jobs.. ")
        job_instance = False
    return job_instance


def save_archive_data(archive_data, archive_json_file):
    """Save archive data to json file"""
    with open(archive_json_file, 'w') as archive_json_file_fp:
        json.dump(archive_data, archive_json_file_fp)


def load_archive_data(archive_json_file):
    """Load archive data from json file"""
    if os.path.exists(archive_json_file):
        with open(archive_json_file, 'r') as archive_json_file_fp:
            result = json.load(archive_json_file_fp)
            return result
    else:
        print("Loading json template..")
        result = {
            "jobs": [{
                "id": "wEOZmsdfKBfaHbr_wLHMrlXqIamtUALhudsfaUmsldfmwMsMiN8MPexEllGKqsfxF7hShjR",
                "created": str(datetime.strptime("2014:10:19-22:55:32", "%Y:%m:%d-%H:%M:%S")),
                "status": "inactive",
                "completed": str(datetime.strptime("2014:10:20-04:23:19", "%Y:%m:%d-%H:%M:%S")),
                },
                {
                "id": "j-jhtdWOZmsdfKB-p1rQObtaR1THCz5YP-hhudsfaUm4RMB0NzI7lsZR-ksFA79duWG9uTuqEB45qN8MPexEllGKqsgwdbN",
                "created": str(datetime.strptime("2014:10:22-01:20:32", "%Y:%m:%d-%H:%M:%S")),
                "status": "active",
                "completed": str(datetime.strptime("2014:10:22-05:23:19", "%Y:%m:%d-%H:%M:%S")),
                }],
            "archives": {}
        }
        return result


def update_job_glacier_archive(job_dict, glacier_archive):
    glacier_archive["jobs"].append(job_dict)
    return glacier_archive

def main():
    # Get regions
    regions = glacier.regions()

    # Create glacier instances
    glacier_layer1 = glacier.layer1.Layer1(aws_access_key, aws_secret_key, region_name=regions[2].name)

    glacier_layer2 = boto.glacier.layer2.Layer2(aws_access_key, aws_secret_key, region=regions[2])


    # Vault name
    vault = glacier_layer2.get_vault(args.vault_name)

    # SNS Topic
    sns_topic = args.sns_topic
    
    #print glacier_layer1.list_vaults()["VaultList"][0]

    #print check_job_id(glacier_layer2)

    #print glacier_connection.list_vaults()

    # glacier_archive = load_archive_data(cache_file)

    # job_dict = request_vault_inventory(vault=get_vault(glacier_layer2, vault_name),
    #                              sns_topic=sns_topic,
    #                              archive_json=glacier_archive)
    # if job_dict:
    #     glacier_archive = update_job_glacier_archive(job_dict, glacier_archive)
    # else:
    #     print("No job dict")

    # Set Job ID
    # job_id = args.job_id

    #print(glacier_archive)

    # if not job_id is None:
    #     print("Job to check: %s" % job_id)
    #     if check_job_id(glacier_layer1, vault_name, job_id=job_id):
    #         get_job(glacier_layer1, vault_name, job_id)
    # 
    # 
    # if args.check_jobs:
    #     check_job_id(glacier_layer1, vault_name, archive_json=glacier_archive)
    
    if args.list_inventory:
        request_vault_inventory(vault, sns_topic)

    if args.check_job:
        print("Checking jobs")
        print vault.list_jobs()
    #print json.dumps(check_job_id(glacier_instance, vault_name, job_id), indent=2)

    #print vault.get_job("rnTR1mM1ChN8MPexEllGKqsiRfVJkfjE5vLqVzwcuRha2YbZ4afXDDt9d4N8MPexEllGKqsEMYO7AzMEpQ")

    #print vault.upload_archive(file)

    # save_archive_data(glacier_archive, cache_file)

    #print vault.retrieve_inventory(sns_topic=snsTopic)
    #vault = glacier_connection.create_vault("")

    #print vault

if __name__ == "__main__":
    main()
