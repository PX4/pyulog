from __future__ import print_function

__author__ = "Beat Kueng"


class PX4ULog:
    """
    This class contains PX4-specific ULog things (field names, etc.)
    """

    def __init__(self, ulog_object):
        """
        @param ulog_object: ULog instance
        """
        self.ulog = ulog_object

    def get_mav_type(self):
        """ return the MAV type as string from initial parameters """

        mav_type = self.ulog.initial_parameters.get('MAV_TYPE', None)
        return {1: 'Fixed Wing',
                2: 'Multirotor',
                20: 'VTOL Tailsitter',
                21: 'VTOL Tiltrotor',
                22: 'VTOL Standard'}.get(mav_type, 'unknown type')

    def get_estimator(self):
        """return the configured estimator as string from initial parameters"""

        mav_type = self.ulog.initial_parameters.get('SYS_MC_EST_GROUP', None)
        return {0: 'INAV', 1: 'LPE', 2: 'EKF2'}.get(mav_type, 'unknown')
