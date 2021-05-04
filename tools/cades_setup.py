#! /usr/bin/env python3

from tools.cluster_setup import cluster_setup

class cades_setup(cluster_setup):

    def __init__(self):
        super().__init__()
        self._name = "CADES"
        self._image = "/home/mfasel_alice/mfasel_cc7_alice.simg"
        self._containermounts = ["/nfs/home", "/lustre"]
        self._basemodules = ["python/3.6.3", "PE-gnu", "singularity"]
        self._account = "birthright"
        self._hasMemResouce = True
        self._hasTimeLimit = True