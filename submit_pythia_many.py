#! /usr/bin/env python3

import argparse
import logging
import os

from submit_simulation_analysis_pythia import submit_simulation_analysis_pythia

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="sumbit_merge_many", description="Submitter for pthard/ktmin productions")
    parser.add_argument("-o", "--outputdir", metavar="OUTPUTDIR", type=str, required=True, help="Output base diretory")
    parser.add_argument("-j", "--jobs", type=int, default=1000, help="Number of jobs")
    parser.add_argument("-n", "--nevents", type=int, default=10000, help="Number of events")
    parser.add_argument("-e", "--ebeam", type=int, default=6500, help="Beam energy")        
    parser.add_argument("-m", "--macro", type=str, default = "makeJetSpectrumAndSoftDrop.C", help="Optional run macro")
    parser.add_argument("-r", "--rootfile", type=str, default="", help="ROOT file (for merging, optional)")
    parser.add_argument("-t", "--timelimit", metavar="TIMELIMIT", type=str, default="14:00:00", help="Time limit")
    parser.add_argument("-q", "--queue", metavar="QUEUE", default="gpu", help="Queue/Partition (default: gpu)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug messages")
    parser.add_argument("--minpthard", metavar="MINPTHARD", type=int, default=0, help="Min. pt-hard bin")
    parser.add_argument("--maxpthard", metavar="MAXPTHARD", type=int, default=20, help="Max. pt-hard bin")
    args = parser.parse_args()

    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(format='[%(levelname)s]: %(message)s', level=loglevel)

    rootfile = None
    if len(args.rootfile):
        rootfile = args.rootfile

    logging.info("Submitting PYTHIA for pt-hard bins from %d to %d", args.minpthard, args.maxpthard)
    for ipth in range(args.minpthard, args.maxpthard+1):
        outbindir =os.path.join(args.outputdir, "bin{}".format(ipth))
        submit_simulation_analysis_pythia(outbindir, args.jobs, args.nevents, args.ebeam, ipth, args.macro, args.timelimit, rootfile, args.queue)