import os, boto3
from botocore.config import Config

AWS_REGION = os.getenv("AWS_REGION", "sa-east-1")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

_cfg = Config(signature_version="s3v4", s3={"addressing_style": "virtual"})
_s3 = boto3.client("s3", region_name=AWS_REGION, config=_cfg)

def presign_put(key: str, content_type: str, expires: int = 900) -> str:
    # no firmamos ContentType para evitar desajustes del cliente
    return _s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": AWS_S3_BUCKET, "Key": key},
        ExpiresIn=expires,
    )

def presign_get(key: str, expires: int = 900, response_content_type: str | None = None) -> str:
    params = {"Bucket": AWS_S3_BUCKET, "Key": key}
    if response_content_type:
        params["ResponseContentType"] = response_content_type
    return _s3.generate_presigned_url("get_object", Params=params, ExpiresIn=expires)
