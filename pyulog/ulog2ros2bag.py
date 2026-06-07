#! /usr/bin/env python

"""
Convert a ULog file into a ROS2 bag. Inspired by ulog2rosbag.py.
"""

from collections import defaultdict
import argparse
import re
from os import environ
from importlib.metadata import version
from rclpy.serialization import serialize_message  # pylint: disable=import-error
import rosbag2_py  # pylint: disable=import-error
from px4_msgs import msg as px4_msgs  # pylint: disable=import-error
import numpy as np

# TODO: temporary for typing
# from .core import ULog
from pyulog import ULog

EXCEPTIONS = {
    "estimator_attitude": "VehicleAttitude",
    "estimator_baro_bias": "EstimatorBias",
    "estimator_global_position": "VehicleGlobalPosition",
    "estimator_gnss_hgt_bias": "EstimatorBias",
    "estimator_local_position": "VehicleLocalPosition",
    "estimator_odometry": "VehicleOdometry",
    "px4io_status": "Px4ioStatus",
    "vehicle_gps_position": "SensorGps",
    "vehicle_visual_odometry": "VehicleOdometry",
}

# pylint: disable=too-many-locals, invalid-name


def main():
    """Command line interface"""

    parser = argparse.ArgumentParser(description="Convert ULog to rosbag")
    parser.add_argument("filename", metavar="file.ulg", help="ULog input file")
    parser.add_argument("bag", metavar="rosbag_file", help="rosbag output file")

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
    rosbag_name: str,
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
            )  # pylint: disable=import-error

            px4_msgs_share_dir = get_package_share_directory("px4_msgs")
        except:
            pass
        print(f"I: ROS2 px4_msgs: {px4_msgs_share_dir or 'not found'}")
        print(f"I: PX4 firmware version from ulog: {ulog.get_version_info_str()}")
        print("")

    topic_count, message_count = 0, 0
    for ulg_topic in ulog.data_list:
        topic_message_count = len(ulg_topic.data["timestamp"])

        # Determine ROS2 topic name
        if multiids[ulg_topic.name] == {0}:
            ros2_topic = "/px4/{}".format(ulg_topic.name)
        else:
            ros2_topic = "/px4/{}_{}".format(ulg_topic.name, ulg_topic.multi_id)

        if verbose:
            if multiids[ulg_topic.name] == {0}:
                ulg_topic_name = ulg_topic.name
            else:
                ulg_topic_name = f"{ulg_topic.name} ({ulg_topic.multi_id})"
            print(
                f"D: Processing ulog topic {ulg_topic_name} with {topic_message_count} messages and ROS2 topic {ros2_topic}"
            )

        # Determine ROS2 message type (px4_msgs)
        msg_type_name = calc_msgtype(ulg_topic.name)
        if msg_type_name is not None:
            MsgType = getattr(px4_msgs, msg_type_name)
        else:
            print(
                f"W: Message type '{to_camel_case(ulg_topic.name)}' for {ulg_topic.name} not found in px4_msgs, skipping."
            )
            continue

        if verbose:
            print(f"D: Found ROS2 message type px4_msgs/msg/{MsgType.__name__}")

        # Check if it is a composed message type
        if any(
            re.compile(r"(.*?)\.(.*?)").match(field.field_name)
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
                f"W: Message type px4_msgs/msg/{MsgType.__name__} does not match topic '{ulg_topic.name}' in ulog, skipping. Please check your version of px4_msgs."
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
                array_condition = re.compile(r"(.*?)\[(\d+)\]")
                array_match = array_condition.match(field.field_name)
                value = ulg_topic.data[field.field_name][i]
                if array_match:
                    field_name, array_index = array_match.groups()
                    array_index = int(array_index)
                    if value.dtype == np.int8:
                        value = bool(value)
                    getattr(msg, field_name)[array_index] = value
                else:
                    try:
                        if value.dtype == np.int8:
                            value = bool(value)
                        else:
                            value = value.item()
                        setattr(msg, field.field_name, value)
                    except Exception as e:
                        print(
                            f"Exception when setting field '{field.field_name}' from topic '{ulg_topic.name}' with type: {type(value)}"
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
    try:
        return version("rosbag2_py") >= "0.25.0"
    except:
        return False  # Default: <= Humble


def rosbag_write_uses_seqnum():
    """
    rosbag2_py commit 62e5f77 adds a parameter to SequentialWriter.write() for a
    topic sequence number, breaking the interface. This attempts to add compatibility
    with both versions.
    """
    try:
        return version("rosbag2_py") >= "0.32.0"
    except:
        return False  # Default: <= Humble


def calc_msgtype(topic_name: str) -> str | None:
    """Calculate message type from topic name, if possible"""
    direct_name = to_camel_case(topic_name)
    global EXCEPTIONS

    if hasattr(px4_msgs, direct_name):
        return direct_name
    elif topic_name.startswith("estimator_aid_src_"):
        if any(
            topic_name.endswith(suffix)
            for suffix in ["hgt", "airspeed", "slideslip", "yaw"]
        ):
            return "EstimatorAidSource1d"
        elif any(
            topic_name.endswith(suffix)
            for suffix in [
                "pos",
                "aux_global_position",
                "aux_vel",
                "optical_flow",
                "drag",
            ]
        ):
            return "EstimatorAidSource2d"
        elif any(topic_name.endswith(suffix) for suffix in ["vel", "gravity", "mag"]):
            return "EstimatorAidSource3d"
        else:
            return None
    elif topic_name.startswith("estimator_innovation"):
        return "EstimatorInnovations"
    elif topic_name in EXCEPTIONS:
        return EXCEPTIONS[topic_name]
    else:
        return None


if __name__ == "__main__":
    main()
