import json
import os
from setuptools import setup, find_packages

BASEDIR = os.path.dirname(os.path.abspath(__file__))
VERSION = json.load(open(os.path.join(BASEDIR, 'package.json'))).get("version")

# Dependencies (format is 'PYPI_PACKAGE_NAME[>=]=VERSION_NUMBER')
BASE_DEPENDENCIES = [
    'python-dotenv>=0.10.3',
    'wildflower-honeycomb-sdk>=0.7.3',
    'boto3>=1.10.0',
    'psycopg2>=2.8.4',
    'psutil>=5.6.7',
    'wf-process-cuwb-data>=0.2.0',
    'numpy>=1.18.1'
]

BASE_DEPENDENCY_LINKS = []
# BASE_DEPENDENCY_LINKS = [
#     'git+https://github.com/WildflowerSchools/wf-geom-render.git@master#egg=geom-render'
# ]

# TEST_DEPENDENCIES = [
# ]
#
# LOCAL_DEPENDENCIES = [
# ]

# Allow setup.py to be run from any path
os.chdir(os.path.normpath(BASEDIR))

setup(
    name='honeycomb-geom-rendering',
    packages=find_packages(),
    version=VERSION,
    include_package_data=True,
    description='A generator for producing and storing honeycomb video geoms',
    long_description=open('honeycomb_tools/README.md').read(),
    url='https://github.com/WildflowerSchools/honeycomb-geom-rendering',
    author='Benjamin Jaffe-Taberg',
    author_email='ben.talberg@wildflowerschools.org',
    install_requires=BASE_DEPENDENCIES,
    dependency_links=BASE_DEPENDENCY_LINKS,
    # tests_require=TEST_DEPENDENCIES,
    # extras_require = {
    #     'test': TEST_DEPENDENCIES,
    #     'local': LOCAL_DEPENDENCIES
    # },
    keywords=['honeycomb, wildflower, websocket, timescaledb'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ]
)
