import boto3
from botocore.client import Config
import time
import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='AWS S3 generate temporary URL for S3 Object')

    parser.add_argument('-f', '--file-name', action="store", help="S3 file (Object) name")
    parser.add_argument('-e', '--expiry', action="store", help="Expiry time of URL in seconds")
    parser.add_argument('-b', '--bucket', action="store", help="S3 Bucket name")
    parser.add_argument('-s', '--signature-version', action="store", help="S3 signature version eg, -s v4")
    args = parser.parse_args()

    expire_timeout = int(args.expiry)
    # Get the service client.
    if args.signature_version == "v4":
        conn = boto3.client('s3', config=Config(signature_version='s3v4'))
    else:
        conn = boto3.client('s3')
    # Generate the URL to get 'file-name' from 'bucket-name'
    params = {
        'Bucket': args.bucket,
        'Key': args.file_name
    }
    url = conn.generate_presigned_url(
                                        ClientMethod='get_object',
                                        Params=params,
                                        ExpiresIn=expire_timeout
    )
    expiry_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + expire_timeout))
    print("Your file: {} is ready to download it will expire on {}\nLink: {}\n".format(args.file_name,
                                                                                       expiry_date,
                                                                                       url))
