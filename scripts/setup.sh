#!/bin/bash

echo "Checking system Python Version..."

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

REQ_MET="Requirements met!"
PYTHON_MET=false
PIP_MET=false

PIP3_REGEX='^pip.+(python\ 3.[6-9].+)$'
PYTHON3_6_REGEX='^Python\ 3\.[6-9].+$'
PYTHON_VERSION="$( python --version )"
PYTHON3_VERSION="$( python3 --version )"

if [[ $PYTHON_VERSION =~ $PYTHON3_6_REGEX ]]; then
	echo $REQ_MET
	PYTHON_MET=true
else
	if [[ $PYTHON3_VERSION =~ $PYTHON3_6_REGEX ]]; then
		echo $REQ_MET
		PYTHON_MET=true
	else
		echo "Python reuqirements not met!"
		echo "Setting up Python 3.6+"

		$("sudo apt-get update")
		$("sudo apt-get install python3 python3-pip")
		PYTHON_MET=true
		PIP_MET=true
	fi
fi

if [ "$PIP_MET" != "true" ]; then
	echo "Checking if pip is installed..."

	PIP_VERSION="$(python3 -m pip --version)"
	if [[ $PIP_VERSION =~ $PIP3_REGEX ]]; then
		echo $REQ_MET
		PIP_MET=true
	else
		echo "Pip is not installed!"
		echo "Installing pip..."

		$("sudo apt-get update")
		$("sudo apt-get install python3-pip")
		PIP_MET=true
	fi
fi

if [ "$PYTHON_MET" = "true" ] && [ "$PIP_MET" = "true" ]; then
	echo "Installing requirements..."
	cd $DIR/..
	python3 -m pip install -r requirements.txt
fi
