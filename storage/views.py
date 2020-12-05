import os
from pathlib import Path
from django.http import FileResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser

from api_basebone.core.exceptions import BusinessException
from api_basebone.drf.response import success_response
from bsm_config.settings import site_setting


def is_relative_to(path, dir_path):
    # 避免 path traversal 问题 https://owasp.org/www-community/attacks/Path_Traversal
    # Python 3.9 才有 Path.is_relative_to，
    # 而 Path.resolve 会 follow symbol link，
    # Path.absolute 又不能解析“../”，
    # 所以只能用 os.path.abspath 了
    return os.path.abspath(path).startswith(os.path.abspath(dir_path))


@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload(request):
    key, policy, file = request.data['key'], request.data['policy'], request.data['file']
    storage_path = site_setting['storage_path']
    if not storage_path:
        raise BusinessException('storage support not enabled')
    file_path = Path(storage_path).joinpath(key)
    if not is_relative_to(file_path, storage_path):
        raise BusinessException('invalid file key: %s' % key)
    dirname = file_path.parent
    if not dirname.exists():
        dirname.mkdir(parents=True)
    elif not dirname.is_dir():
        raise BusinessException('dir exists: %s' % os.path.dirname(key))
    elif file_path.exists():
        raise BusinessException('file already exists: %s' % key)
    with file_path.open('wb+') as f:
        for chunk in file.chunks():
            f.write(chunk)
    return success_response()


def file(request, key):
    storage_path = site_setting['storage_path']
    file_path = Path(storage_path).joinpath(key)
    if not is_relative_to(file_path, storage_path):
        raise BusinessException('invalid file key: %s' % key)
    if not file_path.is_file():
        raise BusinessException('file not exists: %s' % key)
    return FileResponse(file_path.open('rb'))
