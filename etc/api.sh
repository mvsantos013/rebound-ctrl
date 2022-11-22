#!/bin/bash

# This script will active the python virtual environment and execute the API.

source ./etc/virtualenv.sh

sls wsgi serve --port 3005