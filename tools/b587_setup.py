#! /usr/bin/env python3

from tools.cluster_setup import cluster_setup

class b587_setup(cluster_setup):

    def __init__(self):
        super(cluster_setup).__init__()
        self._hasMemResouce = False