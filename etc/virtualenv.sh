#!/bin/bash

# Actives the python virtual environment.

# Get virtualvenv folder path
venv_path=$(pipenv --venv)
venv_path="${venv_path%%[[:cntrl:]]}"

# Create new virtualvenv if there isn't one yet
if [ -z "$venv_path" ]; then
  pipenv install
  venv_path=$(pipenv --venv)
  venv_path="${venv_path%%[[:cntrl:]]}"
fi

# Activate virtual env
if [[ "$OSTYPE" == "win32" || "$OSTYPE" == "msys" ]]; then # Windows
  source $venv_path/Scripts/activate
else
  source $venv_path/bin/activate
fi
