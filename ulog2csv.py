#! /usr/bin/env python

from __future__ import print_function

import argparse
import os

from ulog_parser import *

"""
Convert an ULog file into CSV file(s)
"""

parser = argparse.ArgumentParser(description='Convert ULog to CSV')
parser.add_argument('filename', metavar='file.ulg', help='ULog input file')

parser.add_argument('-m', '--messages', dest='messages',
        help=("Only consider given messages. Must be a comma-separated list of"
              "names, like 'sensor_combined,vehicle_gps_position'"))
parser.add_argument('-d', '--delimiter', dest='delimiter', action='store',
                    help="Use delimiter in CSV (default is ',')", default=',')


def is_valid_directory(parser, arg):
    if os.path.isdir(arg):
        # Directory exists so return the directory
        return arg
    else:
        parser.error('The directory {} does not exist'.format(arg))
parser.add_argument('-o', '--output', dest='output', action='store',
                   help='Output directory (default is same as input file)',
                   metavar='DIR', type=lambda x: is_valid_directory(parser, x))

args = parser.parse_args()
ulog_file_name = args.filename
msg_filter = args.messages.split(',') if args.messages else None

ulog = ULog(ulog_file_name, msg_filter)
data = ulog.data_list

output_file_prefix = ulog_file_name
# strip '.ulg'
if output_file_prefix.lower().endswith('.ulg'):
    output_file_prefix = output_file_prefix[:-4]

# write to different output path?
if args.output:
    base_name = os.path.basename(output_file_prefix)
    output_file_prefix = os.path.join(args.output, base_name)

for d in data:
    fmt = '{0}_{1}_{2}.csv'
    output_file_name = fmt.format(output_file_prefix, d.name, d.multi_id)
    fmt = 'Writing {0} ({1} data points)'
    print(fmt.format(output_file_name, len(d.data['timestamp'])))
    with open(output_file_name, 'w') as csvfile:
        delimiter = args.delimiter

        # use same field order as in the log, except for the timestamp
        data_keys = [f.field_name for f in d.field_data]
        data_keys.remove('timestamp')
        data_keys.insert(0, 'timestamp')  # we want timestamp at first position

        # we don't use np.savetxt, because we have multiple arrays with
        # potentially different data types. However the following is quite
        # slow...

        # write the header
        last_elem = len(data_keys)-1
        # for k in range(len(data_keys)):
        #    csvfile.write(data_keys[k])
        #    if k != last_elem:
        #        csvfile.write(delimiter)
        # csvfile.write('\n')
        csvfile.write(delimiter.join(data_keys) + '\n')

        # write the data
        for i in range(len(d.data['timestamp'])):
            for k in range(len(data_keys)):
                csvfile.write(str(d.data[data_keys[k]][i]))
                if k != last_elem:
                    csvfile.write(delimiter)
            csvfile.write('\n')
