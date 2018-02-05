#! /usr/bin/env python
"""
Extract the raw gps communication from an ULog file.
"""

from __future__ import print_function

import argparse
import os

from .core import ULog

#pylint: disable=too-many-locals, unused-wildcard-import, wildcard-import

def main():
    """
    Command line interface
    """
    parser = argparse.ArgumentParser(
        description='Extract the raw gps communication from an ULog file')
    parser.add_argument('filename', metavar='file.ulg', help='ULog input file')

    def is_valid_directory(parser, arg):
        """Check if valid directory"""
        if not os.path.isdir(arg):
            parser.error('The directory {} does not exist'.format(arg))
        # File exists so return the directory
        return arg
    parser.add_argument('-o', '--output', dest='output', action='store',
                        help='Output directory (default is CWD)',
                        metavar='DIR', type=lambda x: is_valid_directory(parser, x))

    args = parser.parse_args()
    ulog_file_name = args.filename

    msg_filter = ['gps_dump']
    ulog = ULog(ulog_file_name, msg_filter)
    data = ulog.data_list

    output_file_prefix = os.path.basename(ulog_file_name)
    # strip '.ulg'
    if output_file_prefix.lower().endswith('.ulg'):
        output_file_prefix = output_file_prefix[:-4]

    # write to different output path?
    if args.output != None:
        output_file_prefix = os.path.join(args.output, output_file_prefix)

    to_dev_filename = output_file_prefix+'_to_device.dat'
    from_dev_filename = output_file_prefix+'_from_device.dat'


    if len(data) == 0:
        print("File {0} does not contain gps_dump messages!".format(ulog_file_name))
        exit(0)

    gps_dump_data = data[0]

    # message format check
    field_names = [f.field_name for f in gps_dump_data.field_data]
    if not 'len' in field_names or not 'data[0]' in field_names:
        print('Error: gps_dump message has wrong format')
        exit(-1)

    if len(ulog.dropouts) > 0:
        print("Warning: file contains {0} dropouts".format(len(ulog.dropouts)))

    print("Creating files {0} and {1}".format(to_dev_filename, from_dev_filename))

    with open(to_dev_filename, 'wb') as to_dev_file:
        with open(from_dev_filename, 'wb') as from_dev_file:
            msg_lens = gps_dump_data.data['len']
            for i in range(len(gps_dump_data.data['timestamp'])):
                msg_len = msg_lens[i]
                if msg_len & (1<<7):
                    msg_len = msg_len & ~(1<<7)
                    file_handle = to_dev_file
                else:
                    file_handle = from_dev_file
                for k in range(msg_len):
                    file_handle.write(gps_dump_data.data['data['+str(k)+']'][i])
