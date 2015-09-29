import boto.ec2
import argparse
import time


def get_str_date(ami_name):
    name, date_id = ami_name.split()
    return time.strftime('%m/%d/%Y %H:%M:%S',  time.gmtime(float(date_id)))


def main(aws_access_key, aws_secret_key, region, pattern, retention):
    conn = boto.ec2.connect_to_region(region, aws_access_key_id=aws_access_key,
                                      aws_secret_access_key=aws_secret_key)
    images = conn.get_all_images(filters={"name": pattern})
    sorted_images = sorted([(image.name, image.id) for image in images], key=lambda image: image[0])
    delete = sorted_images[:-retention]
    for image in delete:
        print("Deleting: %s %s" % (get_str_date(image[0]), image[1]))
        #conn.deregister_image(image[1])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EC2 AMI tool",
                                     usage='%(prog)s [options]')
    parser.add_argument('--name', '-n', type=str,
                        help='AMI Name can contain wildcard character')
    parser.add_argument("--region", "-r", action="store", help="AWS region")
    parser.add_argument("--secret_key", "-s", action="store", help="AWS secret access key")
    parser.add_argument("--access_key", "-u", action="store", help="AWS access key")
    parser.add_argument("--retention", "-k", type=int, help="Number of AMIs to keep")
    args = parser.parse_args()

    main(args.access_key, args.secret_key, args.region, args.name, args.retention)
