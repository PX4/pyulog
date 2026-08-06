#!/usr/bin/env python
"""
This module allows you to parse ULog files, which are used within the PX4
autopilot middleware.

The file format is documented on https://docs.px4.io/main/en/dev_log/ulog_file_format.html

"""

from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py

DOCLINES = __doc__.split("\n")
LIBEVENTS_PARSE_PACKAGE = "libevents_parse"

# pylint: disable=invalid-name

class BuildPy(build_py):

    def copy_file(self, infile, outfile, *args, **kwargs):
        infile = Path(infile)
        resolved = infile.resolve()

        if infile.name == LIBEVENTS_PARSE_PACKAGE and resolved.is_dir():
            # Copy libevents_parse as setuptools does not allow to copy the symlink
            shutil.copytree(resolved, outfile, dirs_exist_ok=True)
            return str(outfile), True

        return super().copy_file(infile, outfile, *args, **kwargs)

setup(
    long_description="\n".join(DOCLINES),
    long_description_content_type='text/x-rst',
    platforms=["Windows", "Linux", "Solaris", "Mac OS-X", "Unix"],
    cmdclass={"build_py": BuildPy},
)
