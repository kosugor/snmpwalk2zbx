# snmpwalk2zbx: Create a Zabbix template from an SNMPWALK response.
# Copyright (C) Goran Kosutic 2022
# Sorce https://github.com/kosugor/snmpwalk2zbx


import os, sys, getopt

# default values
VER = "2c"
COMMUNITY = "public"
AGENT = "127.0.0.1"
PORT = "161"
OID = "."

ver = VER
community = COMMUNITY
agent = AGENT
port = PORT
oid = OID

try:
    myopts, args = getopt.getopt(sys.argv[1:], "v:c:a:p:o")
except getopt.GetoptError as e:
    print(str(e))
    print("Usage: %s -v 1|2c|3 -c COMMUNITY -a AGENT -p PORT -o OID" % sys.argv[0])
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
        case "-o":
            oid = argument


def WalkResponse(v, c, a, p, o):
    if v == "1" or v == "2c":
        command = "snmpwalk -v %s -c %s -On %s:%s %s" % (v, c, a, p, o)
        print("USING: " + command)
        wr = os.popen(command).read()
        return wr


r = WalkResponse(ver, community, agent, port, oid)
print(r)
