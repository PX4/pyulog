#! /usr/bin/env python
"""
Display information from an ULog file
"""

from __future__ import print_function

import argparse

from .core import ULog

#pylint: disable=too-many-locals, unused-wildcard-import, wildcard-import
#pylint: disable=invalid-name


def main():
    """Commande line interface"""
    parser = argparse.ArgumentParser(description='Display information from an ULog file')
    parser.add_argument('filename', metavar='file.ulg', help='ULog input file')


    args = parser.parse_args()
    ulog_file_name = args.filename
    ulog = ULog(ulog_file_name)

    m1, s1 = divmod(int(ulog.start_timestamp/1e6), 60)
    h1, m1 = divmod(m1, 60)
    m2, s2 = divmod(int((ulog.last_timestamp - ulog.start_timestamp)/1e6), 60)
    h2, m2 = divmod(m2, 60)
    print("Logging start time: {:d}:{:02d}:{:02d}, duration: {:d}:{:02d}:{:02d}".format(
        h1, m1, s1, h2, m2, s2))

    dropout_durations = [dropout.duration for dropout in ulog.dropouts]
    if len(dropout_durations) == 0:
        print("No Dropouts")
    else:
        print("Dropouts: count: {:}, total duration: {:.1f} s, max: {:} ms, mean: {:} ms"
              .format(len(dropout_durations), sum(dropout_durations)/1000.,
                      max(dropout_durations),
                      int(sum(dropout_durations)/len(dropout_durations))))

    version = ulog.get_version_info_str()
    if not version is None:
        print('SW Version: {}'.format(version))

    print("Info Messages:")
    for k in ulog.msg_info_dict:
        print(" {0}: {1}".format(k, ulog.msg_info_dict[k]))


    print("")
    print("{:<41} {:7}, {:10}".format("Name (multi id, message size in bytes)",
                                      "number of data points", "total bytes"))
    for d in ulog.data_list:
        message_size = sum([ULog.UNPACK_TYPES[f.type_str][1] for f in d.field_data])
        num_data_points = len(d.data['timestamp'])
        name_id = "{:} ({:}, {:})".format(d.name, d.multi_id, message_size)
        print(" {:<40} {:7d} {:10d}".format(name_id, num_data_points,
                                            message_size * num_data_points))

