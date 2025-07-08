#!/usr/bin/env python
"""
This module allows you to parse ULog files, which are used within the PX4
autopilot middleware.

The file format is documented on https://docs.px4.io/main/en/dev_log/ulog_file_format.html

"""

from setuptools import setup

DOCLINES = __doc__.split("\n")

# pylint: disable=invalid-name

setup(
    long_description="\n".join(DOCLINES),
    long_description_content_type='text/x-rst',
    platforms=["Windows", "Linux", "Solaris", "Mac OS-X", "Unix"],
    include_package_data=True,
)
