# snmpwalk2zbx: Create a Zabbix template from an SNMPWALK response.
# Copyright (C) Goran Kosutic 2022
#Sorce https://github.com/kosugor/snmpwalk2zbx

import os,sys,re

def WalkResponse(community, snmpver, port, ip, oid):
    if snmpver=="1" or snmpver=="2c"):
        walkresponse = os.popen('snmpwalk -v '+ snmpver +' -c ' + community + ' -On ' + IP + ' ' + oid).read()
        return walkresponse

