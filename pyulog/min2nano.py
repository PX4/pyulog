import time

def convert_to_nanoseconds(minutes_seconds_str):
    """Converts time in MM:SS format to nanoseconds since epoch"""
    if minutes_seconds_str is None:
        return None

    # Parse minutes:seconds format
    minutes, seconds = map(int, minutes_seconds_str.split(':'))

    # Get current time in seconds since epoch
    current_time_seconds = int(time.time())

    # Calculate total seconds since epoch for the given minutes:seconds
    total_seconds = current_time_seconds + (minutes * 60) + seconds

    # Convert total seconds to nanoseconds
    return total_seconds * 1e9

start_MMSS = input("Enter you're starting time value in the format minues:seconds (MM:SS)")
flight_start_ns = convert_to_nanoseconds(start_MMSS)
print("Flight start time in nanoseconds:", flight_start_ns)

end_MMSS = input("Enter you're ending time value in the format minues:seconds (MM:SS)")
flight_end_ns = convert_to_nanoseconds(end_MMSS)
print("Flight end time in nanoseconds:", flight_end_ns)