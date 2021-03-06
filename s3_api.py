# Error Codes:
# https://docs.aws.amazon.com/AmazonS3/latest/API/ErrorResponses.html#ErrorCodeList

import re
import traceback
from dict2xml import dict2xml

from fastapi import APIRouter, Header, Response, File, Request, Depends
from fastapi import HTTPException
from typing import Optional, Dict
import model
import serializer
import socket
import os
import object_store as store

api = APIRouter()

XML_PRAGMA = '<?xml version="1.0" encoding="UTF-8"?>\n'
XML_HEADERS = {"Content-Type": "application/xml"}


class S3ApiException(Exception):
    def __init__(self, body: str, status_code: int):
        self.body = body
        self.status_code = status_code


def is_authorizable(authorization: Optional[str] = Header(None)):
    if authorization is None:
        raise S3ApiException(
            dict2xml(
                {
                    "Error": {
                        "Code": "AccessDenied",
                        "Message": f"Access to resource denied",
                    }
                }
            ),
            status_code=403,
        )


# Provides first 7 chars of AWS_API_KEY as account ID
def simple_aws_account_id(authz_header: Header):
    try:
        (credential, signed_headers, signature) = authz_header.split(",")
        print(
            f"Authz:\n\tCredential: {credential}\n\tSigned: {signed_headers}\n\tSignature: {signature}"
        )

        (algo_spec, cred_var) = credential.split(" ")

        (_, cred_val) = cred_var.split("=")
        return cred_val[0:7]
    except AttributeError:
        print(f"Unable to split header {authz_header}")
        return DEFAULT_BUCKET_OWNER


DEFAULT_BUCKET_OWNER = "default-bucket-owner"
BUCKET_NAME_EXP = r"^[a-z0-9]+(.?[-a-z0-9]+)*$"
BUCKET_NAME_RANGE = (3, 63)


@api.get("/", dependencies=[Depends(is_authorizable)])
async def list_buckets(authorization: Optional[str] = Header(None)):
    account_id = simple_aws_account_id(authorization)
    buckets = model.list_buckets(account_id)
    owner = model.get_bucket_owner(account_id)
    return Response(serializer.list_buckets(buckets, owner), headers=XML_HEADERS,)


# https://docs.aws.amazon.com/AmazonS3/latest/API/API_CreateBucket.html
# CreateBucket:
# aws s3 mb s3://$BUCKET
@api.put("/{bucket}", dependencies=[Depends(is_authorizable)])
async def create_bucket(
    bucket: str,
    authorization: Optional[str] = Header(None),
    x_amz_acl: Optional[str] = Header(None),
    x_amz_grant_full_control: Optional[str] = Header(None),
    x_amz_grant_read: Optional[str] = Header(None),
    x_amz_grant_read_acp: Optional[str] = Header(None),
    x_amz_grant_write: Optional[str] = Header(None),
    x_amz_grant_write_acp: Optional[str] = Header(None),
    x_amz_bucket_object_lock_enabled: Optional[str] = Header(None),
):

    if re.match(BUCKET_NAME_EXP, bucket) is None:
        raise S3ApiException(
            dict2xml(
                {
                    "Error": {
                        "Code": "InvalidBucketName",
                        "Message": f"The bucket name {bucket} must match {BUCKET_NAME_EXP}",
                        "Resource": f"/{bucket}",
                        "RequestId": "SomeRequestID",  # TODO: Support Reqest ID
                    }
                }
            ),
            400,
        )
    if len(bucket) < BUCKET_NAME_RANGE[0] or len(bucket) > BUCKET_NAME_RANGE[1]:
        raise S3ApiException(
            dict2xml(
                {
                    "Error": {
                        "Code": "InvalidBucketName",
                        "Message": f"The bucket name {bucket} must be between {BUCKET_NAME_RANGE[0]} and {BUCKET_NAME_RANGE[1]} characters long",
                        "Resource": f"/{bucket}",
                        "RequestID": "SomeRequestID",
                    }
                }
            ),
            400,
        )
    account_id = simple_aws_account_id(authorization)
    try:
        result = model.create_bucket(bucket, account_id)
        model.set_bucket_creation_date(bucket, account_id)
        # result == 1 ? new : existed
        return Response(headers={"Location": f"/{bucket}"})
    except Exception as e:
        raise S3ApiException(
            dict2xml(
                {
                    "Error": {
                        "Code": "InternalError",
                        "Message": "Unexpected server error while creating bucket",
                    }
                }
            ),
            503,
        )


# https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListObjectsV2.html
# ListBucketV2: List objects in a bucket
# aws s3 ls s3://$BUCKET
@api.get("/{bucket}", dependencies=[Depends(is_authorizable)])
async def get_bucket(
    bucket: str,
    continuation_token: Optional[str] = None,
    delimiter: Optional[str] = None,
    encoding_type: Optional[str] = None,
    fetch_owner: Optional[str] = None,
    max_keys: Optional[str] = None,
    prefix: Optional[str] = None,
    start_after: Optional[str] = None,
    x_amz_expected_bucket_owner: Optional[str] = None,
    x_amz_request_payer: Optional[str] = None,
    authorization: Optional[str] = Header(None),
):
    account_id = simple_aws_account_id(authorization)
    config = {
        "list-type": 2,
        "continuation-token": continuation_token,
        "delimiter": delimiter,
        "encoding-type": encoding_type,
        "fetch-owner": fetch_owner,
        "max-keys": max_keys,
        "prefix": prefix,
        "start-after": start_after,
        "x-amz-expected-bucket-owner": x_amz_expected_bucket_owner,
        "x-amz-request-payer": x_amz_request_payer,
    }

    try:
        if model.is_existing_bucket(bucket, account_id) and model.can_read_bucket(
            bucket, account_id
        ):
            bucket_objects = model.get_bucket(bucket, account_id)
            body = serializer.list_bucket_objects(
                bucket, bucket_objects, config=config,
            )
            return Response(body, headers=XML_HEADERS)
        else:
            if model.is_existing_bucket(bucket, account_id):
                raise S3ApiException(
                    dict2xml(
                        {
                            "Error": {
                                "Code": "AccessDenied",
                                "Message": f"Access to s3://{bucket} denied",
                            }
                        }
                    ),
                    403,
                )
            return Response(
                serializer.list_bucket_objects(bucket, [], config=config),
                headers=XML_HEADERS,
            )
    except Exception as e:
        raise S3ApiException(
            dict2xml(
                {
                    "Error": {
                        "Code": "InternalError",
                        "Message": f"Unexpected server error while getting bucket {bucket}",
                    }
                }
            ),
            503,
        )


# https://docs.aws.amazon.com/AmazonS3/latest/API/API_DeleteObject.html
# DeleteObject
#
@api.delete("/{bucket}/{key}", dependencies=[Depends(is_authorizable)])
async def delete_object(
    bucket: str,
    key: str,
    req: Request,
    version_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    x_amz_mfa: Optional[str] = Header(None),
    x_amz_request_payer: Optional[str] = Header(None),
    x_amz_bypass_governance_retention: Optional[bool] = Header(None),
    x_amz_expected_bucket_owner: Optional[str] = Header(None),
):
    account_id = simple_aws_account_id(authorization)
    has_errors = False
    if model.is_bucket_owner(bucket, account_id):
        if model.is_existing_bucket(bucket, account_id) and model.is_existing_key(
            bucket, key, account_id
        ):
            for object_id in model.list_objects_of_key(bucket, key, account_id):
                # Send DataPutter "Delete ObjectId"
                response = await store.delete(object_id.decode("UTF-8"))
                print(f"Delete {bucket}/{key} yielded {response}")
                if response.decode("UTF-8") == object_id.decode("UTF-8"):
                    model.delete_key_object(
                        object_id.decode("UTF-8"), bucket, key, account_id,
                    )
                else:
                    has_errors = True
        else:
            if model.is_existing_bucket(bucket, account_id):
                raise S3ApiException(
                    dict2xml(
                        {
                            "Error": {
                                "Code": "NoSuchKey",
                                "Message": f"s3://{bucket}/{key} does not exist",
                            }
                        }
                    ),
                    404,
                )
            else:
                raise S3ApiException(
                    dict2xml(
                        {
                            "Error": {
                                "Code": "NoSuchBucket",
                                "Message": f"s3://{bucket} does not exist",
                            }
                        }
                    ),
                    404,
                )
        if not has_errors:
            model.delete_key(bucket, key, account_id)
            return Response(status_code=200)
        print(f"Error deleting object {object_id.decode('UTF-8')}")
        return Response(status_code=503)


@api.delete("/{bucket}", dependencies=[Depends(is_authorizable)])
async def delete_bucket(
    bucket: str,
    authorization: Optional[str] = Header(None),
    x_amz_expected_bucket_owner: Optional[str] = None,
):
    account_id = simple_aws_account_id(authorization)
    if model.is_existing_bucket(bucket, account_id):
        if model.is_bucket_owner(bucket, account_id) and model.is_bucket_empty(
            bucket, account_id
        ):
            print(f"Deleting bucket {bucket}")
            if model.delete_bucket(bucket, account_id):
                return Response(
                    headers={
                        "x-amz-id-2": "OpaqueString",
                        "x-amz-request-id": "OpaqueRequestId",
                    }
                )
            else:
                raise S3ApiException(
                    dict2xml(
                        {
                            "Error": {
                                "Code": "InternalError",
                                "Message": f"Failed to delete bucket {bucket}",
                            }
                        }
                    ),
                    503,
                )
        else:
            raise S3ApiException(
                dict2xml(
                    {"Error": {"Code": "AccessDenied", "Message": f"Access denied",}}
                ),
                403,
            )
    raise S3ApiException(
        dict2xml(
            {
                "Error": {
                    "Code": "NoSuchBucket",
                    "Message": f"Bucket {bucket} does not exist",
                }
            }
        ),
        404,
    )


# https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html
# PutObject
@api.put("/{bucket}/{key}", dependencies=[Depends(is_authorizable)])
async def put_object(
    bucket: str,
    key: str,
    req: Request,
    authorization: Optional[str] = Header(None),
    x_amz_acl: Optional[str] = Header(None),
    cache_control: Optional[str] = Header(None),
    content_disposition: Optional[str] = Header(None),
    content_encoding: Optional[str] = Header(None),
    content_language: Optional[str] = Header(None),
    content_length: Optional[int] = Header(None),
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
    x_amz_expected_bucket_owner: Optional[str] = Header(None),
):

    body = await req.body()
    # No headers are used 😎
    account_id = simple_aws_account_id(authorization)
    if model.is_bucket_owner(bucket, account_id):
        object_id = await store.put(body, content_length)

        if object_id is None:
            raise S3ApiException(
                dict2xml(
                    {
                        "Error": {
                            "Code": "InternalError",
                            "Message": f"Unable to create object ID for {bucket}/{key}",
                        }
                    }
                ),
                503,
            )
        else:
            model.add_key_to_bucket(bucket, key, account_id)
            model.set_key_size(bucket, key, content_length, account_id)
            model.add_object_to_key(bucket, key, object_id, account_id)
            return Response()
    else:
        raise S3ApiException(
            dict2xml(
                {
                    "Error": {
                        "Code": "AccessDenied",
                        "Message": f"Access denied for putObject to {bucket}/{key} by {account_id}",
                    }
                }
            ),
            403,
        )
