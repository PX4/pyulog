""" Event parsing """
import json
import lzma
import urllib.request
from typing import Optional, Callable, Any, List, Tuple

from .libevents_parse.parser import Parser
from .core import ULog


class PX4Events:
    """ class to extract events from logs and combine them with metadata to get the messages """

    DEFAULT_EVENTS_URL = \
        'https://px4-travis.s3.amazonaws.com/Firmware/master/_general/all_events.json.xz'

    def __init__(self):
        self._events_profile = 'dev'
        self._default_parser: Optional[Parser] = None
        self._get_default_json_def_cb = self._get_default_json_definitions

    @staticmethod
    def _get_default_json_definitions(already_has_default_parser: bool) -> Optional[Any]:
        """ Default implementation for retrieving the default json event definitions """

        # If it already exists, return it to avoid re-downloading
        if already_has_default_parser:
            return None

        with urllib.request.urlopen(PX4Events.DEFAULT_EVENTS_URL, timeout=4) as response:
            data = response.read()
            return json.loads(lzma.decompress(data))

    def set_default_json_definitions_cb(self,
        default_json_definitions_cb: Callable[[bool], Optional[Any]]):
        """ Set the callback to retrieve the default event definitions json
         data (can be used for caching) """
        self._get_default_json_def_cb = default_json_definitions_cb

    def _get_event_parser(self, ulog: ULog) -> Optional[Parser]:
        """ get event parser instance or None on error """

        if 'metadata_events' in ulog.msg_info_multiple_dict and \
                'metadata_events_sha256' in ulog.msg_info_dict:
            file_hash = ulog.msg_info_dict['metadata_events_sha256']
            if len(file_hash) <= 64 and file_hash.isalnum():
                events_metadata = ulog.msg_info_multiple_dict['metadata_events'][0]
                event_definitions_json = json.loads(lzma.decompress(b''.join(events_metadata)))
                parser = Parser()
                parser.load_definitions(event_definitions_json)
                parser.set_profile(self._events_profile)
                return parser

        # No json definitions in the log -> use default definitions
        json_definitions = self._get_default_json_def_cb(
            self._default_parser is not None)
        if json_definitions is not None:
            self._default_parser = Parser()
            self._default_parser.load_definitions(json_definitions)
            self._default_parser.set_profile(self._events_profile)

        return self._default_parser

    def get_logged_events(self, ulog: ULog) -> List[Tuple[int, str, str]]:
        """
        Get the events as list of messages
        :return: list of (timestamp, log level str, message) tuples
        """

        def event_log_level_str(log_level: int):
            return {0: 'EMERGENCY',
                    1: 'ALERT',
                    2: 'CRITICAL',
                    3: 'ERROR',
                    4: 'WARNING',
                    5: 'NOTICE',
                    6: 'INFO',
                    7: 'DEBUG',
                    8: 'PROTOCOL',
                    9: 'DISABLED'}.get(log_level, 'UNKNOWN')

        # Parse events
        messages = []
        try:
            events = ulog.get_dataset('event')
            all_ids = events.data['id']

            if len(all_ids) == 0:
                return []

            # Get the parser
            try:
                event_parser = self._get_event_parser(ulog)
            except Exception as exception:  # pylint: disable=broad-exception-caught
                print('Failed to get event parser: {}'.format(exception))
                return []

            for event_idx, event_id in enumerate(all_ids):
                log_level = (events.data['log_levels'][event_idx] >> 4) & 0xf
                if log_level >= 8:
                    continue
                args = []
                i = 0
                while True:
                    arg_str = 'arguments[{}]'.format(i)
                    if arg_str not in events.data:
                        break
                    arg = events.data[arg_str][event_idx]
                    args.append(arg)
                    i += 1
                log_level_str = event_log_level_str(log_level)
                t = events.data['timestamp'][event_idx]
                event = None
                if event_parser is not None:
                    event = event_parser.parse(event_id, bytes(args))
                if event is None:
                    messages.append((t, log_level_str,
                                     '[Unknown event with ID {:}]'.format(event_id)))
                else:
                    # only show default group
                    if event.group() == "default":
                        messages.append((t, log_level_str, event.message()))
                # we could expand this a bit for events:
                # - show the description too
                # - handle url's as link (currently it's shown as text, and all tags are escaped)
        except (KeyError, IndexError, ValueError):
            # no events in log
            pass

        return messages
