#! /usr/bin/env python

"""
Convert a ULog file into rosbag file(s)
"""

from __future__ import print_function

from collections import defaultdict
import argparse
import re
import rospy # pylint: disable=import-error
import rosbag # pylint: disable=import-error
from px4_msgs import msg as px4_msgs # pylint: disable=import-error

from .core import ULog

#pylint: disable=too-many-locals, invalid-name

def main():
    """Command line interface"""

    parser = argparse.ArgumentParser(description='Convert ULog to rosbag')
    parser.add_argument('filename', metavar='file.ulg', help='ULog input file')
    parser.add_argument('bag', metavar='file.bag', help='rosbag output file')

    parser.add_argument(
        '-m', '--messages', dest='messages',
        help=("Only consider given messages. Must be a comma-separated list of"
              " names, like 'sensor_combined,vehicle_gps_position'"))

    parser.add_argument('-i', '--ignore', dest='ignore', action='store_true',
                        help='Ignore string parsing exceptions', default=False)

    args = parser.parse_args()

    convert_ulog2rosbag(args.filename, args.bag, args.messages, args.ignore)

# https://stackoverflow.com/questions/19053707/converting-snake-case-to-lower-camel-case-lowercamelcase
def to_camel_case(snake_str):
    """ Convert snake case string to camel case """
    components = snake_str.split("_")
    return ''.join(x.title() for x in components)

def convert_ulog2rosbag(ulog_file_name, rosbag_file_name, messages, disable_str_exceptions=False):
    """
    Coverts and ULog file to a CSV file.

    :param ulog_file_name: The ULog filename to open and read
    :param rosbag_file_name: The rosbag filename to open and write
    :param messages: A list of message names

    :return: No
    """

    array_pattern = re.compile(r"(.*?)\[(.*?)\]")
    msg_filter = messages.split(',') if messages else None

    ulog = ULog(ulog_file_name, msg_filter, disable_str_exceptions)
    data = ulog.data_list

    multiids = defaultdict(set)
    for d in data:
        multiids[d.name].add(d.multi_id)

    with rosbag.Bag(rosbag_file_name, 'w') as bag:
        items = []
        for d in data:
            if multiids[d.name] == {0}:
                topic = "/px4/{}".format(d.name)
            else:
                topic = "/px4/{}_{}".format(d.name, d.multi_id)
            msg_type = getattr(px4_msgs, to_camel_case(d.name))

            for i in range(len(d.data['timestamp'])):
                msg = msg_type()
                for f in d.field_data:
                    result = array_pattern.match(f.field_name)
                    value = d.data[f.field_name][i]
                    if result:
                        field, array_index = result.groups()
                        array_index = int(array_index)
                        if isinstance(getattr(msg, field), bytes):
                            attr = bytearray(getattr(msg, field))
                            attr[array_index] = value
                            setattr(msg, field, bytes(attr))
                        else:
                            getattr(msg, field)[array_index] = value
                    else:
                        setattr(msg, f.field_name, value)
                ts = rospy.Time(nsecs=d.data['timestamp'][i]*1000)
                items.append((topic, msg, ts))
        items.sort(key=lambda x: x[2])
        for topic, msg, ts in items:
            bag.write(topic, msg, ts)

