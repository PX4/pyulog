#! /usr/bin/env python
"""
Display logged messages from an ULog file
"""

import argparse

from .core import ULog
from .px4_events import PX4Events
#pylint: disable=invalid-name

def main():
    """Commande line interface"""

    parser = argparse.ArgumentParser(description='Display logged messages from an ULog file')
    parser.add_argument('filename', metavar='file.ulg', help='ULog input file')
    parser.add_argument('-i', '--ignore', dest='ignore', action='store_true',
                        help='Ignore string parsing exceptions', default=False)

    args = parser.parse_args()
    ulog_file_name = args.filename
    disable_str_exceptions = args.ignore

    msg_filter = ['event']
    ulog = ULog(ulog_file_name, msg_filter, disable_str_exceptions)

    logged_messages = [(m.timestamp, m.log_level_str(), m.message) for m in ulog.logged_messages]

    # If this is a PX4 log, try to get the events too
    if ulog.msg_info_dict.get('sys_name', '') == 'PX4':
        px4_events = PX4Events()
        events = px4_events.get_logged_events(ulog)

        for t, log_level, message in logged_messages:
            # backwards compatibility: a string message with appended tab is output
            # in addition to an event with the same message so we can ignore those
            if message[-1] == '\t':
                continue
            events.append((t, log_level, message))

        logged_messages = sorted(events, key=lambda m: m[0])

    for t, log_level, message in logged_messages:
        m1, s1 = divmod(int(t/1e6), 60)
        h1, m1 = divmod(m1, 60)
        print("{:d}:{:02d}:{:02d} {:}: {:}".format(h1, m1, s1, log_level, message))



