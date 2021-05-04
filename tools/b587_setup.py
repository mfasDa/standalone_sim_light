#! /usr/bin/env python3

from tools.cluster_setup import cluster_setup

class b587_setup(cluster_setup):

    def __init__(self):
        super().__init__()
        self._name = "B587"
        self._hasMemResouce = False
        self._hasTimeLimit = False