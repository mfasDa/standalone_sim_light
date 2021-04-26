#! /usr/bin/env python3

class mount:
        
    def __init__(self, source: str, target: str):
        self.__source = source
        self.__target = target

    def set_source(self, source: str):
        self.__source = source

    def set_target(self, target: str):
        self.__target = target

    def get_source(self) -> str:
        return self.__source

    def get_target(self) -> str:
        return self.__target

    def build_command(self) -> str:
        return "-B {SOURCE}:{TARGET}".format(SOURCE=self.__source, TARGET=self.__target)

    source = property(fget=get_source, fset=set_source)
    target = property(fget=get_target, fset=set_target)

class singularity:

    def __init__(self, image, command):
        self.__image = image
        self.__mounts = []
        self.__command = command

    def set_image(self, image):
        self.__image = image

    def get_image(self) -> str:
        return self.__image

    def set_command(self, command):
        self.__command = command

    def get_command(self) -> str:
        return self.__command

    def add_mount(self, source: str, target: str = None):
        self.__mounts.append(mount(source, target if target != None else source))

    def add_mounts(self, mounts: list):
        self.__mounts = self.__mounts + [mount(dirname, dirname) for dirname in mounts]

    def build_command(self):
        command = "singularity exec"
        for mnt in self.__mounts:
            command += " {}".format(mnt.build_command())
        command += " {}".format(self.__image)
        command += " {}".format(self.__command)
        return command

class singularity_engine:

    def __init__(self, image=None):
        self.__image = image
        self.__mounts = []

    def add_mount(self, source: str, target: str = None):
        self.__mounts.append(mount(source, target if target != None else source))

    def add_mounts(self, mounts: list):
        self.__mounts = self.__mounts + [mount(dirname, dirname) for dirname in mounts]

    def build_singularity(self, command) -> singularity:
        singobject = singularity(self.__image, command)
        for mount in self.__mounts:
            singobject.add_mount(mount.source, mount.target)
        return singobject