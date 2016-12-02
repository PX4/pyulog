#! /usr/bin/env python

from __future__ import print_function

import argparse
import os
import sys

from .core import ULog

"""
Extract parameters from an ULog file
"""

def main():
    """Commande line interface"""

    parser = argparse.ArgumentParser(description='Extract parameters from an ULog file')
    parser.add_argument('filename', metavar='file.ulg', help='ULog input file')

    parser.add_argument('-d', '--delimiter', dest='delimiter', action='store',
                       help='Use delimiter in CSV (default is \',\')', default=',')

    parser.add_argument('-i', '--initial', dest='initial', action='store_true',
                        help='Only extract initial parameters', default=False)

    parser.add_argument('-o', '--octave', dest='octave', action='store_true',
                        help='Use Octave format', default=False)

    parser.add_argument('output_filename', metavar='params.txt',
            type=argparse.FileType('w'), nargs='?',
            help='Output filename (default=stdout)', default=sys.stdout)

    args = parser.parse_args()
    ulog_file_name = args.filename

    ulog = ULog(ulog_file_name, [])
    data = ulog.data_list

    param_keys = sorted(ulog.initial_parameters.keys())
    delimiter = args.delimiter
    output_file = args.output_filename

    if not args.octave:
        for param_key in param_keys:
            output_file.write(param_key)
            output_file.write(delimiter)
            output_file.write(str(ulog.initial_parameters[param_key]))
            if not args.initial:
                for t, name, value in ulog.changed_parameters:
                    if name == param_key:
                        output_file.write(delimiter)
                        output_file.write(str(value))
            output_file.write('\n')

    else:

        for param_key in param_keys:
            output_file.write('# name ')
            output_file.write(param_key)
            values = [ulog.initial_parameters[param_key]]

            if not args.initial:
                for t, name, value in ulog.changed_parameters:
                    if name == param_key:
                        values += [value]

            if len(values) > 1:
                output_file.write('\n# type: matrix\n')
                output_file.write('# rows: 1\n')
                output_file.write('# columns: ')
                output_file.write(str(len(values)) + '\n')
                for i in range(0, len(values)):
                    output_file.write(str(values[i]) + ' ')

            else:
                output_file.write('\n# type: scalar\n')
                output_file.write(str(values[0]))

            output_file.write('\n')
