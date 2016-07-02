#! /usr/bin/env python

from __future__ import print_function

import argparse
import os

from ulog_parser import *

"""
Display information from an ULog file
"""

parser = argparse.ArgumentParser(description='Display information from an ULog file')
parser.add_argument('filename', metavar='file.ulg', help='ULog input file')

parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                   help='More verbose output (and slower)', default=False)


args = parser.parse_args()
ulog_file_name = args.filename

verbose = args.verbose

if verbose:
    msg_filter = None
else:
    msg_filter = [] # we don't need the messages

ulog = ULog(ulog_file_name, msg_filter)


dropout_durations = [ dropout.duration for dropout in ulog.dropouts]
print("Dropouts: count: {:}, total duration: {:.1f} s, max: {:} ms, mean: {:} ms"
        .format(len(dropout_durations), sum(dropout_durations)/1000.,
                max(dropout_durations),
                sum(dropout_durations)/len(dropout_durations)))

print("Info Messages:")
for k in ulog.msg_info_dict:
    print(" {0}: {1}".format(k, ulog.msg_info_dict[k]))

if verbose:
    m1, s1 = divmod(int(ulog.start_timestamp/1e6), 60)
    h1, m1 = divmod(m1, 60)
    m2, s2 = divmod(int((ulog.last_timestamp - ulog.start_timestamp)/1e6), 60)
    h2, m2 = divmod(m2, 60)
    print("Logging start time: {:d}:{:02d}:{:02d}, duration: {:d}:{:02d}:{:02d}".format(
        h1, m1, s1, h2, m2, s2))

    print("")
    print("Message Name (multi id): number of data points")
    for d in ulog.data_list:
        print(" {0} ({1}): {2}".format(d.name, d.multi_id,
            len(d.data['timestamp'])))
    

