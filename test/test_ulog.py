'''
Tests the ULog class
'''

import os
import inspect
import unittest
import tempfile
import struct
from io import BytesIO

from ddt import ddt, data

import pyulog

TEST_PATH = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))

@ddt
class TestULog(unittest.TestCase):
    '''
    Tests the ULog class
    '''

    @data('sample')
    def test_comparison(self, base_name):
        '''
        Test that the custom comparison method works as expected.
        '''
        ulog_file_name = os.path.join(TEST_PATH, base_name + '.ulg')
        ulog1 = pyulog.ULog(ulog_file_name)
        ulog2 = pyulog.ULog(ulog_file_name)
        assert ulog1 == ulog2
        assert ulog1 is not ulog2

        # make them different in arbitrary field
        ulog1.data_list[0].data['timestamp'][0] += 1
        assert ulog1 != ulog2


    @data('sample',
          'sample_appended',
          'sample_appended_multiple',
          'sample_logging_tagged_and_default_params')
    def test_write_ulog(self, base_name):
        '''
        Test that the write_ulog method successfully replicates all relevant data.
        '''
        with tempfile.TemporaryDirectory() as tmpdirname:
            ulog_file_name = os.path.join(TEST_PATH, base_name + '.ulg')
            written_ulog_file_name = os.path.join(tmpdirname, base_name + '_copy.ulg')

            original = pyulog.ULog(ulog_file_name)
            original.write_ulog(written_ulog_file_name)
            copied = pyulog.ULog(written_ulog_file_name)

        # Some fields are not copied but dropped, so we cheat by modifying the original
        original._sync_seq_cnt = 0  # pylint: disable=protected-access
        original._appended_offsets = []  # pylint: disable=protected-access
        original._incompat_flags[0] &= 0xFE  # pylint: disable=protected-access

        assert copied == original

    @data('sample')
    def test_write_ulog_memory(self, base_name):
        '''
        Test that the write_ulog method can write bytes to memory.
        '''
        ulog_file_name = os.path.join(TEST_PATH, base_name + '.ulg')
        original = pyulog.ULog(ulog_file_name)
        with BytesIO() as bytes_handle:
            original.write_ulog(bytes_handle)
            bytes_handle.seek(0)
            copied = pyulog.ULog(bytes_handle)

        for original_key, original_value in original.__dict__.items():
            copied_value = getattr(copied, original_key)
            if original_key == '_sync_seq_cnt':
                # Sync messages are counted on parse, but otherwise dropped, so
                # we don't rewrite them
                assert copied_value == 0
            elif original_key == '_appended_offsets':
                # Abruptly ended messages just before offsets are dropped, so
                # we don't rewrite appended offsets
                assert copied_value == []
            elif original_key == '_incompat_flags':
                # Same reasoning on incompat_flags[0] as for '_appended_offsets'
                assert copied_value[0] == original_value[0] & 0xFE # pylint: disable=unsubscriptable-object
                assert copied_value[1:] == original_value[1:] # pylint: disable=unsubscriptable-object
            else:
                assert copied_value == original_value

    @staticmethod
    def _build_ulog(*messages):
        '''
        Build a minimal ULog file in memory from (msg_type, payload) tuples.
        '''
        content = pyulog.ULog.HEADER_BYTES + b'\x01' + struct.pack('<Q', 0)
        for msg_type, payload in messages:
            content += struct.pack('<HB', len(payload), ord(msg_type)) + payload
        return BytesIO(content)

    def test_invalid_header(self):
        '''
        Test that a file with an invalid header raises a ULogException.
        '''
        for content in [b'ULog', b'\x00' * 16]:
            with self.assertRaises(pyulog.ULogException):
                pyulog.ULog(BytesIO(content))

    @data(b'\x02' + bytes(7), # unknown flag in the first byte
          b'\x00\x01' + bytes(6)) # any flag in the other bytes
    def test_unknown_incompat_flag(self, incompat_flags):
        '''
        Test that an unknown incompatible flag raises a ULogIncompatibleFlagException.
        '''
        flag_bits = bytes(8) + incompat_flags + bytes(3 * 8)
        with self.assertRaises(pyulog.ULogIncompatibleFlagException):
            pyulog.ULog(self._build_ulog(('B', flag_bits)))

    def test_corrupt_definitions(self):
        '''
        Test that malformed definitions are flagged as file corruption instead of raising.
        '''
        invalid_array_size = b'foo:uint8_t[x] a;'
        bogus_appended_offset = bytes(8) + b'\x01' + bytes(7) + struct.pack('<QQQ', 1 << 63, 0, 0)
        for msg_type, payload in [('F', invalid_array_size), ('B', bogus_appended_offset)]:
            ulog = pyulog.ULog(self._build_ulog((msg_type, payload)))
            assert ulog.file_corruption

    def test_strict_string_parsing(self):
        '''
        Test that string parsing errors still raise with disable_str_exceptions=False,
        both for an info message (definitions) and a logged string (data section).
        '''
        info = bytes([10]) + b'char[2] ab' + b'\xff\xfe'
        logged_string = b'6' + bytes(8) + b'\xff\xfe'
        for msg_type, payload in [('I', info), ('L', logged_string)]:
            with self.assertRaises(UnicodeDecodeError):
                pyulog.ULog(self._build_ulog((msg_type, payload)), disable_str_exceptions=False)
            assert not pyulog.ULog(self._build_ulog((msg_type, payload))).file_corruption

class TestDataStringFields(unittest.TestCase):
    '''
    Tests the ULog.Data helpers that combine char array fields into strings.
    '''

    def _make_data(self, field_data, data):
        ''' Build a ULog.Data object without going through a log file. '''
        data_obj = object.__new__(pyulog.ULog.Data)
        data_obj.name = 'test_topic'
        data_obj.field_data = [pyulog.ULog._FieldData(name, type_str)  # pylint: disable=protected-access
                               for name, type_str in field_data]
        data_obj.data = data
        return data_obj

    def test_string_field_from_log_file(self):
        '''
        The transponder_report topic of the px4 events sample log has a
        char[9] 'callsign' field, stored as 9 individual columns.
        '''
        ulog_file_name = os.path.join(TEST_PATH, 'sample_px4_events.ulg')
        ulog = pyulog.ULog(ulog_file_name)
        data = [d for d in ulog.data_list if d.name == 'transponder_report'][0]
        assert data.list_string_fields() == ['callsign']
        strings = data.get_string_field('callsign')
        assert len(strings) == len(data.data['timestamp'])
        # compare against a manual combination of the char columns
        columns = [data.data['callsign[{}]'.format(i)] for i in range(9)]
        for sample, string in enumerate(strings):
            raw = bytes(int(column[sample]) & 0xff for column in columns)
            assert string == raw.split(b'\x00', 1)[0].decode('utf-8', 'replace')

    def test_string_field_conversion(self):
        ''' Char columns are joined per sample and cut at the first NUL. '''
        import numpy as np
        # 2 samples of a char[5] field: 'ab' (NUL-padded), then a sample
        # with an invalid utf-8 byte: 'c\xffd'
        sample_bytes = [b'ab\x00zz', bytes([0x63, 0xff, 0x64, 0x00, 0x00])]
        columns = {}
        for i in range(5):
            column = np.array([sample[i] for sample in sample_bytes],
                              dtype=np.uint8)
            columns['text[{}]'.format(i)] = column.view(np.int8)
        field_data = [('text[{}]'.format(i), 'char') for i in range(5)]
        data_obj = self._make_data(field_data, columns)
        assert data_obj.list_string_fields() == ['text']
        strings = data_obj.get_string_field('text')
        assert list(strings) == ['ab', 'c\ufffdd']

    def test_plain_char_and_non_char_fields(self):
        ''' A plain char field is a 1-char string field; other types are not
        string fields and requesting them raises a KeyError. '''
        import numpy as np
        field_data = [('timestamp', 'uint64_t'), ('flag', 'char')]
        data = {'timestamp': np.array([1, 2], dtype=np.uint64),
                'flag': np.array([ord('y'), ord('n')], dtype=np.int8)}
        data_obj = self._make_data(field_data, data)
        assert data_obj.list_string_fields() == ['flag']
        assert list(data_obj.get_string_field('flag')) == ['y', 'n']
        with self.assertRaises(KeyError):
            data_obj.get_string_field('timestamp')
        with self.assertRaises(KeyError):
            data_obj.get_string_field('does_not_exist')


# vim: set et fenc=utf-8 ft=python ff=unix sts=4 sw=4 ts=4
