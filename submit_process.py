#! /usr/bin/env python3

import argparse
import os
import sys

from submit_herwig_cades_serial import submit_herwig_cades

if __name__ == "__main__":
    sourcedir = os.path.abspath(os.path.dirname(sys.argv[0]))
    parser = argparse.ArgumentParser("submit_process.py", "Sumbitter for HERWIG CADES jobs")
    parser.add_argument("-o", "--outputdir", type=str, required=True, help="local working directory")
    parser.add_argument("-j", "--jobs", type=int, default=1000, help="Number of jobs")
    parser.add_argument("-n", "--nevents", type=int, default=10000, help="Number of events")
    parser.add_argument("-e", "--ebeam", type=int, default=6500, help="Beam energy")        
    parser.add_argument("-p", "--process", type=str, default="pthard", help="Process (pthard or ktmin)")
    parser.add_argument("-m", "--macro", type=str, default = "makeJetSpectrumAndSoftDrop.C", help="Optional run macro")
    parser.add_argument("-r", "--rootfile", type=str, default="", help="ROOT file (for merging, optional)")
    parser.add_argument("-t", "--time", metavar="TIME", type=str, default="10:00:00", help="Max. time")
    parser.add_argument("-q", "--queue", metavar="QUEUE", default="gpu", help="Queue/Partition (default: gpu)")
    parser.add_argument("-u", "--uetune", metavar="UETUNE", type=str, default="SoftTune", help="Underlying event tune (SoftTune or DefaultTune) - LO process only")
    args = parser.parse_args()
    macrodir = "{REPO}/macros".format(REPO=sourcedir)
    macroname = os.path.join(macrodir, args.macro)
    rootfile=None
    if len(args.rootfile):
        rootfile = args.rootfile

    outputdirgen = None
    binning = []
    if args.process == "pthard":
        binning = [x for x in range(0, 21)]
        outputdirgen = lambda ipth: "bin{}".format(ipth) 
    elif args.process == "ktmin":
        binning = sorted([0, 5, 10, 15, 20, 30, 40, 50, 90, 150, 230])
        outputdirgen = lambda ipth: "%02d" %(ipth)
    else:
        print("Process {PROCESS} unknown. Select either".format(args.process))
        sys.exit(1)

    for ipth in binning:
        outbindir =os.path.join(args.outputdir, outputdirgen(ipth))
        process = "{PROCESS}_{BIN}".format(PROCESS=args.process, BIN=ipth) 
        submit_herwig_cades(outbindir, args.jobs, args.nevents, args.ebeam, process, macroname, args.time, args.uetune, rootfile)
