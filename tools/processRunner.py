#! /usr/bin/env python3

import subprocess

class ProcessRunner:

    def __init__(self):
        self.__command = ""
        self.__alienv_initialized = False

    def __init_alienv(self):
        if self.__alienv_initialized:
            return
        self.__command += "ALIENV=`which alienv;"
        self.__alienv_initialized = True

    def load_module(self, module: str):
        self.__init_alienv()
        self.__command += "eval `$ALIENV --no-refresh load {MODULE}`;".format(MODULE=module)

    def print_modules(self):
        self.__init_alienv()
        self.command += "$ALIENV list;"

    def source_script(self, script):
        self.command += "source {};".format(script)

    def write_instruction(self,  instruction):
        self.__command += "{};".format(instruction)

    def execute(self):
        subprocess.call(self.__command, shell=True)