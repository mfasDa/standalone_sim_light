#! /usr/bin/env python3

import socket
from tools.cades_setup import cades_setup
from tools.b587_setup import b587_setup

def cluster_factory():
    hostname = socket.gethostname()
    if "or-slurm" in hostname:
        return cades_setup()
    elif "pc059" in hostname:
        return b587_setup()
