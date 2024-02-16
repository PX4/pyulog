
#! /usr/bin/env python

"""
Convert a ULog file into CSV file(s)
"""
#commandline usage: python <file.py> <file.ulg> -flight_start <insert timestamp value> -flight_end <insert timestamp value>
#OUTS: python crop_ulog Jan_Subscale_Launch.ulg -flight_start 19:20 -flight_end 21:40
#for us 19:20 to 21:40

from __future__ import print_function

import argparse
import numpy as np

from core import ULog
print("\nCompleted importing core file")

#pylint: disable=too-many-locals, invalid-name, consider-using-enumerate



def main():
    """Command line interface"""
    print("\nStarting argument parsing ...")

    parser = argparse.ArgumentParser(description='Crops ULog file')
    parser.add_argument('ulog_file', metavar='file.ulg', help='ULog input file')

    parser.add_argument(
        '-flight_start', '--flight_start', dest='flight_start',
        help="Start timestamp for flight data (in HH:MM)")

    parser.add_argument(
        '-flight_end', '--flight_end', dest='flight_end',
        help="End timestamp for flight data (in HH:MM)")

    args = parser.parse_args()
    print("Completed argument parsing")

 # Convert HH:MM format to seconds
    flight_start_seconds = convert_to_seconds(args.flight_start)
    flight_end_seconds = convert_to_seconds(args.flight_end)

    crop_ulog(args.ulog_file, flight_start_seconds, flight_end_seconds)

    print(" complete")
    
def convert_to_seconds(time_str):
    """Converts time in HH:MM format to seconds"""
    if time_str is None:
        return None

    hours, minutes = map(int, time_str.split(':'))
    return hours * 3600 + minutes * 60



def crop_ulog(ulog_file_name, flight_start, flight_end):
    """
    Crops the ULog file

    :param ulog_file_name: The ULog filename to open and read
    :param flight_start: Start time for conversion in seconds
    :param flight_end: End time for conversion in seconds

    :return: None
    """
    print("\nStarting to crop ...")

    ulog = ULog(ulog_file_name)
    data = ulog.data_list

    for d in data:
        print("Timestamp data:", d.data['timestamp']) #check timestamp data

        #get the index for row where flight data starts
        flight_start_index = np.where(d.data['timestamp'] >= flight_start * 1e6)[0][0] \
            if flight_start else 0

        #get the index for row where flight data ends
        flight_end_index = np.where(d.data['timestamp'] >= flight_end * 1e6)[0][0] \
            if flight_end else len(d.data['timestamp'])

        # Crop the data
        newData = {}
        for key, value in d.data.items():
            croppedData = value[flight_start_index:flight_end_index]
            newData[key] = croppedData
        d.data = newData



    #save cropped ulog file
    renamed_output_file = ulog_file_name[:-4] + '_cropped.ulg'
    ulog.save(renamed_output_file)
    print("Cropped file saved")


if __name__ == "__main__":
    main()