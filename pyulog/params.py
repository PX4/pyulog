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
    ulog3 = ULog(ulog_file_name2, message_filter, disable_str_exceptions)
    params1 = ulog1.initial_parameters
    params2 = ulog2.initial_parameters
    p2 = ulog3.initial_parameters
    changed_params1 = ulog1.changed_parameters
    changed_params2 = ulog2.changed_parameters
    if args.default is not None:
        params1 = get_defaults(ulog1, args.default)
        args.initial = True

    changed_param1_list = dict([(i[1],i[2]) for i in changed_params1])
    param_keys1 = sorted(params1.keys())
    param_keys1_minusinflight = sorted(params1.keys()) - changed_param1_list.keys()
    param_keys2 = sorted(params2.keys())
    k2 = sorted(p2.keys())
    delimiter = args.delimiter
    output_file = args.output_filename
    version1 = ''
    version2 = ''

    diffs = []

    if 'boot_console_output' in ulog1.msg_info_multiple_dict:
        console_output = ulog1.msg_info_multiple_dict['boot_console_output'][0]
        escape(''.join(console_output))
        version = re.search('Build datetime:',str(console_output))
        if version is not None:
            version1 = str(console_output)[version.end():version.start()+36]
        else:
            version1 = ' Unknown'

    if 'boot_console_output' in ulog2.msg_info_multiple_dict:
        console_output = ulog2.msg_info_multiple_dict['boot_console_output'][0]
        escape(''.join(console_output))
        version = re.search('Build datetime:',str(console_output))
        if version is not None:
            version2 = str(console_output)[version.end():version.start()+36]
        else:
            version1 = ' Unknown'

    if (version1 != ' Unknown') and (version2 != ' Unknown') and (version1 != version2):
        output_file.write('\n')
        output_file.write('New Firmware \n')
        output_file.write('Build:')
        output_file.write(version1)
        output_file.write('\n')
        output_file.write('↓')
        output_file.write('\n')
        output_file.write('Build:')
        output_file.write(version2)
        output_file.write('\n')
    elif (version1 == ' Unknown') or (version2 == ' Unknown'):
        output_file.write('\n')
        output_file.write('Unknown Firmware: version information missing.\n')
        output_file.write('Build:')
        output_file.write(version1)
        output_file.write('\n')
        output_file.write('↓')
        output_file.write('\n')
        output_file.write('Build:')
        output_file.write(version2)
        output_file.write('\n')

    newlist = []
    deletedlist = []
    if args.format == "csv":
        if (set(param_keys2) - set(param_keys1)) or (set(param_keys1) - set(param_keys2)):

            for param_key2 in set(param_keys2) - set(param_keys1):
                newlist.append((param_key2,str(round(params2[param_key2],6))))

            for param_key1 in set(param_keys1) - set(param_keys2):
                deletedlist.append(param_key1)
    newlist.sort()
    deletedlist.sort()
    for a in newlist:
        output_file.write('New: ')
        output_file.write(a[0])
        output_file.write(', ')
        output_file.write(a[1])
        output_file.write('\n')

    for a in deletedlist:
        output_file.write('Deleted: ')
        output_file.write(a)
        output_file.write('\n')

    output_file.write('\nChanged Pre-flight:\n')
    for param_key1 in param_keys1_minusinflight:
        for param_key2 in param_keys2:
            if (param_key1 == param_key2) and (param_key1 != 'LND_FLIGHT_T_LO') and (param_key1 != 'LND_FLIGHT_T_HI') and (param_key1 != 'COM_FLIGHT_UUID'):
                if isinstance(params1[param_key1],float):
                    if (abs(params1[param_key1] - params2[param_key2]) > 0.001):
                        diffs.append((param_key1,str(round(params1[param_key1],5)),str(round(params2[param_key2],5))))
                else:
                    if (params1[param_key1] != params2[param_key2]):
                        diffs.append((param_key1,str(params1[param_key1]),str(params2[param_key2])))
    diffs.sort()
    for a in diffs:
        output_file.write(a[0])
        output_file.write(': ')
        output_file.write(a[1])
        output_file.write(' -> ')
        output_file.write(a[2])
        output_file.write('\n')
    matched_list = []
    #last_matched_val = 0.0
    output_file.write('\nChanged In-flight:\n')
    for k2 in p2:
        for i in changed_params2:
            if (k2 == i[1]) and (k2 != 'LND_FLIGHT_T_LO') and (k2 != 'LND_FLIGHT_T_HI') and (k2 != 'COM_FLIGHT_UUID'):
                if isinstance(p2[k2],float):
                    if (abs(p2[k2] - i[2]) > 0.001):
                        p2[k2] = round(i[2],5)
                        if not (i[1] in matched_list):
                            matched_list.append(i[1])
                else:
                    if (p2[k2] != i[2]):
                        p2[k2] = i[2]
                        if not (i[1] in matched_list):
                            matched_list.append(i[1])
    for i in matched_list:
        output_file.write(i)
        output_file.write(': ')
        output_file.write(str(round(params2[i],5)))
        output_file.write(' -> ')
        output_file.write(str(round(p2[i],5)))
        output_file.write('\n')