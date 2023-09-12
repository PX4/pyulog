#! /bin/bash

pytest test && pylint pyulog/*.py test/*.py

