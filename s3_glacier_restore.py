#!/usr/bin/python3

import argparse
import boto3
import logging

s3 = boto3.resource('s3')
bucket = s3.Bucket('glacier-bucket')
for obj_sum in bucket.objects.all():
    obj = s3.Object(obj_sum.bucket_name, obj_sum.key)
    if obj.storage_class == 'GLACIER':
        # Try to restore the object if the storage class is glacier and
        # the object does not have a completed or ongoing restoration
        # request.
        if obj.restore is None:
            print('Submitting restoration request: %s' % obj.key)
            obj.restore_object(RestoreRequest={'Days': 1})
        # Print out objects whose restoration is on-going
        elif 'ongoing-request="true"' in obj.restore:
            print('Restoration in-progress: %s' % obj.key)
        # Print out objects whose restoration is complete
        elif 'ongoing-request="false"' in obj.restore:
            print('Restoration complete: %s' % obj.key)

if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(description="S3 Glacier restore tool", usage='%(prog)s [options]')
    # Authentication Arguments
    parser.add_argument("--access-id", "-a", action="store", help="AWS Access Key [optional]")
    parser.add_argument("--secret-key", "-s", action="store", help="AWS Secret Key [optional]")
    # Retention arguments
    parser.add_argument("--file", action="store", help="File list [optional]")
    parser.add_argument("--bucket", action="store", required=True, help="Bucket name [required]")
    parser.add_argument("--log", help="Logging level - DEBUG|INFO|WARNING|ERROR|CRITICAL [optional]")
    arguments = parser.parse_args()

    # Setup logging
    log_level = LOG_LEVEL

    # logging.debug("Log level: %s", LOG_LEVEL)
    if arguments.log is not None:
        log_level = arguments.log.upper()

    logging.basicConfig(format='%(levelname)s:%(message)s', level=getattr(logging, log_level))
