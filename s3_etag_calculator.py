import os
import binascii
import hashlib
import argparse

if __name__ == "__main__":
    # Argument parser
    parser = argparse.ArgumentParser(description="S3 tool to calculate ETag checksums", usage='%(prog)s [options]')
    # Authentication Arguments
    parser.add_argument("--access-id", "-a", action="store", help="AWS Access Key [optional]")
    parser.add_argument("--secret-key", "-s", action="store", help="AWS Secret Key [optional]")
    parser.add_argument("--source-file", "-f", action="store", help="Local source file")
    parser.add_argument("--dest-file", "-d", action="store", help="Local source file")
    arguments = parser.parse_args()

    checksums = []

    UPLOAD_MAX_SIZE = 8 * 1024 * 1024
    UPLOAD_MAX_PART_SIZE = 8 * 1024 * 1024
    print(UPLOAD_MAX_PART_SIZE)
    print(type(UPLOAD_MAX_PART_SIZE))

    SOURCE_FILE = arguments.source_file
    SOURCE_FILE_SIZE = os.path.getsize(SOURCE_FILE)
    
    if SOURCE_FILE > UPLOAD_MAX_SIZE:

        block_count = 0
        md5string = ""

        with open(SOURCE_FILE, 'rb') as fp:
            for block in iter(lambda: fp.read(UPLOAD_MAX_PART_SIZE), ""):
                    hash = hashlib.md5()
                    hash.update(block)
                    md5string = md5string + binascii.unhexlify(hash.hexdigest())
                    block_count += 1
            hash = hashlib.md5()
            hash.update(md5string)
            print("{}-{}".format(hash.hexdigest(), str(block_count)))
    else:
        with open(SOURCE_FILE, rb) as fp:
            for block in iter(lambda: fp.read(UPLOAD_MAX_PART_SIZE), ""):
                hash.update(block)
            print(hash.hexdigest())

