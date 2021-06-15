import datetime

from minio import Minio
from minio.datatypes import PostPolicy

from api_basebone.utils.uuid import uuid4_hex
from bsm_config.settings import site_setting


# @lru_cache()
def get_s3_client():
    return Minio(
        '{}:{}'.format(site_setting['S3_ENDPOINT'], site_setting['S3_PORT']),
        site_setting['S3_ACCESS_KEY'],
        site_setting['S3_SECRET_KEY'],
        secure=site_setting['S3_USE_SSL'],
    )


def upload_file(*args, **kwargs):
    """
    使用方式：upload_file('存储路径', '本地文件路径')
    """
    client = get_s3_client()
    client.fput_object(
        site_setting['S3_BUCKET'],
        *args,
        **kwargs,
    )


def s3_presign_url(filename):
    client = get_s3_client()
    return client.presigned_put_object(site_setting['S3_BUCKET'], filename)


def s3_endpoint():
    return '{}://{}:{}/{}/'.format(
        'https' if site_setting['S3_USE_SSL'] else 'http',
        site_setting['S3_ENDPOINT'],
        site_setting['S3_PORT'],
        site_setting['S3_BUCKET'],
    )


def get_token():
    # 现在每次上传之前都先更新一遍token，30秒足矣
    ttl = datetime.timedelta(seconds=30)
    policy = PostPolicy(site_setting['S3_BUCKET'], datetime.datetime.utcnow() + ttl)
    # policy.add_equals_condition('acl', 'public-read')
    uuid = uuid4_hex()
    # 服务端限定前缀增加安全性，至少能防止内容被篡改。
    # 只要使用相同的key再上传一遍，就能覆盖原内容，达到篡改效果。
    directory = f'media-${uuid}/'
    policy.add_starts_with_condition('key', directory)
    form_data = get_s3_client().presigned_post_policy(policy)
    return {
        'host': s3_endpoint(),
        'dir': directory,
        **form_data,
    }
