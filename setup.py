from setuptools import find_packages, setup

NAME = 'lightning'
VERSION = '1.0.0'

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
    name=NAME,
    version=VERSION,
    url='https://github.com/git-men/lightning',
    author='gitmen.com',
    author_email='jeff@gitmen.com',
    description='A Django based no-code Admin and rapid development framework',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    packages=[
        'api_basebone',
        'bsm_config',
        'lightning',
        'shield',
        'storage'
    ],
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
