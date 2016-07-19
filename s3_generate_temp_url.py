import boto
import time
import argparse


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='AWS S3 generate temporary URL for S3 Object')

    parser.add_argument('-f', '--file-name', action="store", help="S3 file (Object) name")
    parser.add_argument('-e', '--expiry', action="store", help="Expiry time of URL in seconds")
    parser.add_argument('-b', '--bucket', action="store", help="S3 Bucket name")

    args = parser.parse_args()

    expire_timeout = int(args.expiry)

    key_name = args.file_name

    conn = boto.connect_s3()

    bucket = conn.get_bucket(args.bucket)

    key = bucket.get_key(key_name)

    expiry_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + expire_timeout))

    temp_url = key.generate_url(expire_timeout)

    print("Your file: {} is ready to download it will expire on {}\nLink: {}\n".format(key_name, expiry_date, temp_url))
