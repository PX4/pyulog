#! /usr/bin/env python

"""
Convert a ULog file into a ROS2 bag.
"""

from collections import defaultdict
import argparse
import re
from os import environ
from pathlib import Path
from importlib.metadata import version
import numpy as np

from .core import ULog
# from pyulog import ULog

# Do not exit on failing to import ROS2 packages so they don't block the help message.
ros2_available = True
try:
    from rclpy.serialization import serialize_message  # pylint: disable=import-error
    import rosbag2_py  # pylint: disable=import-error
except ImportError as e:
    print(
        "Error: Could not import ROS2 packages. Make sure you have sourced"
        " your ROS2 installation."
    )
    print("Actual error:", e)
    ros2_available = False

try:
    from px4_msgs import msg as px4_msgs  # pylint: disable=import-error
except ImportError as e:
    print(
        "Error: Could not import px4_msgs. Make sure you have built and sourced"
        " the correct version of px4_msgs."
    )
    print("Actual error:", e)
    ros2_available = False

# pylint: disable=too-many-locals, invalid-name


def main():
    """Command line interface"""

    parser = argparse.ArgumentParser(description="Convert ULog to rosbag")
    parser.add_argument("filename", metavar="file.ulg", help="ULog input file")

    parser.add_argument(
        "-o",
        "--output",
        dest="bag",
        help="rosbag output destination",
        default=None,
    )

    parser.add_argument(
        "-m",
        "--messages",
        dest="messages",
        help=(
            "Only consider given messages. Must be a comma-separated list of"
            " names, like 'sensor_combined,vehicle_gps_position'"
        ),
    )

    parser.add_argument(
        "-i",
        "--ignore",
        dest="ignore",
        action="store_true",
        help="Ignore string parsing exceptions",
        default=False,
    )

    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Print extra debugging information",
        default=False,
    )

    args = parser.parse_args()

    if not ros2_available:
        return  # Error messages printed in 'except ImportError' blocks above

    convert_ulog2ros2bag(
        args.filename, args.bag, args.messages, args.ignore, args.verbose
    )


# https://stackoverflow.com/questions/19053707/converting-snake-case-to-lower-camel-case-lowercamelcase
def to_camel_case(snake_str):
    """Convert snake case string to camel case"""
    components = snake_str.split("_")
    return "".join(x.title() for x in components)


def convert_ulog2ros2bag(
    ulog_file_name: str,
    rosbag_name: str | None,
    messages: str,
    disable_str_exceptions=False,
    verbose=False,
):
    """
    Coverts and ULog file to a CSV file.

    :param ulog_file_name: The ULog filename to open and read
    :param rosbag_name: The rosbag filename to open and write
    :param messages: A list of message names

    :return: No
    """

    msg_filter = messages.split(",") if messages else None

    ulog = ULog(ulog_file_name, msg_filter, disable_str_exceptions)

    multiids: dict[str, set[int]] = defaultdict(set)
    for topic in ulog.data_list:
        multiids[topic.name].add(topic.multi_id)

    # ROS2 boilerplate
    writer = rosbag2_py.SequentialWriter()

    # Default rosbag name from ulg file
    rosbag_name = rosbag_name or "rosbag_" + re.sub(
        r"\.ulg$", "", Path(ulog_file_name).name
    )

    storage_options = rosbag2_py.StorageOptions(uri=rosbag_name, storage_id="sqlite3")
    converter_options = rosbag2_py.ConverterOptions(
        input_serialization_format="cdr", output_serialization_format="cdr"
    )
    writer.open(storage_options, converter_options)

    # Support rosbag2_py topic sequence number in ROS2 versions greater than Humble
    if rosbag_write_uses_seqnum():
        rosbag_write = lambda topic, msg, timestamp: writer.write(
            topic, msg, timestamp, 0
        )
    else:
        rosbag_write = lambda topic, msg, timestamp: writer.write(topic, msg, timestamp)

    # Support rosbag2_py TopicMetadata ID in ROS2 versions greater than Humble
    if rosbag_topicmetadata_uses_id():
        topic_metadata = lambda name, type: rosbag2_py.TopicMetadata(
            0,
            name=name,  # type: ignore
            type=type,
            serialization_format="cdr",
        )
    else:
        topic_metadata = lambda name, type: rosbag2_py.TopicMetadata(
            name=name,
            type=type,
            serialization_format="cdr",
        )

    if verbose:
        print(f"I: ROS2 Distro: {environ.get('ROS_DISTRO') or 'not detected'}")
        px4_msgs_share_dir = None
        try:
            from ament_index_python.packages import (
                get_package_share_directory,
            )  # pylint: disable=import-error, import-outside-toplevel

            px4_msgs_share_dir = get_package_share_directory("px4_msgs")
        except:  # pylint: disable=bare-except
            pass
        print(f"I: ROS2 px4_msgs: {px4_msgs_share_dir or 'not found'}")
        print(
            f"I: PX4 firmware version from ulog: {ulog.get_version_info_str() or 'not found'}"
        )
        print("")

    topic_count, message_count = 0, 0
    for ulg_topic in ulog.data_list:
        topic_message_count = len(ulg_topic.data["timestamp"])

        # Determine ROS2 topic name
        if multiids[ulg_topic.name] == {0}:
            ros2_topic = f"/px4/{ulg_topic.name}"
        else:
            ros2_topic = f"/px4/{ulg_topic.name}_{ulg_topic.multi_id}"

        if verbose:
            ulg_topic_name = ulg_topic.name
            if multiids[ulg_topic.name] != {0}:
                ulg_topic_name += f" ({ulg_topic.multi_id})"
            print(
                f"D: Processing ulog topic {ulg_topic_name} with {topic_message_count}"
                f" messages and ROS2 topic {ros2_topic}"
            )

        # Determine ROS2 message type (px4_msgs)
        msg_type_name = calc_msgtype(ulg_topic.name)
        if msg_type_name is not None and hasattr(px4_msgs, msg_type_name):
            MsgType = getattr(px4_msgs, msg_type_name)
        else:
            print(
                f"W: Message type '{msg_type_name or to_camel_case(ulg_topic.name)}'"
                f" for {ulg_topic.name} not found in px4_msgs, skipping."
            )
            continue

        if verbose:
            print(f"D: Found ROS2 message type px4_msgs/msg/{MsgType.__name__}")

        # Check if it is a composed message type
        if any(
            re.match(r"(.*?)\.(.*?)", field.field_name)
            for field in ulg_topic.field_data
        ):
            # TODO: add support for composed message types
            print(f"W: Message type for {ulg_topic.name} is composed, skipping.")
            continue

        # Verify message type
        ros2_fields = MsgType.get_fields_and_field_types().keys()
        px4_fields = [
            re.sub(r"\[\d+\]$", "", data.field_name) for data in ulg_topic.field_data
        ]  # strip array indices
        px4_fields = list(set(px4_fields))  # remove duplicates
        if not all([px4_field in ros2_fields for px4_field in px4_fields]):
            print(
                f"W: Message type px4_msgs/msg/{MsgType.__name__} does not match topic"
                f" '{ulg_topic.name}' in ulog, skipping. Please check your version of px4_msgs."
            )
            if verbose:
                for px4_field in [
                    px4_field
                    for px4_field in px4_fields
                    if px4_field not in ros2_fields
                ]:
                    print(
                        f"D: field {px4_field} of {ulg_topic.name} not found in {MsgType.__name__}"
                    )
            continue

        # Register topic in rosbag
        writer.create_topic(
            topic_metadata(ros2_topic, f"px4_msgs/msg/{MsgType.__name__}")
        )

        # Write each message
        for i in range(len(ulg_topic.data["timestamp"])):
            msg = MsgType()
            for field in ulg_topic.field_data:
                array_match = re.match(r"(.*?)\[(\d+)\]", field.field_name)
                value = ulg_topic.data[field.field_name][i]
                if array_match:
                    field_name, array_index = array_match.groups()
                    array_index = int(array_index)
                    value = ros2ify_value(field_name, value, MsgType)
                    getattr(msg, field_name)[array_index] = value
                else:
                    try:
                        value = ros2ify_value(field.field_name, value, MsgType)
                        setattr(msg, field.field_name, value)
                    except Exception as e:
                        print(
                            f"Exception when setting field '{field.field_name}' from"
                            f" topic '{ulg_topic.name}' with type: {type(value)}"
                        )
                        raise e

            ts = ulg_topic.data["timestamp"][i] * 1000  # us -> ns
            rosbag_write(
                ros2_topic,
                serialize_message(msg),
                int(ts),
            )
        topic_count += 1
        message_count += topic_message_count

    writer.close()
    print(
        f"\nWrote rosbag '{rosbag_name}' with {topic_count} topics and {message_count} messages."
    )


def rosbag_topicmetadata_uses_id():
    """
    rosbag2_py PR #1538 adds a parameter to TopicMetadata.__init__() for a topic ID,
    breaking the interface. This attempts to add compability with both versions.
    """
    return version("rosbag2_py") >= "0.25.0"


def rosbag_write_uses_seqnum():
    """
    rosbag2_py commit 62e5f77 adds a parameter to SequentialWriter.write() for a
    topic sequence number, breaking the interface. This attempts to add compatibility
    with both versions.
    """
    return version("rosbag2_py") >= "0.32.0"


def calc_msgtype(topic_name: str) -> str | None:
    """Calculate message type from topic name, if possible"""

    REGEX_EXCEPTIONS = {
        r"^actuator_controls_status_\d$": "ActuatorControlsStatus",
        r"^actuator_outputs\w*": "ActuatorOutputs",
        r"^config_overrides\w*": "ConfigOverrides",
        r"^estimator_aid_src_((gnss_yaw)|(ev_yaw)|(fake_hgt)|(airspeed)|(sideslip)|(\w+_hgt))$": "EstimatorAidSource1d",  # pylint: disable=line-too-long
        r"^estimator_aid_src_((drag)|(aux_vel)|(optical_flow)|(\w+_pos)|(aux_global_position))$": "EstimatorAidSource2d",  # pylint: disable=line-too-long
        r"^estimator_aid_src_((ev_vel)|(gnss_vel)|(gravity)|(mag))$": "EstimatorAidSource3d",
        r"^estimator_ev_pos_bias": "EstimatorBias3d",
        r"^estimator_((baro)|(gnss_hgt))_bias": "EstimatorBias",
        r"^estimator_innovation\w*": "EstimatorInnovations",
        r"^px4io_status$": "Px4ioStatus",
        r"^vehicle_gps_position$": "SensorGps",
        r"^sensors_status_\w+": "SensorsStatus",
        r"^vehicle_angular_velocity\w*": "VehicleAngularVelocity",
        r"^\w+?attitude(_groundtruth)?$": "VehicleAttitude",
        r"^\w+?attitude_setpoint$": "VehicleAttitudeSetpoint",
        r"^\w+?_command\w*": "VehicleCommand",
        r"^\w+?_control_\w+": "VehicleControlMode",
        r"^((aux_)|(estimator_)|(vehicle_)|(external_ins_))global_position(_groundtruth)?$": "VehicleGlobalPosition",  # pylint: disable=line-too-long
        r"^\w+?_local_position(_groundtruth)?$": "VehicleLocalPosition",
        r"^\w+?_odometry$": "VehicleOdometry",
        r"^((estimator)|(vehicle))_optical_flow_vel$": "VehicleOpticalFlowVel",
        r"^vehicle_thrust_setpoint\w*": "VehicleThrustSetpoint",
        r"^vehicle_torque_setpoint\w*": "VehicleTorqueSetpoint",
        r"^(estimator_)?wind$": "Wind",
    }

    direct_name = to_camel_case(topic_name)
    if hasattr(px4_msgs, direct_name):  # type: ignore
        return direct_name

    result = None
    for pattern, type_name in REGEX_EXCEPTIONS.items():
        if re.match(pattern, topic_name):
            result = type_name
            break

    return result


def ros2ify_value(field_name: str, value, MsgType: object):
    """Translate a pyulog numpy value to ros2 plain python value"""
    value_type: np.signedinteger | np.unsignedinteger | np.floating = value.dtype

    # int8 could either be int8_t, bool, or char
    # check the destination type
    ros2_type: str = MsgType.get_fields_and_field_types()[field_name]  # type: ignore

    # startswith() accounts for array types
    if value_type == np.int8 and ros2_type.startswith("bool"):
        return bool(value)

    return value.item()


if __name__ == "__main__":
    main()
