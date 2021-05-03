#! /usr/bin/env python3

import subprocess
from tools.processRunner import ProcessRunner

class AnalysisRunner:

    def __init__(self, macro: str, hepmcfile: str):
        self.__macro = macro
        self.__hepmcfile = hepmcfile
        self.__modules = ["fastjet/latest", "HepMC/latest", "ROOT/latest"]

    def launch(self):
        runsteer = ProcessRunner()
        for module in self.__modules:
            runsteer.load_module(module)
        runsteer.print_modules()
        runsteer.write_instruction("root -l -b -q \'{MACRO}(\"{HEPMCFILE}\")\'".format(MACRO=self.__macro, HEPMCFILE=self.__hepmcfile))
        runsteer.execute()