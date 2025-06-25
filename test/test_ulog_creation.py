"""
Tests for ULog creation and editing functionality
"""

import os
import tempfile
import unittest
from io import BytesIO

import pyulog


class TestULogCreation(unittest.TestCase):
    """
    Tests for creating and editing ULog files
    """
    
    def _create_test_ulog(self):
        """Helper method to create a test ULog instance."""
        return pyulog.ULog.create(
            sys_name='PX4',
            ver_hw='TEST',
            ver_sw='v1.0.0'
        )

    def test_create_empty_ulog(self):
        """Test creating an empty ULog with standard header info."""
        ulog = pyulog.ULog.create(
            sys_name='PX4',
            ver_hw='SITL', 
            ver_sw='v1.0.0-dev',
            ver_sw_release=0x010000FF
        )
        
        # Check that standard info messages are present
        self.assertIn('sys_name', ulog.msg_info_dict)
        self.assertEqual(ulog.msg_info_dict['sys_name'], 'PX4')
        
        self.assertIn('ver_hw', ulog.msg_info_dict)
        self.assertEqual(ulog.msg_info_dict['ver_hw'], 'SITL')
        
        self.assertIn('ver_sw', ulog.msg_info_dict)
        self.assertEqual(ulog.msg_info_dict['ver_sw'], 'v1.0.0-dev')
        
        self.assertIn('ver_sw_release', ulog.msg_info_dict)
        self.assertEqual(ulog.msg_info_dict['ver_sw_release'], 0x010000FF)
        
        self.assertIn('time_ref_utc', ulog.msg_info_dict)
        self.assertEqual(ulog.msg_info_dict['time_ref_utc'], 0)
        
        # Check timestamps are set
        self.assertGreater(ulog.start_timestamp, 0)
        self.assertEqual(ulog.last_timestamp, ulog.start_timestamp)

    def test_add_info_message(self):
        """Test adding custom info messages."""
        ulog = pyulog.ULog.create(
            sys_name='PX4',
            ver_hw='TEST',
            ver_sw='v1.0.0'
        )
        
        # Add custom info message
        ulog.add_info_message('char[32] custom_info', 'test_value')
        
        self.assertIn('custom_info', ulog.msg_info_dict)
        self.assertEqual(ulog.msg_info_dict['custom_info'], 'test_value')
        self.assertEqual(ulog._msg_info_dict_types['custom_info'], 'char[32]')

    def test_add_info_message_invalid_key(self):
        """Test adding info message with invalid key format."""
        ulog = pyulog.ULog.create(
            sys_name='PX4',
            ver_hw='TEST',
            ver_sw='v1.0.0'
        )
        
        with self.assertRaises(ValueError):
            ulog.add_info_message('invalid_key', 'value')

    def test_add_message_format(self):
        """Test adding a message format definition."""
        ulog = pyulog.ULog.create(
            sys_name='PX4',
            ver_hw='TEST',
            ver_sw='v1.0.0'
        )
        
        # Add a simple message format
        fields = [
            ('uint64_t', 0, 'timestamp'),
            ('float', 0, 'x'),
            ('float', 0, 'y'),
            ('float', 0, 'z')
        ]
        ulog.add_message_format('position', fields)
        
        # Check format was added
        self.assertIn('position', ulog.message_formats)
        msg_format = ulog.message_formats['position']
        self.assertEqual(msg_format.name, 'position')
        self.assertEqual(len(msg_format.fields), 4)
        self.assertEqual(msg_format.fields[0], ('uint64_t', 0, 'timestamp'))
        self.assertEqual(msg_format.fields[1], ('float', 0, 'x'))

    def test_add_message_format_with_arrays(self):
        """Test adding a message format with array fields."""
        ulog = pyulog.ULog.create(
            sys_name='PX4',
            ver_hw='TEST',
            ver_sw='v1.0.0'
        )
        
        fields = [
            ('uint64_t', 0, 'timestamp'),
            ('float', 3, 'position'),  # Array of 3 floats
            ('uint8_t', 4, 'status')   # Array of 4 uint8_t
        ]
        ulog.add_message_format('sensor_data', fields)
        
        self.assertIn('sensor_data', ulog.message_formats)
        msg_format = ulog.message_formats['sensor_data']
        self.assertEqual(msg_format.fields[1], ('float', 3, 'position'))
        self.assertEqual(msg_format.fields[2], ('uint8_t', 4, 'status'))

    def test_add_message_format_invalid_name(self):
        """Test adding message format with invalid name."""
        ulog = pyulog.ULog.create(
            sys_name='PX4',
            ver_hw='TEST',
            ver_sw='v1.0.0'
        )
        
        fields = [('uint64_t', 0, 'timestamp')]
        
        with self.assertRaises(ValueError):
            ulog.add_message_format('', fields)
        
        with self.assertRaises(ValueError):
            ulog.add_message_format(None, fields)

    def test_add_message_format_invalid_fields(self):
        """Test adding message format with invalid fields."""
        ulog = pyulog.ULog.create(
            sys_name='PX4',
            ver_hw='TEST',
            ver_sw='v1.0.0'
        )
        
        with self.assertRaises(ValueError):
            ulog.add_message_format('test', [])
        
        with self.assertRaises(ValueError):
            ulog.add_message_format('test', None)
        
        with self.assertRaises(ValueError):
            ulog.add_message_format('test', [('uint64_t', 0)])  # Missing field name

    def test_add_data_message(self):
        """Test adding data messages."""
        ulog = pyulog.ULog.create(
            sys_name='PX4',
            ver_hw='TEST',
            ver_sw='v1.0.0'
        )
        
        # Add message format first
        fields = [
            ('uint64_t', 0, 'timestamp'),
            ('float', 0, 'x'),
            ('float', 0, 'y'),
            ('float', 0, 'z')
        ]
        ulog.add_message_format('position', fields)
        
        # Add data message
        timestamp = ulog.start_timestamp + 1000000  # 1 second later
        ulog.add_data_message('position', timestamp=timestamp, x=1.0, y=2.0, z=3.0)
        
        # Check that subscription was created
        self.assertEqual(len(ulog._subscriptions), 1)
        subscription = list(ulog._subscriptions.values())[0]
        self.assertEqual(subscription.message_name, 'position')
        self.assertEqual(subscription.multi_id, 0)
        self.assertGreater(len(subscription.buffer), 0)
        
        # Check timestamp was updated
        self.assertEqual(ulog.last_timestamp, timestamp)

    def test_add_data_message_auto_timestamp(self):
        """Test adding data message with automatic timestamp."""
        ulog = self._create_test_ulog()
        
        fields = [('uint64_t', 0, 'timestamp'), ('float', 0, 'value')]
        ulog.add_message_format('test_msg', fields)
        
        initial_timestamp = ulog.last_timestamp
        ulog.add_data_message('test_msg', value=42.0)
        
        # Timestamp should remain the same since we didn't provide one
        self.assertEqual(ulog.last_timestamp, initial_timestamp)

    def test_add_data_message_unknown_format(self):
        """Test adding data message for unknown format."""
        ulog = self._create_test_ulog()
        
        with self.assertRaises(ValueError):
            ulog.add_data_message('unknown_format', timestamp=123456, value=1.0)

    def test_add_data_message_unknown_field(self):
        """Test adding data message with unknown field."""
        ulog = self._create_test_ulog()
        
        fields = [('uint64_t', 0, 'timestamp'), ('float', 0, 'x')]
        ulog.add_message_format('position', fields)
        
        with self.assertRaises(ValueError):
            ulog.add_data_message('position', timestamp=123456, x=1.0, unknown_field=2.0)

    def test_add_data_message_missing_required_fields(self):
        """Test adding data message with missing required fields."""
        ulog = self._create_test_ulog()
        
        fields = [('uint64_t', 0, 'timestamp'), ('float', 0, 'x'), ('float', 0, 'y')]
        ulog.add_message_format('position', fields)
        
        # Test missing one field
        with self.assertRaises(ValueError):
            ulog.add_data_message('position', timestamp=123456, x=1.0)  # missing y
        
        # Test missing multiple fields
        with self.assertRaises(ValueError):
            ulog.add_data_message('position', timestamp=123456)  # missing x and y
        
        # Test missing all fields
        with self.assertRaises(ValueError):
            ulog.add_data_message('position')  # missing all fields

    def test_write_created_ulog(self):
        """Test writing a created ULog to file."""
        ulog = self._create_test_ulog()
        
        # Add a message format and some data
        fields = [
            ('uint64_t', 0, 'timestamp'),
            ('float', 0, 'temperature'),
            ('uint32_t', 0, 'sensor_id')
        ]
        ulog.add_message_format('sensor_reading', fields)
        
        # Add multiple data points
        base_time = ulog.start_timestamp
        for i in range(5):
            ulog.add_data_message(
                'sensor_reading',
                timestamp=base_time + i * 100000,  # 100ms intervals
                temperature=20.0 + i * 0.5,
                sensor_id=1
            )
        
        # Write to memory buffer
        with BytesIO() as buffer:
            ulog.write_ulog(buffer)
            buffer.seek(0)
            
            # Read back and verify
            read_ulog = pyulog.ULog(buffer)
            
            # Check info messages
            self.assertEqual(read_ulog.msg_info_dict['sys_name'], 'PX4')
            
            # Check message format
            self.assertIn('sensor_reading', read_ulog.message_formats)
            
            # Check data
            self.assertEqual(len(read_ulog.data_list), 1)
            data = read_ulog.data_list[0]
            self.assertEqual(data.name, 'sensor_reading')
            self.assertEqual(len(data.data['timestamp']), 5)
            self.assertEqual(data.data['temperature'][0], 20.0)
            self.assertEqual(data.data['temperature'][4], 22.0)

    def test_write_created_ulog_to_file(self):
        """Test writing a created ULog to an actual file."""
        ulog = self._create_test_ulog()
        
        # Add some content
        fields = [('uint64_t', 0, 'timestamp'), ('int32_t', 0, 'counter')]
        ulog.add_message_format('counter_msg', fields)
        
        for i in range(3):
            ulog.add_data_message(
                'counter_msg',
                timestamp=ulog.start_timestamp + i * 50000,
                counter=i
            )
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(suffix='.ulg', delete=False) as tmp_file:
            tmp_filename = tmp_file.name
        
        try:
            ulog.write_ulog(tmp_filename)
            
            # Verify file exists and can be read
            self.assertTrue(os.path.exists(tmp_filename))
            
            # Read back and verify content
            read_ulog = pyulog.ULog(tmp_filename)
            self.assertEqual(len(read_ulog.data_list), 1)
            self.assertEqual(read_ulog.data_list[0].name, 'counter_msg')
            self.assertEqual(len(read_ulog.data_list[0].data['counter']), 3)
            
        finally:
            # Clean up
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)

    def test_multi_instance_messages(self):
        """Test adding messages with multiple instances."""
        ulog = self._create_test_ulog()
        
        fields = [('uint64_t', 0, 'timestamp'), ('float', 0, 'value')]
        ulog.add_message_format('sensor', fields)
        
        # Add data for two different sensor instances
        base_time = ulog.start_timestamp
        ulog.add_data_message('sensor', multi_id=0, timestamp=base_time, value=10.0)
        ulog.add_data_message('sensor', multi_id=1, timestamp=base_time, value=20.0)
        
        # Should have two subscriptions
        self.assertEqual(len(ulog._subscriptions), 2)
        
        # Write and read back
        with BytesIO() as buffer:
            ulog.write_ulog(buffer)
            buffer.seek(0)
            read_ulog = pyulog.ULog(buffer)
            
            # Should have two data sets
            self.assertEqual(len(read_ulog.data_list), 2)
            
            # Check multi_ids
            multi_ids = {data.multi_id for data in read_ulog.data_list}
            self.assertEqual(multi_ids, {0, 1})

    def test_complex_message_format(self):
        """Test creating a complex message format with various field types."""
        ulog = self._create_test_ulog()
        
        fields = [
            ('uint64_t', 0, 'timestamp'),
            ('float', 3, 'position'),      # Array of 3 floats
            ('double', 0, 'altitude'),     # Double precision
            ('int32_t', 0, 'mode'),        # Signed integer
            ('uint16_t', 4, 'channels'),   # Array of 4 uint16
            ('bool', 0, 'armed'),          # Boolean
            ('uint8_t', 0, 'battery_pct')  # Percentage
        ]
        ulog.add_message_format('vehicle_status', fields)
        
        # Add data message with all field types
        ulog.add_data_message(
            'vehicle_status',
            timestamp=ulog.start_timestamp + 1000000,
            position=[1.0, 2.0, 3.0],  # This should be handled as separate fields
            altitude=100.5,
            mode=2,
            channels=[1500, 1600, 1700, 1800],  # This should be handled as separate fields
            armed=True,
            battery_pct=85
        )
        
        # Write and verify
        with BytesIO() as buffer:
            ulog.write_ulog(buffer)
            buffer.seek(0)
            read_ulog = pyulog.ULog(buffer)
            
            self.assertEqual(len(read_ulog.data_list), 1)
            data = read_ulog.data_list[0]
            self.assertEqual(data.name, 'vehicle_status')

    def test_create_with_additional_info(self):
        """Test creating ULog with additional info messages."""
        ulog = pyulog.ULog.create(
            sys_name='ArduPilot',
            ver_hw='Pixhawk4',
            ver_sw='v4.2.0',
            start_timestamp=1234567890000000,
            time_ref_utc=-3600,
            ver_sw_release=0x040200FF,
            mission_name='test_flight',
            pilot_name='John Doe',
            flight_number=42
        )
        
        # Check required fields
        self.assertEqual(ulog.msg_info_dict['sys_name'], 'ArduPilot')
        self.assertEqual(ulog.msg_info_dict['ver_hw'], 'Pixhawk4')
        self.assertEqual(ulog.msg_info_dict['ver_sw'], 'v4.2.0')
        self.assertEqual(ulog.msg_info_dict['time_ref_utc'], -3600)
        self.assertEqual(ulog.msg_info_dict['ver_sw_release'], 0x040200FF)
        
        # Check additional fields
        self.assertEqual(ulog.msg_info_dict['mission_name'], 'test_flight')
        self.assertEqual(ulog.msg_info_dict['pilot_name'], 'John Doe')
        self.assertEqual(ulog.msg_info_dict['flight_number'], 42)
        
        # Check timestamp
        self.assertEqual(ulog.start_timestamp, 1234567890000000)

    def test_create_missing_required_params(self):
        """Test that create() requires all mandatory parameters."""
        with self.assertRaises(TypeError):
            pyulog.ULog.create()  # Missing required parameters
        
        with self.assertRaises(TypeError):
            pyulog.ULog.create(sys_name='PX4')  # Missing ver_hw and ver_sw

    def test_add_data_bulk_list_format(self):
        """Test bulk data addition using list of dictionaries format."""
        ulog = self._create_test_ulog()
        
        # Add message format
        fields = [
            ('uint64_t', 0, 'timestamp'),
            ('float', 0, 'temperature'),
            ('uint16_t', 0, 'sensor_id')
        ]
        ulog.add_message_format('sensor_data', fields)
        
        # Prepare bulk data as list of dictionaries
        base_time = ulog.start_timestamp
        bulk_data = []
        for i in range(100):  # 100 samples
            bulk_data.append({
                'timestamp': base_time + i * 10000,  # 10ms intervals
                'temperature': 20.0 + i * 0.1,
                'sensor_id': 1
            })
        
        # Add bulk data
        ulog.add_data_bulk('sensor_data', bulk_data)
        
        # Verify subscription was created and has data
        self.assertEqual(len(ulog._subscriptions), 1)
        subscription = list(ulog._subscriptions.values())[0]
        self.assertEqual(subscription.message_name, 'sensor_data')
        self.assertGreater(len(subscription.buffer), 0)
        
        # Verify timestamp was updated
        expected_last_time = base_time + 99 * 10000
        self.assertEqual(ulog.last_timestamp, expected_last_time)

    def test_add_data_bulk_dict_format(self):
        """Test bulk data addition using dictionary of lists format."""
        ulog = self._create_test_ulog()
        
        # Add message format
        fields = [
            ('uint64_t', 0, 'timestamp'),
            ('float', 0, 'x'),
            ('float', 0, 'y'),
            ('float', 0, 'z')
        ]
        ulog.add_message_format('position', fields)
        
        # Prepare bulk data as dictionary of lists
        base_time = ulog.start_timestamp
        timestamps = [base_time + i * 20000 for i in range(50)]  # 50 samples, 20ms intervals
        x_values = [i * 0.1 for i in range(50)]
        y_values = [i * 0.2 for i in range(50)]
        z_values = [i * 0.05 for i in range(50)]
        
        bulk_data = {
            'timestamp': timestamps,
            'x': x_values,
            'y': y_values,
            'z': z_values
        }
        
        # Add bulk data
        ulog.add_data_bulk('position', bulk_data)
        
        # Verify data was added
        self.assertEqual(len(ulog._subscriptions), 1)
        subscription = list(ulog._subscriptions.values())[0]
        self.assertEqual(subscription.message_name, 'position')
        
        # Verify timestamp
        expected_last_time = base_time + 49 * 20000
        self.assertEqual(ulog.last_timestamp, expected_last_time)

    def test_add_data_bulk_with_arrays(self):
        """Test bulk data addition with array fields."""
        ulog = self._create_test_ulog()
        
        # Add message format with arrays
        fields = [
            ('uint64_t', 0, 'timestamp'),
            ('float', 3, 'position'),  # Array of 3 floats
            ('uint16_t', 4, 'channels') # Array of 4 uint16
        ]
        ulog.add_message_format('complex_data', fields)
        
        # Prepare bulk data with arrays
        base_time = ulog.start_timestamp
        bulk_data = []
        for i in range(10):
            bulk_data.append({
                'timestamp': base_time + i * 50000,
                'position': [i * 0.1, i * 0.2, i * 0.3],
                'channels': [1500 + i, 1600 + i, 1700 + i, 1800 + i]
            })
        
        # Add bulk data
        ulog.add_data_bulk('complex_data', bulk_data)
        
        # Verify data was added
        self.assertEqual(len(ulog._subscriptions), 1)
        subscription = list(ulog._subscriptions.values())[0]
        self.assertEqual(subscription.message_name, 'complex_data')

    def test_add_data_bulk_multi_instance(self):
        """Test bulk data addition with multiple instances."""
        ulog = self._create_test_ulog()
        
        # Add message format
        fields = [('uint64_t', 0, 'timestamp'), ('float', 0, 'value')]
        ulog.add_message_format('sensor', fields)
        
        # Add bulk data for instance 0
        base_time = ulog.start_timestamp
        bulk_data_0 = [
            {'timestamp': base_time + i * 10000, 'value': i * 1.0}
            for i in range(5)
        ]
        ulog.add_data_bulk('sensor', bulk_data_0, multi_id=0)
        
        # Add bulk data for instance 1
        bulk_data_1 = [
            {'timestamp': base_time + i * 10000, 'value': i * 2.0}
            for i in range(5)
        ]
        ulog.add_data_bulk('sensor', bulk_data_1, multi_id=1)
        
        # Should have two subscriptions
        self.assertEqual(len(ulog._subscriptions), 2)

    def test_add_data_bulk_invalid_format(self):
        """Test bulk data addition with invalid input formats."""
        ulog = self._create_test_ulog()
        
        fields = [('uint64_t', 0, 'timestamp'), ('float', 0, 'value')]
        ulog.add_message_format('test_msg', fields)
        
        # Test invalid data_list type
        with self.assertRaises(ValueError):
            ulog.add_data_bulk('test_msg', "invalid_format")
        
        # Test mismatched list lengths in dict format
        with self.assertRaises(ValueError):
            ulog.add_data_bulk('test_msg', {
                'timestamp': [1, 2, 3],
                'value': [1.0, 2.0]  # Different length
            })

    def test_add_data_bulk_unknown_fields(self):
        """Test bulk data addition with unknown fields."""
        ulog = self._create_test_ulog()
        
        fields = [('uint64_t', 0, 'timestamp'), ('float', 0, 'x')]
        ulog.add_message_format('position', fields)
        
        # Test unknown field in list format
        bulk_data = [
            {'timestamp': 1000, 'x': 1.0, 'unknown_field': 2.0}
        ]
        
        with self.assertRaises(ValueError):
            ulog.add_data_bulk('position', bulk_data)

    def test_add_data_bulk_missing_required_fields(self):
        """Test bulk data addition with missing required fields."""
        ulog = self._create_test_ulog()
        
        fields = [('uint64_t', 0, 'timestamp'), ('float', 0, 'x'), ('float', 0, 'y')]
        ulog.add_message_format('position', fields)
        
        # Test missing field in list format
        bulk_data = [
            {'timestamp': 1000, 'x': 1.0}  # missing y
        ]
        with self.assertRaises(ValueError):
            ulog.add_data_bulk('position', bulk_data)
        
        # Test missing field in dict format
        bulk_data_dict = {
            'timestamp': [1000, 2000],
            'x': [1.0, 2.0]
            # missing y
        }
        with self.assertRaises(ValueError):
            ulog.add_data_bulk('position', bulk_data_dict)
        
        # Test completely empty data (should be allowed as no-op)
        ulog.add_data_bulk('position', [])  # Should not raise an error

    def test_add_data_bulk_write_read_roundtrip(self):
        """Test bulk data addition with write/read roundtrip."""
        ulog = self._create_test_ulog()
        
        # Add message format
        fields = [
            ('uint64_t', 0, 'timestamp'),
            ('float', 0, 'temperature'),
            ('float', 3, 'acceleration')
        ]
        ulog.add_message_format('imu_data', fields)
        
        # Add bulk data
        base_time = ulog.start_timestamp
        bulk_data = {
            'timestamp': [base_time + i * 5000 for i in range(20)],  # 5ms intervals
            'temperature': [25.0 + i * 0.1 for i in range(20)],
            'acceleration': [[i * 0.1, i * 0.2, i * 0.3] for i in range(20)]
        }
        
        ulog.add_data_bulk('imu_data', bulk_data)
        
        # Write and read back
        with BytesIO() as buffer:
            ulog.write_ulog(buffer)
            buffer.seek(0)
            read_ulog = pyulog.ULog(buffer)
            
            # Verify data
            self.assertEqual(len(read_ulog.data_list), 1)
            data = read_ulog.data_list[0]
            self.assertEqual(data.name, 'imu_data')
            self.assertEqual(len(data.data['timestamp']), 20)
            
            # Check some values
            self.assertEqual(data.data['temperature'][0], 25.0)
            self.assertEqual(data.data['temperature'][19], 25.0 + 19 * 0.1)
            
            # Check array fields
            self.assertEqual(data.data['acceleration[0]'][0], 0.0)
            self.assertEqual(data.data['acceleration[1]'][19], 19 * 0.2)

    def test_add_data_bulk_empty_data(self):
        """Test bulk data addition with empty data."""
        ulog = self._create_test_ulog()
        
        fields = [('uint64_t', 0, 'timestamp'), ('float', 0, 'value')]
        ulog.add_message_format('test_msg', fields)
        
        # Empty list should not create subscription
        ulog.add_data_bulk('test_msg', [])
        self.assertEqual(len(ulog._subscriptions), 0)
        
        # Empty dict should not create subscription
        ulog.add_data_bulk('test_msg', {})
        self.assertEqual(len(ulog._subscriptions), 0)


if __name__ == '__main__':
    unittest.main()