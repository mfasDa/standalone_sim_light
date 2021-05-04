#! /usr/bin/env python3

import argparse
import logging
import os

from submit_analysis_cades_serial import submit_analysis_cades

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="sumbit_merge_many", description="Submitter for pthard/ktmin productions")
    parser.add_argument("-i", "--inputdir", metavar="INPUTDIR", type=str, required=True, help="Output base diretory")
    parser.add_argument("-o", "--outputdir", metavar="OUTPUTDIR", type=str, required=True, help="Output base diretory")
    parser.add_argument("-m", "--macro", metavar="MACRO", type=str, default="makeJetSpectrumAndSoftDrop.C", help="Macro to be processed")
    parser.add_argument("-n", "--numfiles", metavar="NUMFILES", type=int, default=10, help="Number of files to analyse per slot")
    parser.add_argument("-r", "--rootfile", metavar="ROOTFILE", type=str, default="", help="Name of the rootfile")
    parser.add_argument("-t", "--timelimit", metavar="TIMELIMIT", type=str, default="10:00:00", help="Time limit")
    parser.add_argument("-q", "--queue", metavar="QUEUE", default="gpu", help="Queue/Partition (default: gpu)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug messages")
    args = parser.parse_args()

    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(format='[%(levelname)s]: %(message)s', level=loglevel)

    rootfile = None
    if len(args.rootfile):
        rootfile = args.rootfile

    for cnt in sorted(os.listdir(args.inputdir)):
        tstdir = os.path.abspath(os.path.join(args.inputdir, cnt))
        outwork = os.path.abspath(os.path.join(args.outputdir, cnt))
        if not os.path.isdir(tstdir):
            continue
        if cnt.isdigit() or "bin" in cnt:
            print("Submit analysis for {WORKDIR} to outputdir {OUTPUTDIR}".format(WORKDIR=tstdir, OUTPUTDIR=outwork))
            submit_analysis_cades(tstdir, outwork, args.numfiles, args.macro, args.timelimit, rootfile, args.queue)
    pass