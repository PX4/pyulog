### pyulog ###

This repository contains a python package to parse ULog files and scripts to
convert and display them. ULog is a self-describing logging format which is
documented [here](http://dev.px4.io/advanced-ulog-file-format.html).

#### Installation ####

Installation with package manager:
```bash
pip install pyulog
```

Installation from source:
```bash
python setup.py build install
```

#### Command Line Scripts ####
- `ulog_info`: display information from an ULog file.
- `ulog_messages`: display logged messages from an ULog file.
- `ulog_params`: extract parameters from an ULog file.
- `ulog2csv`: convert ULog to CSV files.
- `ulog2kml`: convert ULog to KML files.


#### Development ####

To install the code in a format so that it can be easily edited use the
following command (this will install the package as a link to the repo):

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

#### Code Checking ####

```bash
pylint pyulog/*.py
```

