"""
Extract values from a ULog file message to use in scripting
"""

import numpy as np
from .core import ULog

def extract_message(ulog_file_name: str, message: str, time_s: "int | None" = None, time_e: "int | None" = None,
                     disable_str_exceptions=False) -> list[dict]:
    """
    Extract values from a ULog file

    :param ulog_file_name: (str) The ULog filename to open and read
    :param message: (str) A ULog message to return values from
    :param time_s: (int) Offset time for conversion in seconds
    :param time_e: (int) Limit until time for conversion in seconds

    :return: (list[dict]) A list of each record from the ULog as key-value pairs
    """

    if not type(message) == str:
        raise AttributeError("Must provide a message to pull from ULog file")

    msg_filter = message.split(',') if message else None

    ulog = ULog(ulog_file_name, msg_filter, disable_str_exceptions)
    data = ulog.data_list

    if not data:
        raise AttributeError("Provided message is not in the ULog file")

    values = []
    for record in data:
        # use same field order as in the log, except for the timestamp
        data_keys = [f.field_name for f in record.field_data]
        data_keys.remove('timestamp')
        data_keys.insert(0, 'timestamp')  # we want timestamp at first position

        #get the index for row where timestamp exceeds or equals the required value
        time_s_i = np.where(record.data['timestamp'] >= time_s * 1e6)[0][0] \
                if time_s else 0
        #get the index for row upto the timestamp of the required value
        time_e_i = np.where(record.data['timestamp'] >= time_e * 1e6)[0][0] \
                if time_e else len(record.data['timestamp'])

        # write the data
        for i in range(time_s_i, time_e_i):
            row = {}
            for k in range(len(data_keys)):
                row[data_keys[k]] = record.data[data_keys[k]][i]
            values.append(row)

    return values
