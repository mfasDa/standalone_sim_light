#! /usr/bin/env python3

import os
from tools.singularity import singularity_engine
from tools.cluster_setup import cluster_setup

class runhandler:

    def __init__(self, repositiry: str, executable: str, arguments: list):
        self.__repository = repositiry
        self.__executable = executable
        self.__arguments = arguments
        self.__logfile = None
        self.__containerhandler = None

    def set_logfile(self, logfile: str):
        self.__logfile = logfile

    def initalize_containerhandler(self, image: str, mounts: list):
        self.__containerhandler = singularity_engine(image)
        if len(mounts):
            self.__containerhandler.add_mounts(mounts)

    def initialize(self, batchconfig: cluster_setup):
        if batchconfig.image():
            self.__containerhandler = singularity_engine(batchconfig.image())
            if batchconfig.containermounts() and len(batchconfig.containermounts()):
                self.__containerhandler.add_mounts(batchconfig.containermounts())

    def launch(self):
        runcommand = "{WRAP} {EXE}".format(WRAP=os.path.join(self.__repository, "containerwrapper.sh"), EXE=self.__executable) if self.__containerhandler else self.__executable
        for arg in self.__arguments:
            runcommand += " {ARG}".format(ARG=arg)
        if self.__logfile and len(self.__logfile):
            runcommand += " &> {}".format(self.__logfile)
        if self.__containerhandler:
            return self.__containerhandler.build_singularity(runcommand).build_command()
        else:
            return runcommand
