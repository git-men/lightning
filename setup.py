from setuptools import find_packages, setup

NAME = 'api_basebone'
VERSION = '1.0.0'


def get_packages():
    """获取包"""
    return [NAME] + [
        "{}.{}".format(NAME, item) for item in find_packages(NAME)
    ]


def get_install_require_packages():
    """获取依赖的安装包"""
    packages = []
    with open('requirements.in', 'r') as file:
        for line in file.readlines():
            packages.append(line.replace('==', '>='))
    return packages


with open('README.md', 'r') as file:
    long_description = file.read()


setup(
    name='baseman',
    version=VERSION,
    #url='https://github.com/git-men/sky',
    #author='Kycool',
    #author_email='kycoolcool@gmail.com',
    description='基于 Django, DRF 通用的接口解决方案',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='BSD',
    packages=get_packages(),
    include_package_data=True,
    install_requires=get_install_require_packages(),
    zip_safe=False,
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
