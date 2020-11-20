from dict2xml import dict2xml
from typing import List, Dict, Optional
from datetime import datetime

def bucket_object(obj: Dict) -> Dict:
    return {
        "ETag": "eTag",
        "Key": obj.get("key"),
        "LastModified": str(datetime.now()),
        "Owner": {
            "DisplayName": obj.get("display_name"),
            "ID": obj.get("id")
        },
        "Size": obj.get("size"),
        "StorageClass": "standard",
    }

def bucket_metadata(bucket: Dict) -> Dict:
    print("BucketMetadata:", bucket)
    return {
        "Name": bucket.get("name"),
        "CreationDate": bucket.get("creation_date"),
    }

def bucket_owner(owner: Dict) -> Dict:
    return {
        "DisplayName": owner.get("display_name"),
        "ID": owner.get("id"),
    }

# https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListBuckets.html
# listBuckets
def list_buckets(buckets: List, owner: Dict, config: Optional[Dict] = {}) -> str:
    list_buckets_response = {
        "ListAllMyBucketsResult": {
            "Buckets": [bucket_metadata(bucket) for bucket in buckets],
            "Owner": bucket_owner(owner),
        }
    }
    return dict2xml(list_buckets_response)

# https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectsV2.html
# ListObjectsV2 Response
def list_bucket_objects(
    bucket: str,
    objects: List,
    config: Optional[Dict] = {}) -> str:
    list_bucket_v2_response = {
        "ListBucketResult": {
            '@': { "xmlns": 'http://doc.s3.amazonaws.com/2006-03-01/' },
            "IsTruncated": False,
            "KeyCount": len(objects),
            "MaxKeys": len(objects),
            "Name": bucket,
            "Prefix": config.get("prefix") or "",
            "Delimiter": config.get("delimiter") or "",
            "MaxKeys": config.get("max-keys") or 1000,
            # TODO: Support delimiter query parameter
            # "CommonPrefixes": [
            #     {"Prefix": "CommonPrefix"},
            # ],
            "EncodingType": "UTF-8",
            "KeyCount": len(objects),
            "ContinuationToken": config.get("continuation-token") or "",
            "NextContinuationToken": "nextContinuationToken",
            "StartAfter": config.get("start-after") or "",
        }
    }
    if len(objects) > 0:
        contents = [bucket_object(o) for o in objects]
        list_bucket_v2_response['ListBucketResult']['Contents'] = contents
    return dict2xml(list_bucket_v2_response)