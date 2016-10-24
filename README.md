### pyulog ###

This repository contains a python package to parse ULog files and scripts to
convert and display them. ULog is a self-describing logging format which is
documented [here](http://dev.px4.io/advanced-ulog-file-format.html).

#### Installation ####

```bash
python setup.py build install
```

#### Command Line Scripts ####
- `pyulog_info`: display information from an ULog file.
- `pyulog_messages`: display logged messages from an ULog file.
- `pyulog_params`: extract parameters from an ULog file.
- `ulog2csv`: convert ULog to CSV files.


#### Development ####

To install the code in a format so that it can be easily
edited use the following command:

```bash
pip install -e .
```

#### Testing ####

```bash
nosetests -sv
```

or 

```bash
python setup.py test
```
