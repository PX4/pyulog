#! /usr/bin/env python

"""
Evaluate a ULog file
"""

from __future__ import print_function

import argparse
import os
#import tools as tl
import numpy as np
from scipy import integrate
import datetime

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

    args = parser.parse_args()

    if args.output and not os.path.isdir(args.output):
        print('Creating output directory {:}'.format(args.output))
        os.mkdir(args.output)

    convert_ulog2csv(args.filename, args.messages, args.output, args.delimiter, args.ignore)


def convert_ulog2csv(ulog_file_name, messages, output, delimiter, disable_str_exceptions=False):
    """
    Coverts and ULog file to a CSV file.

    :param ulog_file_name: The ULog filename to open and read
    :param messages: A list of message names
    :param output: Output file path
    :param delimiter: CSV delimiter

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

    #roll_integ(data)
    #pitch_integ(data)
    #fx21(data)
    #waypo(ulog)
    #consum(ulog)
    msg_analyzer(ulog)


def roll_integ(data):

    """
    Roll angular rate integral evaluator
    """

    d = data[40]

    # use same field order as in the log, except for the timestamp
    data_keys = [f.field_name for f in d.field_data]
    data_keys.remove('timestamp')
    data_keys.insert(0, 'timestamp') # we want timestamp at first position

    rateint = 0
    maxint = 0
    absmaxint = 0

    for i in range(len(d.data['timestamp'])):
        rateint = d.data[data_keys[1]][i] * 100
        if absmaxint < abs(rateint):
            absmaxint = abs(rateint)
            maxint = rateint

    if absmaxint < 20:
        print('Roll integral max =', maxint)
    elif 20 <= absmaxint < 40:
        print('Roll integral max =', maxint)
    else:
        print('Roll integral max =', maxint)


def pitch_integ(data):

    """
    Pitch angular rate integral evaluator
    """

    d = data[40]

    # use same field order as in the log, except for the timestamp
    data_keys = [f.field_name for f in d.field_data]
    data_keys.remove('timestamp')
    data_keys.insert(0, 'timestamp') # we want timestamp at first position

    rateint = 0
    maxint = 0
    absmaxint = 0

    for i in range(len(d.data['timestamp'])):
        rateint = d.data[data_keys[2]][i] * 100
        if absmaxint < abs(rateint):
            absmaxint = abs(rateint)
            maxint = rateint

    if absmaxint < 20:
        print('Pitch integral max =', maxint)
    elif 20 <= absmaxint < 40:
        print('Pitch integral max =', maxint)
    else:
        print('Pitch integral max =', maxint)


def fx21(data):

    """
    Roll error mean calculator
    """

    d1 = data[32] # The 33rd dataset is 'vehicle_attitude_setpoint_0'
    d2 = data[33] # The 34th dataset is 'vehicle_attitude_0'

    # use same field order as in the log, except for the timestamp
    data_keys1 = [f.field_name for f in d1.field_data]
    data_keys1.remove('timestamp')
    data_keys1.insert(0, 'timestamp') # we want timestamp at first position

    data_keys2 = [f.field_name for f in d2.field_data]
    data_keys2.remove('timestamp')
    data_keys2.insert(0, 'timestamp')

    anglelist = np.empty([0, 3])

    for i in range(len(d1.data['timestamp'])):
        anglelist = np.append(anglelist, [[d1.data[data_keys1[0]][i], d1.data[data_keys1[1]][i], 1]], axis=0)

    for i in range(len(d2.data['timestamp'])):
        anglelist = np.append(anglelist, [[d2.data[data_keys2[0]][i], d2.data[data_keys2[1]][i], 2]], axis=0)

    col_num = 0
    anglelist = anglelist[np.argsort(anglelist[:, col_num])]

    print(len(anglelist))

def waypo(ulog):

    d = ulog.get_dataset('mission_result')
    data = ulog.data_list

    # use same field order as in the log, except for the timestamp
    data_keys = [f.field_name for f in d.field_data]
    data_keys.remove('timestamp')
    data_keys.insert(0, 'timestamp') # we want timestamp at first position

    minsec = []

    for i in range(len(d.data['timestamp'])):
        td = datetime.timedelta(microseconds=int(d.data['timestamp'][i]))
        m, s = divmod(td.seconds, 60)
        ctime = format(m, '02') + ':' + format(s, '02')
        minsec.append(ctime)
    
    print('time  -  No.')

    for i in range(len(d.data['timestamp'])):
        wayr = d.data['seq_reached'][i]
        print(minsec[i],'-', '{:>3}'.format(wayr))

def consum(ulog):

    d = ulog.get_dataset('battery_status')
    data = ulog.data_list

    # use same field order as in the log, except for the timestamp
    data_keys = [f.field_name for f in d.field_data]
    data_keys.remove('timestamp')
    data_keys.insert(0, 'timestamp') # we want timestamp at first position

    sm, ss = input('Start time? (format = xx:yy) : ').split(':')
    em, es = input('End time? (format = xx:yy) : ').split(':')

    td = datetime.timedelta(minutes=int(sm), seconds=int(ss))
    st = int(td.total_seconds()*1000000)
    td = datetime.timedelta(minutes=int(em), seconds=int(es))
    et = int(td.total_seconds()*1000000)

    for i in range(len(d.data['timestamp'])):
        if d.data['timestamp'][i] > st:
            si = i
            break
    
    for i in range(len(d.data['timestamp'])):
        if d.data['timestamp'][i] > et:
            ei = i - 1
            break
    
    watt = 0
    x = d.data['timestamp']
    y = d.data['current_a'] * d.data['voltage_filtered_v']

    for i in range(si, ei):
        watt = watt + y[i]

    watt = watt / (ei - si)

    print('Average consumption = ', '{:.2f}'.format(watt), ' W')

def msg_analyzer(ulog):

    m = ulog.logged_messages
    print(m)

