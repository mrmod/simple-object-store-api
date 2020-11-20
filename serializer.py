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

def get_bucket(
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
        list_bucket_v2_response['Contents'] = [bucket_object(o) for o in objects]
    return dict2xml(list_bucket_v2_response)