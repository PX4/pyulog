""" Main Module to load and parse an ULog file """

from __future__ import print_function

import struct
import sys
import numpy as np
#pylint: disable=too-many-instance-attributes, unused-argument, missing-docstring
#pylint: disable=protected-access, too-many-branches

__author__ = "Beat Kueng"


# check python version
if sys.hexversion >= 0x030000F0:
    RUNNING_PYTHON3 = True
    def _parse_string(cstr):
        return str(cstr, 'ascii')
else:
    RUNNING_PYTHON3 = False
    def _parse_string(cstr):
        return str(cstr)


class ULog(object):
    """
    This class parses an ulog file
    """

    ## constants ##
    HEADER_BYTES = b'\x55\x4c\x6f\x67\x01\x12\x35'

    # message types
    MSG_TYPE_FORMAT = ord('F')
    MSG_TYPE_DATA = ord('D')
    MSG_TYPE_INFO = ord('I')
    MSG_TYPE_PARAMETER = ord('P')
    MSG_TYPE_ADD_LOGGED_MSG = ord('A')
    MSG_TYPE_REMOVE_LOGGED_MSG = ord('R')
    MSG_TYPE_SYNC = ord('S')
    MSG_TYPE_DROPOUT = ord('O')
    MSG_TYPE_LOGGING = ord('L')

    UNPACK_TYPES = {
        'int8_t':   ['b', 1, np.int8],
        'uint8_t':  ['B', 1, np.uint8],
        'int16_t':  ['h', 2, np.int16],
        'uint16_t': ['H', 2, np.uint16],
        'int32_t':  ['i', 4, np.int32],
        'uint32_t': ['I', 4, np.uint32],
        'int64_t':  ['q', 8, np.int64],
        'uint64_t': ['Q', 8, np.uint64],
        'float':    ['f', 4, np.float32],
        'double':   ['d', 8, np.float64],
        'bool':     ['?', 1, np.int8],
        'char':     ['c', 1, np.int8]
        }

    # pre-init unpack structs for quicker use
    _unpack_ushort_byte = struct.Struct('<HB').unpack
    _unpack_ushort = struct.Struct('<H').unpack
    _unpack_uint64 = struct.Struct('<Q').unpack


    class Data(object):
        """ contains the final topic data for a single topic and instance """

        def __init__(self, message_add_logged_obj):
            self.multi_id = message_add_logged_obj.multi_id
            self.name = message_add_logged_obj.message_name
            self.field_data = message_add_logged_obj.field_data
            self.timestamp_idx = message_add_logged_obj.timestamp_idx

            # get data as numpy.ndarray
            np_array = np.frombuffer(message_add_logged_obj.buffer,
                                     dtype=message_add_logged_obj.dtype)
            # convert into dict of np.array (which is easier to handle)
            self.data = {}
            for name in np_array.dtype.names:
                self.data[name] = np_array[name]

        def list_value_changes(self, field_name):
            """ get a list of (timestamp, value) tuples, whenever the value
            changes. The first data point with non-zero timestamp is always
            included, messages with timestamp = 0 are ignored """

            t = self.data['timestamp']
            x = self.data[field_name]
            indices = t != 0 # filter out 0 values
            t = t[indices]
            x = x[indices]
            if len(t) == 0: return []
            ret = [(t[0], x[0])]
            indices = np.where(x[:-1] != x[1:])[0] + 1
            ret.extend(zip(t[indices], x[indices]))
            return ret



    ## Representations of the messages from the log file ##

    class MessageHeader(object):
        """ 3 bytes ULog message header """

        def __init__(self):
            self.msg_size = 0
            self.msg_type = 0

        def initialize(self, data):
            self.msg_size, self.msg_type = ULog._unpack_ushort_byte(data)

    class MessageInfo(object):
        """ ULog info message representation """

        def __init__(self, data, header):
            key_len, = struct.unpack('<B', data[0:1])
            type_key = _parse_string(data[1:1+key_len])
            type_key_split = type_key.split(' ')
            self.type = type_key_split[0]
            self.key = type_key_split[1]
            if self.type.startswith('char['): # it's a string
                self.value = _parse_string(data[1+key_len:])
            elif self.type in ULog.UNPACK_TYPES:
                unpack_type = ULog.UNPACK_TYPES[self.type]
                self.value, = struct.unpack('<'+unpack_type[0], data[1+key_len:])
            else: # probably an array (or non-basic type)
                self.value = data[1+key_len:]

    class MessageFormat(object):
        """ ULog message format representation """

        def __init__(self, data, header):
            format_arr = _parse_string(data).split(':')
            self.name = format_arr[0]
            types_str = format_arr[1].split(';')
            self.fields = [] # list of tuples (type, array_size, name)
            for t in types_str:
                if len(t) > 0:
                    self.fields.append(self.extract_type(t))

        @staticmethod
        def extract_type(field_str):
            field_str_split = field_str.split(' ')
            type_str = field_str_split[0]
            name_str = field_str_split[1]
            a_pos = type_str.find('[')
            if a_pos == -1:
                array_size = 1
                type_name = type_str
            else:
                b_pos = type_str.find(']')
                array_size = int(type_str[a_pos+1:b_pos])
                type_name = type_str[:a_pos]
            return type_name, array_size, name_str

    class MessageLogging(object):
        """ ULog logged string message representation """

        def __init__(self, data, header):
            self.log_level, = struct.unpack('<B', data[0:1])
            self.timestamp, = struct.unpack('<Q', data[1:9])
            self.message = _parse_string(data[9:])

        def log_level_str(self):
            return {ord('0'): 'EMERGENCY',
                    ord('1'): 'ALERT',
                    ord('2'): 'CRITICAL',
                    ord('3'): 'ERROR',
                    ord('4'): 'WARNING',
                    ord('5'): 'NOTICE',
                    ord('6'): 'INFO',
                    ord('7'): 'DEBUG'}.get(self.log_level, 'UNKNOWN')

    class MessageDropout(object):
        """ ULog dropout message representation """
        def __init__(self, data, header, timestamp):
            self.duration, = struct.unpack('<H', data)
            self.timestamp = timestamp

    class FieldData(object):
        """ Type and name of a single ULog data field """
        def __init__(self, field_name, type_str):
            self.field_name = field_name
            self.type_str = type_str

    class MessageAddLogged(object):
        """ ULog add logging data message representation """
        def __init__(self, data, header, message_formats):
            self.multi_id, = struct.unpack('<B', data[0:1])
            self.msg_id, = struct.unpack('<H', data[1:3])
            self.message_name = _parse_string(data[3:])
            self.field_data = [] # list of FieldData
            self.timestamp_idx = -1
            self.parse_format(message_formats)

            self.timestamp_offset = 0
            for field in self.field_data:
                if field.field_name == 'timestamp':
                    break
                self.timestamp_offset += ULog.UNPACK_TYPES[field.type_str][1]

            self.buffer = bytearray() # accumulate all message data here

            # construct types for numpy
            dtype_list = []
            for field in self.field_data:
                numpy_type = ULog.UNPACK_TYPES[field.type_str][2]
                dtype_list.append((field.field_name, numpy_type))
            self.dtype = np.dtype(dtype_list).newbyteorder('<')


        def parse_format(self, message_formats):
            self.parse_nested_type('', self.message_name, message_formats)

            # remove padding fields at the end
            while (len(self.field_data) > 0 and
                   self.field_data[-1].field_name.startswith('_padding')):
                self.field_data.pop()

        def parse_nested_type(self, prefix_str, type_name, message_formats):
            # we flatten nested types
            message_format = message_formats[type_name]
            for (type_name, array_size, field_name) in message_format.fields:
                if type_name in ULog.UNPACK_TYPES:
                    if array_size > 1:
                        for i in range(array_size):
                            self.field_data.append(ULog.FieldData(
                                prefix_str+field_name+'['+str(i)+']', type_name))
                    else:
                        self.field_data.append(ULog.FieldData(prefix_str+field_name, type_name))
                    if prefix_str+field_name == 'timestamp':
                        self.timestamp_idx = len(self.field_data) - 1
                else: # nested type
                    if array_size > 1:
                        for i in range(array_size):
                            self.parse_nested_type(prefix_str+field_name+'['+str(i)+'].',
                                                   type_name, message_formats)
                    else:
                        self.parse_nested_type(prefix_str+field_name+'.',
                                               type_name, message_formats)

    class MessageData(object):
        def __init__(self):
            self.timestamp = 0

        def initialize(self, data, header, subscriptions, ulog_object):
            msg_id, = ULog._unpack_ushort(data[:2])
            if msg_id in subscriptions:
                subscription = subscriptions[msg_id]
                # accumulate data to a buffer, will be parsed later
                subscription.buffer += data[2:]
                t_off = subscription.timestamp_offset
                # TODO: the timestamp can have another size than uint64
                self.timestamp, = ULog._unpack_uint64(data[t_off+2:t_off+10])
            else:
                if not msg_id in ulog_object.filtered_message_ids:
                    # this is an error, but make it non-fatal
                    if not msg_id in ulog_object.missing_message_ids:
                        ulog_object.missing_message_ids.add(msg_id)
                        print('Warning: no subscription found for message id {:}. Continuing,'
                              ' but file is most likely corrupt'.format(msg_id))
                self.timestamp = 0


    def __init__(self, file_name, message_name_filter_list=None):
        """
        Initialize the object & load the file

        @param message_name_filter_list: list of strings, to only load messages
               with the given names.
        """


        ## parsed data: public interface ##

        self.start_timestamp = 0 # timestamp of file start
        self.last_timestamp = 0 # timestam of last message
        self.msg_info_dict = {} # dict of all information messages
        self.initial_parameters = {} # dict of all initially set parameters (key=param name)
        self.changed_parameters = [] # list of all changed parameters (tuple of
                                     # (timestamp, name, value))
        self.message_formats = {} # dict with key=format name, value = MessageFormat object
        self.logged_messages = [] # array of MessageLogging objects
        self.dropouts = [] # list of MessageDropout objects
        self.data_list = [] # extracted data: list of Data objects


        """ The following are internal representations only """

        self.subscriptions = {} # dict of key=msg_id, value=MessageAddLogged
        self.filtered_message_ids = set() # MessageAddLogged id's that are filtered
        self.missing_message_ids = set() # MessageAddLogged id's that could not be found


        self._load_file(file_name, message_name_filter_list)

    def _load_file(self, file_name, message_name_filter_list):
        """ load and parse an ULog file into memory """
        self.file_name = file_name
        self.file_handle = open(file_name, "rb")

        # parse the whole file
        self._read_file_header()
        self.last_timestamp = self.start_timestamp
        self._read_file_definitions()
        self._read_file_data(message_name_filter_list)


    def _read_file_header(self):
        header_data = self.file_handle.read(16)
        if len(header_data) != 16:
            raise Exception("Invalid file format (Header too short)")
        if header_data[:7] != self.HEADER_BYTES:
            raise Exception("Invalid file format (Failed to parse header)")
        if header_data[7:8] != b'\x00':
            print("Warning: unknown file version. Will attempt to read it anyway")

        # read timestamp
        self.start_timestamp, = ULog._unpack_uint64(header_data[8:])

    def _read_file_definitions(self):
        header = self.MessageHeader()
        while True:
            data = self.file_handle.read(3)
            if not data:
                break
            header.initialize(data)
            data = self.file_handle.read(header.msg_size)
            if header.msg_type == self.MSG_TYPE_INFO:
                msg_info = self.MessageInfo(data, header)
                self.msg_info_dict[msg_info.key] = msg_info.value
            elif header.msg_type == self.MSG_TYPE_FORMAT:
                msg_format = self.MessageFormat(data, header)
                self.message_formats[msg_format.name] = msg_format
            elif header.msg_type == self.MSG_TYPE_PARAMETER:
                msg_info = self.MessageInfo(data, header)
                self.initial_parameters[msg_info.key] = msg_info.value
            elif (header.msg_type == self.MSG_TYPE_ADD_LOGGED_MSG or
                  header.msg_type == self.MSG_TYPE_LOGGING):
                self.file_handle.seek(-(3+header.msg_size), 1)
                break # end of section
            #else: skip

    def _read_file_data(self, message_name_filter_list):
        try:
            # pre-init reusable objects
            header = self.MessageHeader()
            msg_data = self.MessageData()

            while True:
                data = self.file_handle.read(3)
                header.initialize(data)
                data = self.file_handle.read(header.msg_size)
                if len(data) < header.msg_size:
                    break # less data than expected. File is most likely cut

                if header.msg_type == self.MSG_TYPE_PARAMETER:
                    msg_info = self.MessageInfo(data, header)
                    self.changed_parameters.append((self.last_timestamp,
                                                    msg_info.key, msg_info.value))
                elif header.msg_type == self.MSG_TYPE_ADD_LOGGED_MSG:
                    msg_add_logged = self.MessageAddLogged(data, header,
                                                           self.message_formats)
                    if (message_name_filter_list is None or
                            msg_add_logged.message_name in message_name_filter_list):
                        self.subscriptions[msg_add_logged.msg_id] = msg_add_logged
                    else:
                        self.filtered_message_ids.add(msg_add_logged.msg_id)
                elif header.msg_type == self.MSG_TYPE_LOGGING:
                    msg_logging = self.MessageLogging(data, header)
                    self.logged_messages.append(msg_logging)
                elif header.msg_type == self.MSG_TYPE_DATA:
                    msg_data.initialize(data, header, self.subscriptions, self)
                    if msg_data.timestamp != 0:
                        self.last_timestamp = msg_data.timestamp
                elif header.msg_type == self.MSG_TYPE_DROPOUT:
                    msg_dropout = self.MessageDropout(data, header,
                                                      self.last_timestamp)
                    self.dropouts.append(msg_dropout)
                #else: skip
        except struct.error:
            pass #we read past the end of the file

        # convert into final representation
        while self.subscriptions:
            _, value = self.subscriptions.popitem()
            if len(value.buffer) > 0: # only add if we have data
                data_item = ULog.Data(value)
                self.data_list.append(data_item)


    def get_version_info(self, key_name='ver_sw_release'):
        """
        get the (major, minor, patch, type) version information as tuple.
        Returns None if not found
        definition of type is:
         >= 0: development
         >= 64: alpha version
         >= 128: beta version
         >= 192: RC version
         == 255: release version
        """
        if key_name in self.msg_info_dict:
            val = self.msg_info_dict[key_name]
            return ((val >> 24) & 0xff, (val >> 16) & 0xff, (val >> 8) & 0xff, val & 0xff)
        return None

    def get_version_info_str(self, key_name='ver_sw_release'):
        """
        get version information in the form 'v1.2.3 (RC)', or None if version
        tag either not found or it's a development version
        """
        version = self.get_version_info(key_name)
        if not version is None and version[3] >= 64:
            type_str = ''
            if version[3] < 128: type_str = ' (alpha)'
            elif version[3] < 192: type_str = ' (beta)'
            elif version[3] < 255: type_str = ' (RC)'
            return 'v{}.{}.{}{}'.format(version[0], version[1], version[2], type_str)
        return None

