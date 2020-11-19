import dict2xml
from typing import List, Dict, Optional
from datetime import datetime

def _bucket_object(obj: Dict) -> Dict:
    return {
        "ETag": "e-tag",
        "Key": obj.get("key"),
        "LastModified": str(datetime.now()),
        "Owner": {
            "DisplayName": obj.get("display_name"),
            "ID": obj.get("id"),
            "Size": obj.get("size"),
            "StorageClass": "standard",
        }
    }

def get_bucket(
    bucket: str,
    objects: List,
    config: Optional[Dict] = {}) -> str:
    {
        "ListBucketResult": {
            '@': { "xmlns": 'http://doc.s3.amazonaws.com/2006-03-01/' },
            "IsTruncated": True,
            "Contents": [_bucket_object(obj) for obj in objects],
            "Name": bucket,
            "Prefix": config.get("prefix") or "/",
            "Delimiter": config.get("delimiter") or "",
            "MaxKeys": config.get("max-keys") or 1000,
            "CommonPrefixes": [
            {"Prefix": "CommonPrefix"},
            ],

            "EncodingType": "UTF-8",
            "KeyCount": len(objects),
            "ContinuationToken": config.get("continuation-token") or "",
            "NextContinuationToken": "nextContinuationToken",
            "StartAfter": config.get("start-after") or "",
        }
    }