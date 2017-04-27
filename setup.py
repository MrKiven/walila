# -*- coding: utf-8 -*-

import os
import re

from setuptools import setup, find_packages


def get_version():
    v_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               'lib', '__init__.py')
    ver_info_str = re.compile(r".*version_info = \((.*?)\)", re.S). \
        match(open(v_file_path).read()).group(1)
    return re.sub(r'(\'|"|\s+)', '', ver_info_str).replace(',', '.')


test_require = []
with open('dev_requirements.txt') as require_fd:
    for req in require_fd:
        test_require.append(req)

require = []
with open('requirements.txt') as require_fd:
    for req in require_fd:
        require.append(req)

setup(
    name='walila',
    version=get_version(),
    description="Dobechina lib",
    author='Kiven',
    author_email='shenjialong@dobechina.com',
    packages=find_packages(),
    tests_require=test_require,
    install_requires=require
)
