#!/bin/bash

CURR_PATH=$(pwd)

cd Analysis
export PYTHONPATH=../../src/Analysis:../../src/common
py.test-3

cd $CURR_PATH
