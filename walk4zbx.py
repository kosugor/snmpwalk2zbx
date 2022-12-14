# snmpwalk2zbx: Create a Zabbix template from an SNMPWALK response.
# Copyright (C) Goran Kosutic 2022
# Sorce https://github.com/kosugor/walk4zbx
import sys
import getopt
import re
from os import popen

# from html import escape

DESCpattC = re.compile(r'DESCRIPTION\s+"([^"]*)"')
OIDpattC = re.compile(r"^(\.[A-Za-z0-9-_]+)+")
MSpattC = re.compile(r"^(\S*)::(\S*)")
SYNpattC = re.compile(r"SYNTAX\s+INTEGER\s+\{(.*)\s?\}")
VMpattC = re.compile(r"([^{}()\s]+)[(](\d+)[)]")
CONVpattC = re.compile(r"TEXTUAL CONVENTION (.*)")


class Walker:
    def __init__(self):
        # default options and arguments
        SNMPVER = "2c"
        COMMUNITY = "public"
        AGENT = "127.0.0.1:161"
        BASEOIDS = [
            ".",
        ]
        # default zabbix item configuration
        UPDATEINTERVAL = "60"
        DISCINTERVAL = "3600"
        HISTORY = "7"
        TRENDS = "365"
        # exit codes
        EX_OK = 0
        EX_USAGE = 64
        self.oidset = set()
        self.scalarset = set()
        self.columnset = set()
        helpMessage = f"""\
Usage: python3 {sys.argv[0]} [OPTIONS] AGENT OID [OID...]

Create a Zabbix template from an snmpwalk response.
Copyright (C) Goran Kosutic 2022
Source https://github.com/kosugor/walk4zbx

OPTIONS:
    -h, --help                  display this help message and exit
    -v, snmpver=1|2c|3          specifies SNMP version to use (default: '2c')

SNMP version 1 or 2 specific
    -c, community=COMMUNITY     community string (default: 'public')

SNMP version 3 specific
    -l, --level=LEVEL           security level (noAuthNoPriv|authNoPriv|authPriv)
    -n, --context==CONTEXT      context name
    -u, --username=USER-NAME    security name
    -a, --auth=PROTOCOL         authentication protocol (MD5|SHA|SHA-224|SHA-256|SHA-384|SHA-512)
    -A, --authpass=PASSPHRASE   authentication protocol pass phrase
    -x, --privacy=PROTOCOL      privacy protocol (DES|AES|AES-192|AES-256)
    -X, --privpass=PASSPHRASE   privacy protocol pass phrase

Zabbix item configuration
    -U, --update=SECONDS        update interval in seconds (default: 60)
    -D, --discover=SECONDS      discovery interval in seconds (default: 3600)
    -H, --history=DAYS          history retention in days (default: 7)
    -T, --trends=DAYS           trends retention in days (default: 365)

ARGUMENTS:
    AGENT                       SNMP agent (default: '127.0.0.1:161')
    OID [OID...]                list of oid roots to export (default: '.')
"""
        try:
            myopts, args = getopt.getopt(
                sys.argv[1:],
                "hv:c:l:n:u:a:A:x:X:U:D:H:T:",
                [
                    "help",
                    "snmpver=",
                    "community=",
                    "level=",
                    "context=",
                    "username=",
                    "auth=",
                    "authpass=",
                    "privacy=",
                    "privpass=",
                    "update=",
                    "discover=",
                    "history=",
                    "trends=",
                ],
            )
        except getopt.GetoptError as e:
            sys.stderr.write("ERROR: %s\r\n%s\r\n" % (str(e), helpMessage))
            sys.exit(EX_USAGE)

        self.snmpver = SNMPVER
        self.community = COMMUNITY
        self.agent = AGENT
        self.baseoids = BASEOIDS
        for option, argument in myopts:
            if option == "-h" or option == "--help":
                sys.stderr.write(helpMessage)
                sys.exit(EX_OK)
            if option == "-v" or option == "--snmpver":
                if argument in ["1", "2c", "3"]:
                    self.snmpver = argument
                else:
                    print("snmp version not recognized, using default (2c)")
            if option == "-c" or option == "--community":
                if argument is not None:
                    self.community = argument
            if option == "-l" or option == "--level":
                self.level = argument
            if option == "-n" or option == "--context":
                self.context = argument
            if option == "-u" or option == "--username":
                self.username = argument
            if option == "-a" or option == "--auth":
                self.auth = argument
            if option == "-A" or option == "--authpass":
                self.authpas = argument
            if option == "-x" or option == "--privacy":
                self.privacy = argument
            if option == "-X" or option == "--privpass":
                self.privpass = argument
            if option == "-U" or option == "--update":
                try:
                    argint = int(argument)
                    self.updateinterval = argint
                except ValueError:
                    print("using using default update interval")
                    self.updateinterval = UPDATEINTERVAL
            if option == "-D" or option == "--discover":
                try:
                    argint = int(argument)
                    self.discdelay = argint
                except ValueError:
                    print("using using default discovery delay")
                    self.discinterval = DISCINTERVAL
            if option == "-H" or option == "--history":
                try:
                    argint = int(argument)
                    self.history = argint
                except ValueError:
                    print("using using default discovery delay")
                    self.history = HISTORY
            if option == "-T" or option == "--trends":
                try:
                    argint = int(argument)
                    self.trends = argint
                except ValueError:
                    print("using using default discovery delay")
                    self.trends = TRENDS

        if len(args) > 1:
            self.agent = args[0]
            self.baseoids = args[1:]

    def walk(self):
        for baseoid in self.baseoids:
            if self.snmpver == "1" or self.snmpver == "2c":
                command = f"snmpwalk -v {self.snmpver} -c {self.community}"
            if self.snmpver == "3":
                command = f"snmpwalk -v 3 -a {self.auth} -A {self.authpass}"
                command += f" -l {self.level} -n {self.context}"
                command += f" -u {self.user} -x {self.protocol}"
                command += f" -X {self.passphrase}"
            command += f" -Of {self.agent} {baseoid}"
            print("USING: " + command)
            walkresponse = popen(command).read()
            walkresponse = walkresponse.strip()
            responselines = walkresponse.splitlines()
            print(f"Response has {len(responselines)} lines")
            for r in responselines:
                # checking if it is a numeric oid in the beginning of response line
                oidmatch = OIDpattC.match(r)
                if oidmatch:
                    currentoid = oidmatch.group()
                    self.oidset.add(currentoid)
                else:
                    print("Discarding line: ", r)

    def classify(self):
        for oid in self.oidset:
            if "TABLE" in oid.upper():
                nodes = oid.split(".")
                col = nodes
                for level, node in enumerate(nodes[1:]):
                    if node.upper().endswith("TABLE"):
                        # table name is level+2, column name is level+4
                        col = nodes[: level + 4]
                        break
                coloid = ".".join(col)
                self.columnset.add(coloid)
            else:
                self.scalarset.add(oid)


class OIDitem:
    def __init__(self, o):
        self.oid = o
        self.mib = ""
        self.short = ""
        self.detail = ""
        transdetail = popen(f"snmptranslate -Td -OS {o}").read()
        self.detail = transdetail.rstrip()
        # determine MIB and short symbolic name
        MSmatch = MSpattC.match(self.detail)
        if MSmatch:
            ms = MSmatch.groups()
            self.mib = ms[0]
            self.short = ms[1]

    def description(self):
        DESCsearch = DESCpattC.search(self.detail)
        if DESCsearch:
            return DESCsearch.group(1)

    def valuemap(self):
        SYNsearch = SYNpattC.search(self.detail)
        if SYNsearch:
            vm = SYNsearch.group(1)
            vmlist = VMpattC.findall(vm)
            return vmlist

    def textconv(self):
        CONVsearch = CONVpattC.search(self.detail)
        if CONVsearch:
            return CONVsearch.group(1)


walker = Walker()
walker.walk()
walker.classify()

for scalar in sorted(walker.scalarset):
    OID = OIDitem(scalar)
    if OID.valuemap():
        print(OID.mib + "::" + OID.short)
        # print(OID.description())
        print(OID.textconv(), OID.valuemap(), "\n")
