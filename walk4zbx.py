# snmpwalk2zbx: Create a Zabbix template from an SNMPWALK response.
# Copyright (C) Goran Kosutic 2022
# Sorce https://github.com/kosugor/walk4zbx
import sys
import getopt
import re
from os import popen
from html import escape
from collections import OrderedDict


DESCpattern = re.compile(r'DESCRIPTION\s+"([^"]*)"')
OIDpattern = re.compile(r"^(\.[0-9]+)+")
MSpattern = re.compile(r"^(\S*)::(\S*)")


class Setup:
    def __init__(self):
        # default values
        VER = "2c"
        COMMUNITY = "public"
        AGENT = "127.0.0.1"
        PORT = "161"
        BASEOIDS = [
            ".",
        ]
        self.ver = VER
        self.community = COMMUNITY
        self.agent = AGENT
        self.port = PORT
        self.baseoids = BASEOIDS

    def readParams(self):
        try:
            myopts, args = getopt.getopt(sys.argv[1:], "v:c:a:p")
        except getopt.GetoptError as e:
            print(str(e))
            print(
                f"Usage: {sys.argv[0]} -v 1|2c|3 -c COMMUNITY -a AGENT -p PORT OID [OID2...]"
            )
            sys.exit(2)

        for option, argument in myopts:
            match option:
                case "-v":
                    if argument in ["1", "2c", "3"]:
                        self.ver = argument
                    else:
                        print("snmp version not recognized, using default (2c)")
                case "-c":
                    self.community = argument
                case "-a":
                    self.agent = argument
                case "-p":
                    self.port = argument

        if len(args) != 0:
            self.baseoids = args


def WalkResponse(v, c, a, p, o):
    if v == "1" or v == "2c":
        command = f"snmpwalk -v {v} -c {c} -On {a}:{p} {o}"
        print("USING: " + command)
        wr = popen(command).read()
        return wr.rstrip()


def OIDtranslate(o):
    # returns a tuple (fullname, details)
    transfull = popen(f"snmptranslate -Of {o}").read()
    transdetail = popen(f"snmptranslate -Td -OS {o}").read()
    # determine MIB and short symbolic name
    ms = findMS(transdetail)
    return transfull.rstrip(), transdetail.rstrip(), ms[0], ms[1]


def findLevels(o):
    l = o.split(".")
    return len(l)


def uplevels(o, n):
    newoid = o
    for l in range(1, n + 1):
        n = newoid.rfind(".")
        newoid = newoid[:n]
    return newoid


def lastLevel(o):
    t = o.rfind(".") + 1
    ll = o[t:]
    return ll


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


def desc2html(det):
    detsearch = DESCpattern.search(det)
    dettext = detsearch.group(1)
    return escape(dettext)


def findMS(det):
    MSmatch = MSpattern.match(det)
    if MSmatch:
        return MSmatch.groups()


checkedoids = OrderedDict()
scalars = []
columnoids = []

s = Setup()
s.readParams()

for baseoid in s.baseoids:
    response = WalkResponse(s.ver, s.community, s.agent, s.port, baseoid)
    responselines = response.splitlines()
    print(f"Response has {len(responselines)} lines")
    for responseline in responselines:
        # checking if it is a numeric oid in the beginning of response line
        oidmatch = OIDpattern.match(responseline)
        if oidmatch:
            currentoid = oidmatch.group()
            # avoiding duplicate oids
            if currentoid not in checkedoids:
                trfull, trdetail, m, s = OIDtranslate(currentoid)
                checkedoids[currentoid] = trfull, trdetail
                if not BelongsToTable(currentoid):
                    # first it needs to check how many oid levels in short oid
                    levelsShort = findLevels(s)
                    parfull = uplevels(trfull, levelsShort)
                    parshort = lastLevel(parfull)
                    desc = desc2html(trdetail)
                    scalars.append((parshort, s, currentoid, trfull, desc))
                    print(
                        f"ADDING SIMPLE ITEM: APP {parshort} ITEM {m}::{s} KEY {currentoid}\n{trfull}\n{desc}\n"
                    )
                else:
                    CN = FindColumnName(currentoid)
                    if CN not in columnoids:
                        columnoids.append(CN)
                        TN = uplevels(CN, 2)
                        # print(f"TABLE {TN} COLUMN {CN}")
        else:
            print("discarding line: '" + responseline + "'")
    print("")

print(f"Total OIDs: {len(checkedoids)}")

print("Simple items:", len(scalars))
print("Columns:", len(columnoids))
