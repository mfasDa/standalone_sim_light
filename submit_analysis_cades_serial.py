#! /usr/bin/env python3

import argparse
import logging
import os
import sys

from tools.cluster_factory import cluster_factory
from tools.run_handler import runhandler
from tools.slurm import launch_job, slurm 
from submit_merge import submit_merge

sourcedir = os.path.dirname(os.path.abspath(sys.argv[0]))

class AnalysisChunk:

    def __init__(self, workdir):
        self.__workdir = workdir
        self.__files = []

    def hasFiles(self) -> bool:
        return len(self.__files) > 0

    def add_file(self, hepmcfile : str):
        self.__files.append(hepmcfile)

    def build(self):
        if not os.path.exists(self.__workdir):
            os.makedirs(self.__workdir, 0o755)
        with open(os.path.join(self.__workdir, "inputfiles.txt"), "w") as filewriter:
            for hepfile in self.__files:
                filewriter.write("{}\n".format(hepfile))
            filewriter.close()

def find_hepmcfiles(inputdir: str) -> list:
    result = []
    for root, dirs, files in os.walk(inputdir):
        for fl in files:
            if "hepmc" in fl:
                result.append(os.path.join(root, fl))
    return sorted(result)

def create_jobscript(inputbase: str, outputdir: str, filesperjob: int, macro: str, maxtime: str, queue: str = ""):
    if not os.path.exists(outputdir):
        os.makedirs(outputdir, 0o755)

    macroname=macro
    if not "/" in macro:
        macrolocation = os.path.join(sourcedir, "macros")
        logging.info("Loading macro from defuault macro location %s", macrolocation)
        macroname = os.path.join(macrolocation, macro)

    # preare directory structure with file lists to analyse
    nchunk = 0
    ncurrentfiles = 0
    currentchunk = None
    for currenthepfile in find_hepmcfiles(inputbase):
        if not currentchunk:
            currentchunk = AnalysisChunk(os.path.join(outputdir, "%04d" %nchunk))
        elif ncurrentfiles == filesperjob:
            currentchunk.build()
            nchunk += 1
            ncurrentfiles = 0
            currentchunk = AnalysisChunk(os.path.join(outputdir, "%04d" %nchunk))
        currentchunk.add_file(currenthepfile)
        ncurrentfiles += 1
    if currentchunk.hasFiles():
        currentchunk.build()
        nchunk += 1

    jobscriptname = os.path.join(outputdir, "jobscript.sh")
    logdir = os.path.join(outputdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "joboutput_%a.log")

    cluster_setup = cluster_factory()
    batchhandler = slurm("hepmc_analysis", logfile, maxtime, "4G")
    batchhandler.configure_from_setup(cluster_setup)
    if len(queue):
        batchhandler.partition = queue
    batchhandler.arraysize = nchunk
    batchhandler.workdir = outputdir
    batchhandler.init_jobscript(jobscriptname)
    batchhandler.message("Starting analysis in current workdir ...")
    process_runner = runhandler(sourcedir, os.path.join(sourcedir, "run_analysis_general.sh"), ["$WORKDIR/inputfiles.txt", "$WORKDIR", macroname])
    process_runner.initialize(cluster_setup)
    process_runner.set_logfile("run_analysis.log")
    batchhandler.launch(process_runner)
    batchhandler.remove(jobscriptname)
    batchhandler.message("Job done ...")
    batchhandler.finish_jobscript()
    return jobscriptname

def submit_analysis_cades(inputdir: str, outputdir: str, numfiles: int, macro: str, timelimit, rootfile = None, queue: str = ""):
    jobid = launch_job(create_jobscript(inputdir, outputdir, numfiles, macro, timelimit, queue))
    if rootfile:
        submit_merge(outputdir, rootfile, jobid, queue)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_analysis_cades_serial.py", "Submitter for analysis on existing hepmc output")
    parser.add_argument("-i", "--inputdir", metavar="INPUTDIR", type=str, required=True, help="Input directory")
    parser.add_argument("-o", "--outputdir", metavar="OUTPUTDIR", type=str, required=True, help="Output directory")
    parser.add_argument("-m", "--macro", metavar="MACRO", type=str, default="makeJetSpectrumAndSoftDrop.C", help="Macro to be processed")
    parser.add_argument("-n", "--nfiles", metavar="NFILES", type=int, default=10, help="Number of files per slot")
    parser.add_argument("-r", "--rootfile", metavar="ROOTFILE", type=str, default="", help="Name of the resulting roofile (for merging)")
    parser.add_argument("-t", "--timelimit", metavar="TIMELIMIT", type=str, default="10:00:00", help="Max. time per slot")
    parser.add_argument("-q", "--queue", metavar="QUEUE", default="gpu", help="Queue/Partition (default: gpu)")
    parser.add_argument("-d" ,"--debug", metavar="DEBUG", action="store_true", help="Enable debug printouts")
    args = parser.parse_args()
    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(format='[%(levelname)s]: %(message)s', level=loglevel)
    rootfile = None
    if len(args.rootfile):
        rootfile = args.rootfile
    submit_analysis_cades(args.inputdir, args.outputdir, args.nfiles, args.macro, args.timelimit, rootfile, args.queue)