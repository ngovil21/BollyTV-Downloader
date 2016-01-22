#!/usr/bin/env bash

runpath="${0%/*}"
if [ -d "${runpath}" ]
then
    cd "${runpath}"
fi

python3 ./BollyTV/Main.py