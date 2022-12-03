# snmpwalk2zbx: Create a Zabbix template from an SNMPWALK response.
# Copyright (C) Goran Kosutic 2022
# Sorce https://github.com/kosugor/snmpwalk2zbx


import os, sys, re


def WalkResponse(community, snmpver, port, IP, oid):
    if snmpver == "1" or snmpver == "2c":
        walkresponse = os.popen(
            "snmpwalk -v " + snmpver + " -c " + community + " -On " + IP + " " + oid
        ).read()
        return walkresponse


snmpver = "2c"
community = "public"
port = "161"
IP = "127.0.0.1"
oid = ".1.3.6.1"

r = WalkResponse(community, snmpver, port, IP, oid)
print(r)
