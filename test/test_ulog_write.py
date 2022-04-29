import os
import inspect
import unittest
import pyulog
import tempfile
from ddt import ddt, data

TEST_PATH = os.path.dirname(os.path.abspath(
    inspect.getfile(inspect.currentframe())))

@ddt
class Test(unittest.TestCase):

    @data('sample', 'sample_appended', 'sample_appended_multiple', 'sample_logging_tagged_and_default_params')
    def test_ulog_write(self, base_name):
        tmpdir = tempfile.TemporaryDirectory()
        ulog_file_name = os.path.join(TEST_PATH, base_name + '.ulg')
        written_ulog_file_name = os.path.join(tmpdir.name, base_name + '_copy.ulg')

        original = pyulog.ULog(ulog_file_name)
        original.write_ulog(written_ulog_file_name)
        copied = pyulog.ULog(written_ulog_file_name)

        # Check first and last timestamps
        assert original.start_timestamp == copied.start_timestamp
        assert original.last_timestamp == copied.last_timestamp

        # Check flag bitset message 'B'
        assert original._compat_flags == copied._compat_flags
        if original.has_data_appended:
            # Data is not appended when using write_ulog(). Add the flag manually.
            copied._incompat_flags[0] = copied._incompat_flags[0] | 0x01
        assert original._incompat_flags == copied._incompat_flags

        # Check format definitions 'F'
        assert original.message_formats == copied.message_formats

        # Check information messages 'I'
        assert original.msg_info_dict == copied.msg_info_dict

        # Check information message multi 'M'
        assert original.msg_info_multiple_dict == copied.msg_info_multiple_dict

        # Check initial parameters 'P'
        assert original.initial_parameters == copied.initial_parameters

        # Check default parameters 'Q'
        assert original.has_default_parameters == copied.has_default_parameters
        assert original._default_parameters == copied._default_parameters

        # Check data 'A'/'D'
        assert original.data_list == copied.data_list

        # Check logged string messages 'L'
        assert original.logged_messages == copied.logged_messages

        # Check tagged logged string message 'C'
        assert original.logged_messages_tagged == copied.logged_messages_tagged

        # Check dropouts 'O'
        assert original.dropouts == copied.dropouts

        # Check changed parameters 'P'
        assert original.changed_parameters == copied.changed_parameters

# vim: set et fenc=utf-8 ft=python ff=unix sts=4 sw=4 ts=4 : 
