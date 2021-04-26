#! /usr/bin/env python3

import argparse
import logging
import os
from submit_merge import submit_merge

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="sumbit_merge_many", description="Submitter for pthard/ktmin productions")
    parser.add_argument("-o", "--outputdir", metavar="OUTPUTDIR", type=str, required=True, help="Output base diretory")
    parser.add_argument("-r", "--rootfile", metavar="ROOTFILE", type=str, required=True, help="Name of the rootfile")
    parser.add_argument("-q", "--queue", metavar="QUEUE", default="gpu", help="Queue/Partition (default: gpu)")
    parser.add_argument("-d", "--debug", metavar="DEBUG", action="store_true", help="Enable debug messages")
    args = parser.parse_args()

    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(format='[%(levelname)s]: %(message)s', level=loglevel)

    for cnt in sorted(os.listdir(args.outputdir)):
        tstdir = os.path.abspath(os.path.join(args.outputdir, cnt))
        if not os.path.isdir(tstdir):
            continue
        if cnt.isdigit() or "bin" in cnt:
            print("Submit mergeing for {WORKDIR}".format(WORKDIR=tstdir))
            submit_merge(tstdir, args.rootfile, None, args.queue)