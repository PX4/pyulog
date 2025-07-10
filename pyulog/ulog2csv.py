#! /usr/bin/env python

"""
Convert a ULog file into CSV file(s)
"""

import argparse
import os
import re

import numpy as np

from .core import ULog

#pylint: disable=too-many-locals, invalid-name, consider-using-enumerate

def main():
    """Command line interface"""

    parser = argparse.ArgumentParser(description='Convert ULog to CSV')
    parser.add_argument('filename', metavar='file.ulg', help='ULog input file')

    parser.add_argument(
        '-m', '--messages', dest='messages',
        help=("Only consider given messages. Must be a comma-separated list of"
              " names, like 'sensor_combined,vehicle_gps_position'"))
    parser.add_argument('-d', '--delimiter', dest='delimiter', action='store',
                        help="Use delimiter in CSV (default is ',')", default=',')


    parser.add_argument('-o', '--output', dest='output', action='store',
                        help='Output directory (default is same as input file)',
                        metavar='DIR')
    parser.add_argument('-i', '--ignore', dest='ignore', action='store_true',
                        help='Ignore string parsing exceptions', default=False)

    parser.add_argument(
        '-ts', '--time_s', dest='time_s', type = int,
        help="Only convert data after this timestamp (in seconds)")

    parser.add_argument(
        '-te', '--time_e', dest='time_e', type=int,
        help="Only convert data upto this timestamp (in seconds)")

    args = parser.parse_args()

    if args.output and not os.path.isdir(args.output):
        print('Creating output directory {:}'.format(args.output))
        os.mkdir(args.output)

    convert_ulog2csv(args.filename, args.messages, args.output, args.delimiter,
                     args.time_s, args.time_e, args.ignore)


def read_string_data(data: ULog.Data, field_name: str, array_size: int, data_index: int) -> str:
    """ Parse a data field as string """
    s = ''
    for index in range(array_size):
        character = data.data[f'{field_name}[{index}]'][data_index]
        if character == 0:
            break
        s += chr(character)
    return s

def convert_ulog2csv(ulog_file_name, messages, output, delimiter, time_s, time_e,
                     disable_str_exceptions=False):
    """
    Coverts and ULog file to a CSV file.

    :param ulog_file_name: The ULog filename to open and read
    :param messages: A list of message names
    :param output: Output file path
    :param delimiter: CSV delimiter
    :param time_s: Offset time for conversion in seconds
    :param time_e: Limit until time for conversion in seconds

    :return: None
    """

    msg_filter = messages.split(',') if messages else None

    ulog = ULog(ulog_file_name, msg_filter, disable_str_exceptions)
    data = ulog.data_list

    output_file_prefix = ulog_file_name
    # strip '.ulg'
    if output_file_prefix.lower().endswith('.ulg'):
        output_file_prefix = output_file_prefix[:-4]

    # write to different output path?
    if output:
        base_name = os.path.basename(output_file_prefix)
        output_file_prefix = os.path.join(output, base_name)

    array_pattern = re.compile(r"(.*)\[(.*?)\]")

    def get_fields(data: ULog.Data) -> tuple[list[str], dict[str, int]]:
        # use same field order as in the log, except for the timestamp
        data_keys = []
        string_array_sizes = {}
        for f in data.field_data:
            if f.field_name.startswith('_padding'):
                continue
            result = array_pattern.fullmatch(f.field_name)
            if result and f.type_str == 'char':  # string (array of char's)
                field, array_index = result.groups()
                array_index = int(array_index)
                string_array_sizes[field] = max(array_index + 1, string_array_sizes.get(field, 0))
                if array_index == 0:
                    data_keys.append(field)
            else:
                data_keys.append(f.field_name)
        data_keys.remove('timestamp')
        data_keys.insert(0, 'timestamp')  # we want timestamp at first position
        return data_keys, string_array_sizes

    for d in data:
        name_without_slash = d.name.replace('/', '_')
        output_file_name = f'{output_file_prefix}_{name_without_slash}_{d.multi_id}.csv'
        num_data_points = len(d.data['timestamp'])
        print(f'Writing {output_file_name} ({num_data_points} data points)')
        with open(output_file_name, 'w', encoding='utf-8') as csvfile:

            data_keys, string_array_sizes = get_fields(d)

            # we don't use np.savetxt, because we have multiple arrays with
            # potentially different data types. However the following is quite
            # slow...

            # write the header
            csvfile.write(delimiter.join(data_keys) + '\n')

            #get the index for row where timestamp exceeds or equals the required value
            time_s_i = np.where(d.data['timestamp'] >= time_s * 1e6)[0][0] \
                    if time_s else 0
            #get the index for row upto the timestamp of the required value
            time_e_i = np.where(d.data['timestamp'] >= time_e * 1e6)[0][0] \
                    if time_e else len(d.data['timestamp'])

            # write the data
            last_elem = len(data_keys)-1
            for i in range(time_s_i, time_e_i):
                for k in range(len(data_keys)):
                    if data_keys[k] in string_array_sizes: # string
                        s = read_string_data(d, data_keys[k], string_array_sizes[data_keys[k]], i)
                        csvfile.write(s)
                    else:
                        csvfile.write(str(d.data[data_keys[k]][i]))
                    if k != last_elem:
                        csvfile.write(delimiter)
                csvfile.write('\n')

