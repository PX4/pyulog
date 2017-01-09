#!/usr/bin/env python
"""Python log crunching for PX4.

This module allows you to do control and statistical analysis for the PX4.

"""

from __future__ import print_function

MAJOR = 0
MINOR = 1
MICRO = 0
ISRELEASED = True
VERSION = '%d.%d.%d' % (MAJOR, MINOR, MICRO)

DOCLINES = __doc__.split("\n")

import os
import sys
import subprocess

from setuptools import setup, find_packages

CLASSIFIERS = """\
Development Status :: 1 - Planning
Intended Audience :: Science/Research
Intended Audience :: Developers
License :: OSI Approved :: BSD License
Programming Language :: Python
Programming Language :: Python :: 3
Programming Language :: Other
Topic :: Software Development
Topic :: Scientific/Engineering :: Artificial Intelligence
Topic :: Scientific/Engineering :: Mathematics
Topic :: Scientific/Engineering :: Physics
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
"""


# Return the git revision as a string
def git_version():
    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {}
        for k in ['SYSTEMROOT', 'PATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        # LANGUAGE is used on win32
        env['LANGUAGE'] = 'C'
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        out = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            env=env).communicate()[0]
        return out

    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        GIT_REVISION = out.strip().decode('ascii')
    except OSError as e:
        print(e)
        GIT_REVISION = "Unknown"

    return GIT_REVISION


def get_version_info():
    # Adding the git rev number needs to be done inside write_version_py(),
    # otherwise the import of package.version messes up
    # the build under Python 3.
    FULLVERSION = VERSION
    if os.path.exists('.git'):
        GIT_REVISION = git_version()
    elif os.path.exists('pyulog/version.py'):
        # must be a source distribution, use existing version file
        try:
            from pyulog.version import git_revision as GIT_REVISION
        except ImportError as e:
            raise ImportError(str(e) + " - Unable to import git_revision. Try removing "
                              "pyulog/version.py and the build directory "
                              "before building.")
    else:
        GIT_REVISION = "Unknown"

    if not ISRELEASED:
        FULLVERSION += '.dev-' + GIT_REVISION[:7]

    return FULLVERSION, GIT_REVISION


def write_version_py(filename='pyulog/version.py'):
    cnt = """
# THIS FILE IS GENERATED FROM SETUP.PY
#pylint: skip-file
short_version = '%(version)s'
version = '%(version)s'
full_version = '%(full_version)s'
git_revision = '%(git_revision)s'
release = %(isrelease)s

if not release:
    version = full_version
"""
    FULLVERSION, GIT_REVISION = get_version_info()

    a = open(filename, 'w')
    try:
        a.write(cnt % {'version': VERSION,
                       'full_version': FULLVERSION,
                       'git_revision': GIT_REVISION,
                       'isrelease': str(ISRELEASED)})
    finally:
        a.close()


def setup_package():
    src_path = os.path.dirname(os.path.abspath(sys.argv[0]))
    old_path = os.getcwd()
    os.chdir(src_path)
    sys.path.insert(0, src_path)

    # Rewrite the version file everytime
    write_version_py()

    metadata = dict(
        name='pyulog',
        maintainer="James Goppert",
        maintainer_email="james.goppert@gmail.com",
        description=DOCLINES[0],
        long_description="\n".join(DOCLINES[2:]),
        url='https://github.com/PX4/pyulog',
        author='Beat Kueng',
        author_email='beat-kueng@gmx.net',
        download_url='https://github.com/PX4/pyulog',
        license='BSD 3-Clause',
        classifiers=[_f for _f in CLASSIFIERS.split('\n') if _f],
        platforms=["Windows", "Linux", "Solaris", "Mac OS-X", "Unix"],
        install_requires=['numpy', 'simplekml'],
        tests_require=['nose'],
        test_suite='nose.collector',
        entry_points = {
            'console_scripts': [
                'ulog_extract_gps_dump=pyulog.extract_gps_dump:main',
                'ulog_info=pyulog.info:main',
                'ulog_messages=pyulog.messages:main',
                'ulog_params=pyulog.params:main',
                'ulog2csv=pyulog.ulog2csv:main',
                'ulog2kml=pyulog.ulog2kml:main',
            ],
        },
        packages=find_packages(),
    )

    FULLVERSION, GIT_REVISION = get_version_info()
    metadata['version'] = FULLVERSION

    try:
        setup(**metadata)
    finally:
        del sys.path[0]
        os.chdir(old_path)
    return

if __name__ == '__main__':
    setup_package()
