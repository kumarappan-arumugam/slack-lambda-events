#!/usr/bin/env python

import codecs
import os
import re

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

def get_requirements(req_file='requirements.txt'):
    with open(req_file) as fp:
        return [x.strip() for x in fp.read().split('\n') if not x.startswith('#')]

with codecs.open("README.md", encoding="utf-8") as fp:
    long_description = fp.read()

here = os.path.abspath(os.path.dirname(__file__))

# Read the version number from a source file.
# Why read it, and not import?
# see https://groups.google.com/d/topic/pypa-dev/0PkjVpcxTzQ/discussion
def find_version(*file_paths):
    # Open in Latin-1 so that we avoid encoding errors.
    # Use codecs.open for Python 2 compatibility
    with codecs.open(os.path.join(here, *file_paths), 'r', 'latin1') as f:
        version_file = f.read()

    # The version line must have the form
    # __version__ = 'ver'
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")

setup(
    name='slack-lambda-events',
    version=find_version('src', 'version.py'),
    author='Kumarappan Arumugam',
    author_email='kumarappan.ar@gmail.com',
    description='Python Slack Events API adapter for AWS Lambda',
    long_description=long_description,
    url='https://github.com/kumarappan-arumugam/slack-lambda-events',
    packages=find_packages(),
    package_dir={'slacklambdaevents': 'src'},
    install_requires=get_requirements(),
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development'
    ],
    keywords=['Slack', 'Lambda', 'ALB', 'Events'],
)
