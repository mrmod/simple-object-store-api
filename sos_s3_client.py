import boto3
import os
import sys
from pprint import pprint
session = boto3.session.Session()

# aws_access_key_id = os.env.get("AWS_ACCESS_KEY_ID")
# aws_secret_access_key = os.env.get("AWS_SECRET_ACCESS_KEY")
s3_client = session.client(
    service_name='s3',
    # aws_access_key_id=aws_access_key_id,
    # aws_secret_access_key=aws_secret_access_key,
    endpoint_url='http://localhost:5000',
    use_ssl=False,
)

# print(s3_client.list_buckets())

print("Using S3 Resource")
s3 = boto3.resource("s3", endpoint_url="http://localhost:8000")

def list_buckets(*args):
    for bucket in s3.buckets.all():
        print(bucket)

def create_bucket(*args):
    bucket = args[0]
    print(f"Bucket={bucket}")
    s3.create_bucket(Bucket=bucket)

def list_objects(*args):
    bucket = s3.Bucket(args[0])
    print(f"Bucket={bucket} Object listing")
    for obj in bucket.objects.all():
        print(obj)

def get_object(*args):
    bucket = args[0]
    key = args[1]
    obj = s3.Object(bucket, key)
    print(f"Object.get: bucket: {bucket} key: {key}")
    r = obj.get()
    pprint(r)

    # with client
    # c = boto3.client('s3')
    print(f"get_object: Bucket={bucket} Key={key}")
    r = s3_client.get_object(Bucket=bucket, Key=key)
    pprint(r)

TEST_OUTFILE = '/tmp/s3_download_fileobj'
def download_fileobj(*args):
    bucket = args[0]
    key = args[1]
    print(f"download_fileobj: Bucket={bucket} Key={key}")
    with open(TEST_OUTFILE, 'wb+') as outfile:
        s3_client.download_fileobj(bucket, key, outfile)
    
    with open(TEST_OUTFILE, 'r') as infile:
        assert infile.read() == "object data"
        print("OK")

    os.unlink(TEST_OUTFILE)
    print(f"download_file: Bucket={bucket} Key={key}")
    s3.meta.client.download_file(bucket, key, TEST_OUTFILE)
    with open(TEST_OUTFILE, 'r') as infile:
        assert infile.read() == "object data"
        print("OK")

def put_object(*args):
    bucket = args[0]
    key = args[1]
    content = args[2]
    print(f"put_object: Bucket={bucket} Key={key} as Bytestream")
    with open(content, 'rb') as infile:
        s3_client.put_object(Bucket=bucket, Key=key, Body=infile.read())
    
    print(f"put_object: Bucket={bucket} Key={key} as Bucket resource")
    with open(content, 'rb') as infile:
        b = s3.Bucket(bucket)
        b.put_object(Key=key, Body=infile.read())

cmd = sys.argv[1]
args = sys.argv[2:]
print(f"Executing {cmd} with args {args}")
locals()[cmd](*args)
