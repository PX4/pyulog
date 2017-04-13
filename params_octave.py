#! /usr/bin/env python

from __future__ import print_function

import argparse
import os

from ulog_parser import *

"""
Extract parameters from an ULog file
Limitation: currently does not handle multiple values for a parameter (writes only the initial values)
the required format for an array is this:
    # name: x
    # type: matrix
    # rows: 1
    # columns: 4
     1 2 3 4
"""

parser = argparse.ArgumentParser(description='Extract parameters from an ULog file')
parser.add_argument('filename', metavar='file.ulg', help='ULog input file')

parser.add_argument('-d', '--delimiter', dest='delimiter', action='store',
                   help='Use delimiter in CSV (default is \',\')', default=',')

parser.add_argument('-i', '--initial', dest='initial', action='store_true',
                   help='Only extract initial parameters', default=False)

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


for param_key in param_keys:
    output_file.write('#name ')
    output_file.write(param_key)
    output_file.write('\n#type: scalar\n')
    output_file.write(str(ulog.initial_parameters[param_key]))

#    if not args.initial:
#        for t, name, value in ulog.changed_parameters:
#            if name == param_key:
#                output_file.write(delimiter)
#                output_file.write(str(value))
    output_file.write('\n')


