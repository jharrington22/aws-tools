aws-tools
=========

Collection of AWS scripts written in python making use of boto.

All scripts require boto to be installed:

Install boto - https://pypi.python.org/pypi/boto#downloads

#### ec2_snapshot.py

A tool which allows quick and easy snapshots from the command line while having the capability to manage retention.

When specifying either instance name (-n) or instance ID (-i) ec2_snapshot.py will automatically snapshot all volumes attached to the associated instance.

eg. Create a snapshot of an instance named "ProductionInstance"

```
python ec2_snapshot.py -a ${AWS_ACCESS_KEY} -s ${AWS_SECRET_KEY} -r ap-southeast-2 -c -n ProductionInstance
```

In conjunction with cron you can use this script to setup hourly, daily, weekly or monthly snapshots. 

eg. Create a snapshot of an instance named "ProductionInstance" and keep 7 days retention

```
python ec2_snapshot.py -a ${AWS_ACCESS_KEY} -s ${AWS_SECRET_KEY} -r ap-southeast-2 -c -n ProductionInstance --daily 7
```

# Usage

```
usage: ec2_snapshot.py [options]

EC2 snapshot tool

optional arguments:
  -h, --help            show this help message and exit
  --access-id ACCESS_ID, -a ACCESS_ID
                        AWS Access Key [optional]
  --secret-key SECRET_KEY, -s SECRET_KEY
                        AWS Secret Key [optional]
  --hours HOURS         Hourly retention [optional]
  --days DAYS, -d DAYS  Daily retention [optional]
  --weeks WEEKS, -w WEEKS
                        Weekly retention [optional]
  --months MONTHS, -m MONTHS
                        Monthly retention [optional]
  --volume-id VOLUME_ID, -i VOLUME_ID
                        Volume ID [optional]
  --instance-id INSTANCE_ID
                        EC2 Instance ID [optional]
  --instance-name INSTANCE_NAME, -n INSTANCE_NAME
                        EC2 Instance Name [optional]
  --region REGION, -r REGION
                        AWS Region [optional]
  --snapshot-create, -c
                        Create a snapshot [optional]
  --snapshot-name SNAPSHOT_NAME
                        Specify a custom name for your snapshot [optional]
  --snapshot-delete SNAPSHOT_DELETE
                        Delete snapshot [optional]
  --snapshot-info       Output information on snapshot ID [optional]
  --list-instances, -l  List all instances with associated account [optional]
  --verbose, -v         More verbose output [optional]
  --progress, -p        Output a progress bar when taking snapshot [optional]
```


*When specifying either instance name (-n) or instance ID (-i) ec2_snapshot.py will snapshot all volumes attached to the associated instance. 

##### Credentials 

There are 3 ways you can provide credentails to ec2_snapshot.py

1. On the command line using -a for the access key and -s for the access secret
2. In the aws-tools configuration f ile ~/.aws_tools.cfg (See example in repository). The location of this config file can be changed by modifying the config_file variable in ec2_snapshot.py
3. Because ec2_snapshot.py uses boto in ~/.boto as per Boto documentation

#### s3_sync.py

An attempt to make a simple sync script for syncing local files/directories to s3 using boto.