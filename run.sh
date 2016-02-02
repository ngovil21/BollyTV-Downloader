#!/usr/bin/env bash

runpath="${0%/*}"
if [ -d "${runpath}" ]
then
    cd "${runpath}"
fi

if [ -z "${1}" ]
then
    python3 ./BollyTV/Main.py "${1}"
else
    python3 ./BollyTV/Main.py
fi

