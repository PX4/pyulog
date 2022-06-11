#! /usr/bin/env python

"""
Tools for ulogEvaluator
"""

import math

def starttime(data):

    """
    detect start time of logs
    """

    d = data[0]
    # use same field order as in the log, except for the timestamp
    data_keys = [f.field_name for f in d.field_data]
    data_keys.remove('timestamp')
    data_keys.insert(0, 'timestamp') # we want timestamp at first position
    tmin = d.data[data_keys[0]][0]
    flag = 0
    ii = 0

    for d in data:

        # use same field order as in the log, except for the timestamp
        data_keys = [f.field_name for f in d.field_data]
        data_keys.remove('timestamp')
        data_keys.insert(0, 'timestamp') # we want timestamp at first position

        tstamp = 0

        for i in range(len(d.data['timestamp'])):

            tstamp = d.data[data_keys[0]][i]

            if tstamp < tmin:
                tmin = tstamp
                flag = ii

        ii = ii + 1

    num = (tmin, flag)

    return num


def lasttime(data):

    """
    detect last time of logs
    """

    d = data[0]
    # use same field order as in the log, except for the timestamp
    data_keys = [f.field_name for f in d.field_data]
    data_keys.remove('timestamp')
    data_keys.insert(0, 'timestamp') # we want timestamp at first position
    tmax = 0
    flag = 0
    ii = 0

    for d in data:

        # use same field order as in the log, except for the timestamp
        data_keys = [f.field_name for f in d.field_data]
        data_keys.remove('timestamp')
        data_keys.insert(0, 'timestamp') # we want timestamp at first position

        tstamp = 0

        for i in range(len(d.data['timestamp'])):

            tstamp = d.data[data_keys[0]][i]

            if tstamp > tmax:
                tmax = tstamp
                flag = ii

        ii = ii + 1

    num = (tmax, flag)

    return num


def q2euler(ulog):

    """
    vehicle attitude quaternion to euler(degree)
    """

    d = ulog.get_dataset('vehicle_attitude') # The 34th dataset is 'vehicle_attitude_0'

    degRoll1 = [0] * len(d.data['timestamp'])
    degPitch1 = [0] * len(d.data['timestamp'])
    degYaw1 = [0] * len(d.data['timestamp'])
    q0 = 0
    q1 = 0
    q2 = 0
    q3 = 0

    # use same field order as in the log, except for the timestamp
    data_keys = [f.field_name for f in d.field_data]
    data_keys.remove('timestamp')
    data_keys.insert(0, 'timestamp') # we want timestamp at first position

    for i in range(len(d.data['timestamp'])):
        q0 = d.data[data_keys[1]][i]
        q1 = d.data[data_keys[2]][i]
        q2 = d.data[data_keys[3]][i]
        q3 = d.data[data_keys[4]][i]
        eulRoll = math.atan2(2.0 * (q2 * q3 + q0 * q1), q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3)
        degRoll1[i] = math.degrees(eulRoll)
        eulPitch = math.asin(2.0 * (q0 * q2 - q1 * q3))
        degPitch1[i] = math.degrees(eulPitch)
        eulYaw = math.atan2(2.0 * (q1 * q2 + q0 * q3), q0 * q0 + q1 * q1 - q2 * q2 - q3 * q3)
        degYaw1[i] = math.degrees(eulYaw)


def degRoll(q0, q1, q2, q3):

    """
    vehicle attitude quaternion to Roll Angle(degree)
    """

    eul = math.atan2(2.0 * (q2 * q3 + q0 * q1), q0 * q0 - q1 * q1 - q2 * q2 + q3 * q3)
    deg = math.degrees(eul)

    return deg


def degPitch(q0, q1, q2, q3):

    """
    vehicle attitude quaternion to Pitch Angle(degree)
    """

    eul = math.asin(2.0 * (q0 * q2 - q1 * q3))
    deg = math.degrees(eul)

    return deg


def degYaw(q0, q1, q2, q3):

    """
    vehicle attitude quaternion to Yaw Angle(degree)
    """

    eul = math.atan2(2.0 * (q1 * q2 + q0 * q3), q0 * q0 + q1 * q1 - q2 * q2 - q3 * q3)
    deg = math.degrees(eul)

    return deg
