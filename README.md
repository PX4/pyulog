# pyulog

This repository contains a python package to parse ULog files and scripts to
convert and display them. ULog is a self-describing logging format which is
documented [here](https://dev.px4.io/en/log/ulog_file_format.html).

The provided [command line scripts](#scripts) are:
- `ulog_info`: display information from an ULog file.
- `ulog_messages`: display logged messages from an ULog file.
- `ulog_params`: extract parameters from an ULog file.
- `ulog2csv`: convert ULog to CSV files.
- `ulog2kml`: convert ULog to KML files.


## Installation

Installation with package manager:
```bash
pip install pyulog
```

Installation from source:
```bash
python setup.py build install
```

## Development

To install the code in a format so that it can be easily edited use the
following command (this will install the package as a link to the repo):

```bash
pip install -e .
```

## Testing

```bash
nosetests -sv
```

or 

```bash
python setup.py test
```

## Code Checking 

```bash
pylint pyulog/*.py
```

<span id="scripts"></span>
## Command Line Scripts

All scripts are installed as system-wide applications (i.e. they be called on the command line without specifying Python or a system path), and support the `-h` flag for getting usage instructions.

The sections below show the usage syntax and sample output (from [test/sample.ulg](test/sample.ulg)): 

###  Display information from an ULog file (ulog_info)

Usage:
```bash
usage: ulog_info [-h] [-v] file.ulg

Display information from an ULog file

positional arguments:
  file.ulg       ULog input file

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Verbose output
```

Example output:
```bash
$ ulog_info sample.ulg
Logging start time: 0:01:52, duration: 0:01:08
Dropouts: count: 4, total duration: 0.1 s, max: 62 ms, mean: 29 ms
Info Messages:
 sys_name: PX4
 time_ref_utc: 0
 ver_hw: AUAV_X21
 ver_sw: fd483321a5cf50ead91164356d15aa474643aa73

Name (multi id, message size in bytes)    number of data points, total bytes
 actuator_controls_0 (0, 48)                 3269     156912
 actuator_outputs (0, 76)                    1311      99636
 commander_state (0, 9)                       678       6102
 control_state (0, 122)                      3268     398696
 cpuload (0, 16)                               69       1104
 ekf2_innovations (0, 140)                   3271     457940
 estimator_status (0, 309)                   1311     405099
 sensor_combined (0, 72)                    17070    1229040
 sensor_preflight (0, 16)                   17072     273152
 telemetry_status (0, 36)                      70       2520
 vehicle_attitude (0, 36)                    6461     232596
 vehicle_attitude_setpoint (0, 55)           3272     179960
 vehicle_local_position (0, 123)              678      83394
 vehicle_rates_setpoint (0, 24)              6448     154752
 vehicle_status (0, 45)                       294      13230
```

### Display logged messages from an ULog file (ulog_messages)

Usage:
```
usage: ulog_messages [-h] file.ulg

Display logged messages from an ULog file

positional arguments:
  file.ulg    ULog input file

optional arguments:
  -h, --help  show this help message and exit
```

Example output:
```
ubuntu@ubuntu:~/github/pyulog/test$ ulog_messages sample.ulg
0:02:38 ERROR: [sensors] no barometer found on /dev/baro0 (2)
0:02:42 ERROR: [sensors] no barometer found on /dev/baro0 (2)
0:02:51 ERROR: [sensors] no barometer found on /dev/baro0 (2)
0:02:56 ERROR: [sensors] no barometer found on /dev/baro0 (2)
```

### Extract parameters from an ULog file (ulog_params)

Usage:
```
usage: ulog_params [-h] [-d DELIMITER] [-i] [-o] file.ulg [params.txt]

Extract parameters from an ULog file

positional arguments:
  file.ulg              ULog input file
  params.txt            Output filename (default=stdout)

optional arguments:
  -h, --help            show this help message and exit
  -d DELIMITER, --delimiter DELIMITER
                        Use delimiter in CSV (default is ',')
  -i, --initial         Only extract initial parameters
  -o, --octave          Use Octave format
```

Example output (to console):
```
ubuntu@ubuntu:~/github/pyulog/test$ ulog_params sample.ulg
ATT_ACC_COMP,1
ATT_BIAS_MAX,0.0500000007451
ATT_EXT_HDG_M,0
...
VT_OPT_RECOV_EN,0
VT_TYPE,0
VT_WV_LND_EN,0
VT_WV_LTR_EN,0
VT_WV_YAWR_SCL,0.15000000596
```

### Convert ULog to CSV files (ulog2csv)

Usage:
```
usage: ulog2csv [-h] [-m MESSAGES] [-d DELIMITER] [-o DIR] file.ulg

Convert ULog to CSV

positional arguments:
  file.ulg              ULog input file

optional arguments:
  -h, --help            show this help message and exit
  -m MESSAGES, --messages MESSAGES
                        Only consider given messages. Must be a comma-
                        separated list of names, like
                        'sensor_combined,vehicle_gps_position'
  -d DELIMITER, --delimiter DELIMITER
                        Use delimiter in CSV (default is ',')
  -o DIR, --output DIR  Output directory (default is same as input file)
```


### Convert ULog to KML files (ulog2kml)

> **Note** The `simplekml` module must be installed on your computer. If not already present, you can install it with:
  ```
  pip install simplekml
  ```

Usage:
```
usage: ulog2kml [-h] [-o OUTPUT_FILENAME] [--topic TOPIC_NAME]
                [--camera-trigger CAMERA_TRIGGER]
                file.ulg

Convert ULog to KML

positional arguments:
  file.ulg              ULog input file

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT_FILENAME, --output OUTPUT_FILENAME
                        output filename
  --topic TOPIC_NAME    topic name with position data
                        (default=vehicle_gps_position)
  --camera-trigger CAMERA_TRIGGER
                        Camera trigger topic name (e.g. camera_capture)
```
