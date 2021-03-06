#! /usr/bin/env python3 

class cluster_setup(object):

    def __init__(self):
        self._name = None
        self._image = None
        self._containermounts = None
        self._basemodules = None
        self._account = None
        self._hasMemResouce = None
        self._hasTimeLimit = None

    def name(self):
        return self._name

    def image(self):
        return self._image

    def containermounts(self):
        return self._containermounts

    def basemodules(self):
        return self._basemodules

    def account(self):
        return self._account

    def hasMemResource(self):
        return self._hasMemResouce

    def hasTimeLimit(self):
        return self._hasTimeLimit