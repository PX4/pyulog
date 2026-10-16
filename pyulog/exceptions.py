""" Exceptions raised by pyulog """


class ULogException(Exception):
    """
    Raised if a ULog file cannot be parsed at all, e.g. because of an invalid header.
    Corrupt messages are skipped instead, and reported via ULog.file_corruption.
    """


class ULogIncompatibleFlagException(ULogException):
    """
    Raised if a ULog file has an unknown incompatible flag set, i.e. it uses a format
    extension that this version of pyulog cannot parse.
    """
