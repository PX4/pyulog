# pyulog

 이 레포지토리에는 ULog 파일 및 스크립트를 파싱하는 python 패키지가 포함되어 있습니다.
 ULog는 self-describing 형식을 따르며, 해당 관련 문서는 다음과 같습니다(https://docs.px4.io/main/en/dev_log/ulog_file_format.html).

제공되는 명령어 스크립트는(command line scripts)는 아래와 같습니다:
- `ulog_info`: ULog 파일의 정보를 나타냅니다.
- `ulog_messages`: ULog 파일에 기록된 로그 메시지(logged messages)를 출력합니다.
- `ulog_params`: ULog 파일에 저장된 파라미터들을 추출합니다.
- `ulog2csv`: ULog 파일을 CSV 파일로 변환합니다.
- `ulog2kml`: ULog 파일을 KML 파일로 변환합니다.


## 설치

패키지 설치:
```bash
pip install pyulog
```

소스코드를 통한 설치:
```bash
python setup.py build install
```

## 추가 개발

코드를 쉽게 변경 및 편집할 수 있는 형식으로 설치하려면 다음 명령 사용(해당 명령은 패키지를 Repo에 대한 링크로 설치합니다):

```bash
pip install -e .
```

## 테스트

```bash
pytest test
```

또는,

```bash
python setup.py test
```

## 코드 검사(Code Checking)

```bash
pylint pyulog/*.py
```

<span id="scripts"></span>
## 명령어 스크립트


모든 스크립트는 시스템 전체 어플리케이션단에서 설치되며(Python 또는 시스템 경로를 지정하지 않고
커맨드 라인에서 호출), `-h` 플래그를 통해 각 스크립트의 사용법을 확인할 수 있습니다.

아래 섹션에서는 사용 구문 및 샘플 출력을 나타냅니다. (from [test/sample.ulg](test/sample.ulg)):

###  ULog 파일로부터 정보 출력 (ulog_info)

사용:
```bash
usage: ulog_info [-h] [-v] file.ulg

Display information from an ULog file

positional arguments:
  file.ulg       ULog input file

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Verbose output
```

결과 예시:
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

### ULog 파일에 기록된 로그 메시지 출력 (ulog_messages)

사용:
```
usage: ulog_messages [-h] file.ulg

Display logged messages from an ULog file

positional arguments:
  file.ulg    ULog input file

optional arguments:
  -h, --help  show this help message and exit
```

결과 예시:
```
ubuntu@ubuntu:~/github/pyulog/test$ ulog_messages sample.ulg
0:02:38 ERROR: [sensors] no barometer found on /dev/baro0 (2)
0:02:42 ERROR: [sensors] no barometer found on /dev/baro0 (2)
0:02:51 ERROR: [sensors] no barometer found on /dev/baro0 (2)
0:02:56 ERROR: [sensors] no barometer found on /dev/baro0 (2)
```

### ULog 파일에 저장된 파라미터 추출 (ulog_params)

사용:
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

결과 예시 (콘솔 출력):
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

### ULog 파일을 CSV 파일로 변환 (ulog2csv)

사용:
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


### ULog 파일을 KML 파일로 변환 (ulog2kml)

> **Note** 모듈 `simplekml` 이 사용자의 PC에 설치되어 있어야 합니다. 만약 설치되어 있지 않다면, 아래 명령어를 통해 설치하십시오.
  ```
  pip install simplekml
  ```

사용:
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

### ULog 파일을 rosbag 파일로 변환 (ulog2rosbag)

> **Note** `px4_msgs`가 설치된 ROS 환경이 필요합니다.

사용:
```
usage: ulog2rosbag [-h] [-m MESSAGES] file.ulg result.bag

Convert ULog to rosbag

positional arguments:
  file.ulg              ULog input file
  result.ulg            rosbag output file

optional arguments:
  -h, --help            show this help message and exit
  -m MESSAGES, --messages MESSAGES
                        Only consider given messages. Must be a comma-
                        separated list of names, like
                        'sensor_combined,vehicle_gps_position'
```
### Migrate/setup the database for use with the DatabaseULog class (ulog_migratedb)

사용:
```
usage: ulog_migratedb [-h] [-d DB_PATH] [-n] [-s SQL_DIR] [-f]

Setup the database for DatabaseULog

optional arguments:
  -h, --help            show this help message and exit
  -d DB_PATH, --database DB_PATH
                        Path to the database file
  -n, --noop            Only print results, do not execute migration scripts.
  -s SQL_DIR, --sql SQL_DIR
                        Directory with migration SQL files
  -f, --force           Run the migration script even if the database is not
                        created with this script.

```
결과 예시 (콘솔 출력):
```
ubuntu@ubuntu:~/github/pyulog$ ulog_migratedb
Using migration files in /home/ubuntu/github/pyulog/pyulog/sql.
Database file pyulog.sqlite3 not found, creating it from scratch.
Current schema version: 0 (database) and 1 (code).
Executing /home/ubuntu/github/pyulog/pyulog/sql/pyulog.1.sql.
Migration done.
```
