# Error Codes:
# https://docs.aws.amazon.com/AmazonS3/latest/API/ErrorResponses.html#ErrorCodeList

import re
from dict2xml import dict2xml

from fastapi import APIRouter, Header, Response, File
from typing import Optional, Dict
import model
import serializer
api = APIRouter()

XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>\n'

def simple_aws_account_id(authz_header: Header):
    try:
        (credential, signed_headers, signature) = authz_header.split(",")
        print(f"Authz:\n\tCredential: {credential}\n\tSigned: {signed_headers}\n\tSignature: {signature}")

        (algo_spec, cred_var) = credential.split(" ")

        (_, cred_val) = cred_var.split("=")
        return cred_val[0:7]
    except AttributeError:
        print(f"Unable to split header {authz_header}")
        return DEFAULT_BUCKET_OWNER

DEFAULT_BUCKET_OWNER = "default-bucket-owner"
BUCKET_NAME_EXP = r'^[a-z0-9]+(.?[-a-z0-9]+)*$'
BUCKET_NAME_RANGE = (3, 63)
@api.put("/{bucket}")
async def create_bucket(
    bucket: str,
    res: Response,
    authorization: Optional[str] = Header(None),
    x_amz_acl: Optional[str] = Header(None),
    x_amz_grant_full_control: Optional[str] = Header(None),
    x_amz_grant_read: Optional[str] = Header(None),
    x_amz_grant_read_acp: Optional[str] = Header(None),
    x_amz_grant_write: Optional[str] = Header(None),
    x_amz_grant_write_acp: Optional[str] = Header(None),
    x_amz_bucket_object_lock_enabled: Optional[str] = Header(None)):
    # if authorization is None:
    #     res.status_code = 403
    #     return
    # if not is_authorized:
    #     res.status_code = 401
    #     return
    print(f"CreateBucket request: Bucket={bucket}")
    if re.match(BUCKET_NAME_EXP, bucket) is None:
        res.status_code = 400
        res.headers['Content-Type'] = 'application/xml'
        print(f"Bucket doesn't match regex")
        return dict2xml({
            "Error": {
                "Code": "InvalidBucketName",
                "Message": f"The bucket name {bucket} must match {BUCKET_NAME_EXP}",
                "Resource": f"/{bucket}",
                "RequestId": "SomeRequestID", # TODO: Support Reqest ID
            }
        })
    if len(bucket) < BUCKET_NAME_RANGE[0] or len(bucket) > BUCKET_NAME_RANGE[1]:
        res.status_code = 400
        res.headers['Content-Type'] = 'application/xml'
        print(f"Bucket length outside range: {BUCKET_NAME_RANGE[0]} and {BUCKET_NAME_RANGE[1]}")
        return dict2xml({
            "Error": {
                "Code": "InvalidBucketName",
                "Message": f"The bucket name {bucket} must be between {BUCKET_NAME_RANGE[0]} and {BUCKET_NAME_RANGE[1]} characters long",
                "Resource": f"/{bucket}",
                "RequestID": "SomeRequestID",
            }
        })
    account_id = simple_aws_account_id(authorization)
    try:
        result = model.create_bucket(bucket, account_id)
        # result == 1 ? new : existed
        return Response(headers={"Location": f"/{bucket}"})
    except Exception as e:
        print(f"Error creating response: ", e)
        res.headers['Content-Type'] = 'application/xml'
        res.status_code = 503
        return dict2xml({
            "Error": {
                "Code": "InternalError",
                "Message": "Unexpected server error while creating bucket",
            }
        })

def _staple_owner(object_id: str, account_id: str) -> Dict:
    return {
        "display_name": account_id,
        "id": account_id,
        "size": 1000,
        "key": object_id,
    }

@api.get("/{bucket}")
async def get_bucket(bucket: str,
    res: Response,
    authorization: Optional[str] = Header(None),
):
    print(f"Get bucket {bucket}")
    account_id = simple_aws_account_id(authorization)
    try:
        if model.can_read_bucket(bucket, account_id):
            return serializer.get_bucket(
                [_staple_owner(obj, account_id) for obj in model.get_bucket(bucket, account_id)]
            )
        else:
            res.status_code = 403
            return dict2xml({
                "Error": {
                    "Code": "AccessDenied",
                    "Message": f"Access to s3://{bucket} denied"
                }
            })
    except Exception:
        res.status_code = 503
        return dict2xml({
            "Error": {
                "Code": "InternalError",
                "Message": f"Unexpected server error while getting bucket {bucket}"
            }
        })

# @api.put("/{bucket}/{key}")
async def put_object(bucket: str, key: str, bytestream: bytes = File(...),
    authorization: Optional[str] = Header(None),
    x_amz_acl: Optional[str] = Header(None),
    cache_control: Optional[str] = Header(None),
    content_disposition: Optional[str] = Header(None),
    content_encoding: Optional[str] = Header(None),
    content_language: Optional[str] = Header(None),
    content_length: Optional[str] = Header(None),
    content_md5: Optional[str] = Header(None),
    content_type: Optional[str] = Header(None),
    expires: Optional[str] = Header(None),
    x_amz_grant_full_control: Optional[str] = Header(None),
    x_amz_grant_read: Optional[str] = Header(None),
    x_amz_grant_read_acp: Optional[str] = Header(None),
    x_amz_grant_write_acp: Optional[str] = Header(None),
    x_amz_server_side_encryption: Optional[str] = Header(None),
    x_amz_storage_class: Optional[str] = Header(None),
    x_amz_website_redirect_location: Optional[str] = Header(None),
    x_amz_server_side_encryption_customer_algorithm: Optional[str] = Header(None),
    x_amz_server_side_encryption_customer_key: Optional[str] = Header(None),
    x_amz_server_side_encryption_customer_key_MD5: Optional[str] = Header(None),
    x_amz_server_side_encryption_aws_kms_key_id: Optional[str] = Header(None),
    x_amz_server_side_encryption_context: Optional[str] = Header(None),
    x_amz_request_payer: Optional[str] = Header(None),
    x_amz_tagging: Optional[str] = Header(None),
    x_amz_object_lock_mode: Optional[str] = Header(None),
    x_amz_object_lock_retain_until_date: Optional[str] = Header(None),
    x_amz_object_lock_legal_hold: Optional[str] = Header(None),
    x_amz_expected_bucket_owner: Optional[str] = Header(None)):
        # No headers are used 😎

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(SOS_DATAPUTTER_ROUTER)
            s.send(len(bytestream).to_bytes(CONTENT_LENGTH_HEADER_SIZE, 'big'))
            s.send(bytestream)

            object_id = s.recv(OBJECT_ID_SIZE)
        if object_id is None:
            return "Error:"
