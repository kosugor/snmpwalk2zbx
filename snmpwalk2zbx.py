# snmpwalk2zbx: Create a Zabbix template from an SNMPWALK response.
# Copyright (C) Goran Kosutic 2022
# Sorce https://github.com/kosugor/snmpwalk2zbx


import sys, getopt, re
from os import popen
from collections import OrderedDict

# default values
VER = "2c"
COMMUNITY = "public"
AGENT = "127.0.0.1"
PORT = "161"
OID = ["."]

ver = VER
community = COMMUNITY
agent = AGENT
port = PORT

try:
    myopts, args = getopt.getopt(sys.argv[1:], "v:c:a:p:o")
except getopt.GetoptError as e:
    print(str(e))
    print(f"Usage: {sys.argv[0]} -v 1|2c|3 -c COMMUNITY -a AGENT -p PORT OID [OID2...]")
    sys.exit(2)

for option, argument in myopts:
    match option:
        case "-v":
            if argument in ["1", "2c", "3"]:
                ver = argument
            else:
                print("snmp version not recognized, using default (2c)")
        case "-c":
            community = argument
        case "-a":
            agent = argument
        case "-p":
            port = argument

baseoids = args
if len(baseoids) == 0:
    baseoids = OID


def WalkResponse(v, c, a, p, o):
    if v == "1" or v == "2c":
        command = f"snmpwalk -v {v} -c {c} -On {a}:{p} {o}"
        print("USING: " + command)
        wr = popen(command).read()
        return wr


def OIDtranslate(o):
    # returns a tuple (fullname, details)
    transfull = popen(f"snmptranslate -Of {o}").read()
    transdetail = popen(f"snmptranslate -Td -OS {o}").read()
    return transfull.rstrip(), transdetail.rstrip()


def BelongsToTable(k):
    # must be executed after translations exist for checked oids, [0] is fullname
    if "TABLE" in checkedoids[k][0].upper():
        return True


checkedoids = OrderedDict()

for baseoid in baseoids:
    response = WalkResponse(ver, community, agent, port, baseoid).rstrip()
    responselines = response.split("\n")
    print(f"response has {len(responselines)} lines")
    for responseline in responselines:
        # checking if it is a numeric oid in the beginning of response line
        if re.match(r"(\.[0-9]+)+", responseline):
            # taking only numeric oid
            currentoid = responseline.split("=")[0].rstrip()
            # avoiding duplicate oids
            if currentoid not in checkedoids:
                trfull, trdetail = OIDtranslate(currentoid)
                checkedoids[currentoid] = trfull, trdetail
        else:
            print("discarding line: '" + responseline + "'")

print(f"Total OIDs: {len(checkedoids)}")

scalars = []
fullColumnNames = []

for key, value in checkedoids.items():
    if not BelongsToTable(key):
        scalars.append(key)

print("simple items:", len(scalars))
for sc in scalars:
    print(checkedoids[sc][0])
