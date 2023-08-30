import os
from setuptools import find_packages, setup

NAME = 'django-lightning'

os.chdir(os.path.dirname(os.path.abspath(__file__)))
VERSION = '1.2.0'

import ssl

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

setup(
    name=NAME,
    version=VERSION,
    url='https://github.com/git-men/lightning',
    author='gitmen.com',
    author_email='jeff@gitmen.com',
    description='A Django based no-code Admin and rapid development framework',
    long_description='A Django based no-code Admin and rapid development framework',
    # long_description_content_type='text/markdown',
    license='MIT',
    packages=find_packages(exclude=['lightning_code', 'lightning_code.*']),
    include_package_data=True,
    data_files={},
    install_requires=[
        'arrow>=0.12.1,<=0.15.8',
        'django>=2.2,<3',
        'django-cors-headers>=2.4.0,<=3.2.1',
        'django-extensions==2.1.3',
        'django-environ==0.4.5',
        'djangorestframework==3.9.4',
        'django-rest-swagger==2.2.0',
        'jsonfield==3.1.0',
        'raven==6.9.0',
        'Werkzeug==0.15.0',
        'pydash==4.7.4',
        'django-guardian==2.3.0',
        'django-redis',
        'django-mptt',
    ],
    extras_require={
        'celery': [
            'celery==5.1.0',
            'django-celery-beat @ https://github.com/jeffkit/django-celery-beat/archive/refs/heads/master.zip',
        ],
        'mysql': [
            'mysqlclient>=1.4.3,<2',
        ],
        'postgresql': [
            'psycopg2-binary',
        ],
        'development': [
            'factory-boy==2.11.1',
            'oss2>=2.6.0,<=2.12.1',
            'qcloud-python-sts==3.0.3',
            'wechatpy @ https://github.com/jeffkit/wechatpy/archive/v.18.13-work.zip',
        ],
        'excel': [
            'openpyxl>=2.5.12,<3.1',
            'pillow',  # openpyxl用到pillow
        ],
    },
    py_modules=['lightning_flags'],
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
