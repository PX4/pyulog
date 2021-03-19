#! /usr/bin/env python
"""
Extract and compare parameters from two ULog files
"""

from __future__ import print_function

import argparse
import sys
import re
from html import escape

from .core import ULog
#pylint: disable=unused-variable, too-many-branches

def get_defaults(ulog, default):
    """ get default params from ulog """
    assert ulog.has_default_parameters, "Log does not contain default parameters"

    if default == 'system': return ulog.get_default_parameters(0)
    if default == 'current_setup': return ulog.get_default_parameters(1)
    raise Exception('invalid value \'{}\' for --default'.format(default))

def main():
    """Commande line interface"""
    parser = argparse.ArgumentParser(description='Extract parameters from an ULog file')
    parser.add_argument('filename1', metavar='file1.ulg', help='ULog input file')
    parser.add_argument('filename2', metavar='file2.ulg', help='ULog input file')

    parser.add_argument('-l', '--delimiter', dest='delimiter', action='store',
                        help='Use delimiter in CSV (default is \',\')', default=',')

    parser.add_argument('-i', '--initial', dest='initial', action='store_true',
                        help='Only extract initial parameters. (octave|csv)', default=False)

    parser.add_argument('-t', '--timestamps', dest='timestamps', action='store_true',
                        help='Extract changed parameters with timestamps. (csv)', default=False)

    parser.add_argument('-f', '--format', dest='format', action='store', type=str,
                        help='csv|octave|qgc', default='csv')

    parser.add_argument('output_filename', metavar='params.txt',
                        type=argparse.FileType('w'), nargs='?',
                        help='Output filename (default=stdout)', default=sys.stdout)

    parser.add_argument('--ignore', dest='ignore', action='store_true',
                        help='Ignore string parsing exceptions', default=False)

    parser.add_argument('-d', '--default', dest='default', action='store', type=str,
                        help='Select default param values instead of configured '
                        'values (implies --initial). Valid values: system|current_setup',
                        default=None)

    args = parser.parse_args()
    ulog_file_name1 = args.filename1
    ulog_file_name2 = args.filename2
    disable_str_exceptions = args.ignore

    message_filter = []
    if not args.initial: message_filter = None

    ulog1 = ULog(ulog_file_name1, message_filter, disable_str_exceptions)
    ulog2 = ULog(ulog_file_name2, message_filter, disable_str_exceptions)

    params1 = ulog1.initial_parameters
    params2 = ulog2.initial_parameters
    if args.default is not None:
        params1 = get_defaults(ulog1, args.default)
        args.initial = True

    param_keys1 = sorted(params1.keys())
    param_keys2 = sorted(params2.keys())
    delimiter = args.delimiter
    output_file = args.output_filename
    version1 = ''
    version2 = ''

    if 'boot_console_output' in ulog1.msg_info_multiple_dict:
        console_output = ulog1.msg_info_multiple_dict['boot_console_output'][0]
        escape(''.join(console_output))
        version = re.search('Build datetime:',str(console_output))
        version1 = str(console_output)[version.end():version.start()+36]

    if 'boot_console_output' in ulog2.msg_info_multiple_dict:
        console_output = ulog2.msg_info_multiple_dict['boot_console_output'][0]
        escape(''.join(console_output))
        version = re.search('Build datetime:',str(console_output))
        version2 = str(console_output)[version.end():version.start()+36]

    if version1 != version2:
        output_file.write('\n')
        output_file.write('New Firmware \n')
        output_file.write('Build:')
        output_file.write(version1)
        output_file.write('\n')
        output_file.write('↓')
        output_file.write('\n')
        output_file.write('Build:')
        output_file.write(version2)
        output_file.write('\n\n')

    if args.format == "csv":
        if (set(param_keys2) - set(param_keys1)) or (set(param_keys1) - set(param_keys2)):
            for param_key2 in set(param_keys2) - set(param_keys1):
                output_file.write('New: ')
                output_file.write(param_key2)
                output_file.write(',')
                output_file.write('\t')
                output_file.write(str(round(params2[param_key2],6)))
                output_file.write('\n')
            for param_key1 in set(param_keys1) - set(param_keys2):
                output_file.write('Deleted: ')
                output_file.write(param_key1)
                output_file.write('\n')

        for param_key1 in param_keys1:
            for param_key2 in param_keys2:
                if (param_key1 == param_key2) and (param_key1 != 'LND_FLIGHT_T_LO') and (param_key1 != 'COM_FLIGHT_UUID'):
                    if isinstance(params1[param_key1],float):
                        if (abs(params1[param_key1] - params2[param_key2]) > 0.001):
                            output_file.write(param_key1)
                            output_file.write(':\t')
                            if len(param_key1) < 15:
                                output_file.write('\t')
                            output_file.write(str(round(params1[param_key1],5)))
                            output_file.write(' -> ')
                            output_file.write(str(round(params2[param_key2],5)))
                            output_file.write('\n')
                    else:
                        if (params1[param_key1] != params2[param_key2]):
                            output_file.write(param_key1)
                            output_file.write(':\t')
                            if len(param_key1) < 15:
                                output_file.write('\t')
                            output_file.write(str(params1[param_key1]))
                            output_file.write(' -> ')
                            output_file.write(str(params2[param_key2]))
                            output_file.write('\n')

