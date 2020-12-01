from setuptools import find_packages, setup

NAME = 'lightning'
VERSION = '1.0.0'

def get_install_require_packages():
    """获取依赖的安装包"""
    with open('requirements.in', 'r') as file:
        return [line
            for line in file.readlines() if not line.startswith('http')]

with open('README.zh-CN.md', 'r') as file:
    long_description = file.read()


def get_packages(app):
    """获取包"""
    return [app] + [
        "{}.{}".format(app, item) for item in find_packages(app)
    ]

all_packages = []
[all_packages.extend(item) for item in map(get_packages, [
    'api_basebone',
    'bsm_config',
    'lightning',
    'shield',
    'storage',
    'puzzle'
])]

setup(
    name=NAME,
    version=VERSION,
    url='https://github.com/git-men/lightning',
    author='gitmen.com',
    author_email='jeff@gitmen.com',
    description='A Django based no-code Admin and rapid development framework',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    packages=all_packages,
    include_package_data=True,
    data_files={},
    install_requires=get_install_require_packages(),
    dependency_links = [
     "git+https://github.com/jeffkit/wechatpy/archive/v.18.13-work.zip",
    ],
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
