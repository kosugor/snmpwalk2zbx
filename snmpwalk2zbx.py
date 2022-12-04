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


def FindColumnName(k):
    # must be executed after translations exist for checked oids, [0] is fullname
    fn = checkedoids[k][0].upper()
    namenodes = fn.split(".")
    numbernodes = k.split(".")
    for level, node in enumerate(namenodes[1:]):
        if node.upper().endswith("TABLE"):
            # table name is level+2, column name is level+4
            co = numbernodes[: level + 4]
            break
    return ".".join(co)


checkedoids = OrderedDict()
scalars = []
columnoids = []

for baseoid in baseoids:
    response = WalkResponse(ver, community, agent, port, baseoid).rstrip()
    responselines = response.split("\n")
    print(f"Response has {len(responselines)} lines")
    for responseline in responselines:
        # checking if it is a numeric oid in the beginning of response line
        if re.match(r"(\.[0-9]+)+", responseline):
            # taking only numeric oid
            currentoid = responseline.split("=")[0].rstrip()
            # avoiding duplicate oids
            if currentoid not in checkedoids:
                trfull, trdetail = OIDtranslate(currentoid)
                checkedoids[currentoid] = trfull, trdetail
                if not BelongsToTable(currentoid):
                    scalars.append(currentoid)
                    print(f"ADDING SIMPLE ITEM {currentoid}")
                else:
                    CN = FindColumnName(currentoid)
                    if CN not in columnoids:
                        columnoids.append(CN)
                        print(f"ADDING COLUMN {CN}")
        else:
            print("discarding line: '" + responseline + "'")
    print("")

print(f"Total OIDs: {len(checkedoids)}")

print("Simple items:", len(scalars))
print("Columns:", len(columnoids))

"""
for sc in scalars:
    print(checkedoids[sc][0])
"""
