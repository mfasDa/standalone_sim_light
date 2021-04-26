#! /usr/bin/env python3
import argparse
import logging
import os
import sys
from tools.cluster_setup import cluster_setup

from tools.run_handler import runhandler
from tools.cluster_factory import cluster_factory
from tools.slurm import slurm, launch_job
from submit_merge import submit_merge

sourcedir = os.path.dirname(os.path.abspath(sys.argv[0]))

def createJobscript(outputdir: str, maxtime: str, nslots: int, nevents: int, energy_cms: float, pthardbin: int, macro: str, queue: str = "gpu"):
    cluster_setup = cluster_factory()

    jobscriptname = os.path.join(outputdir, "jobscript.sh")
    logdir = os.path.join(outputdir, "logs")
    if not os.path.exists(logdir):
        os.makedirs(logdir, 0o755)
    logfile = os.path.join(logdir, "joboutput_%a.log")

    macroname=macro
    if not "/" in macro:
        macrolocation = os.path.join(sourcedir, "macros")
        logging.info("Loading macro from defuault macro location %s", macrolocation)
        macroname = os.path.join(macrolocation, macro)

    batchhandler = slurm("pythia", logfile, maxtime, "4G")
    if len(queue):
        batchhandler.partition = queue
    batchhandler.arraysize = nslots
    batchhandler.workdir = outputdir
    batchhandler.configure_from_setup(cluster_setup)
    batchhandler.init_jobscript(jobscriptname)
    batchhandler.message("Running simulation ...")
    batchhandler.write_instruction("SEED=$SLURM_JOBID")
    process_runner = runhandler(os.path.join(sourcedir, "run_pythia_general.sh"), [nevents, "$SEED", energy_cms, pthardbin, macroname])
    process_runner.initialize(cluster_setup)
    process_runner.set_logfile("run_pythia.log")
    batchhandler.launch(process_runner)
    batchhandler.remove(jobscriptname)
    batchhandler.message("Job done ...")
    batchhandler.finish_jobscript() 
    return jobscriptname


def submit_simulation_analysis_pythia(outputdir: str, jobs: int, events: int, energybeam: float, pthardbin: int, macro: str, timelimit: str, rootfile=None, queue: str = ""):
    logging.basicConfig(format='[%(levelname)s]: %(message)s', level=logging.INFO)
    if not os.path.exists(outputdir):
        os.makedirs(outputdir, 0o755)
    jobid = launch_job(createJobscript(outputdir, timelimit, jobs, events, 2*energybeam, pthardbin, macro, queue))
    if rootfile:
        submit_merge(outputdir, rootfile, jobid, queue)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_herwig.py", "Submitter for POWHEG dijet process")
    parser.add_argument("-j", "--jobs", metavar="NJOBS", type=int, default = 10, help="Number of jobs")
    parser.add_argument("-n", "--nevents", metavar="NEVENTS", type=int, default=50000, help="Number of events")
    parser.add_argument("-e", "--ebeam", metavar="EBEAM", type=float, default=6500, help="Beam energy")
    parser.add_argument("-p", "--pthardbin", metavar="PTHARDBIN", type=int, required=True, help="Beam energy")
    parser.add_argument("-m", "--macro", metavar="MACRO", type=str, default="makeJetSpectrumAndSoftDrop.C", help="run macro")
    parser.add_argument("-o", "--outputdir", metavar="OUTPUTDIR", type=str, required=True, help="Output directory")
    parser.add_argument("-r", "--rootfile", metavar="ROOTFILE", type=str, default="", help="ROOT file name (for merging, optional)")
    parser.add_argument("-t", "--time", metavar="TIME", default="10:00:00", help="Max. time")
    parser.add_argument("-q", "--queue", metavar="QUEUE", default="gpu", help="Queue/Partition (default: gpu)")
    parser.add_argument("-d" ,"--debug", action="store_true", help="Enable debug printouts")
    args = parser.parse_args()
    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(format='[%(levelname)s]: %(message)s', level=loglevel)
    rootfile = None
    if len(args.rootfile):
        rootfile = args.rootfile
    submit_simulation_analysis_pythia(args.outputdir, args.jobs, args.nevents, args.ebeam, args.pthardbin, args.macro, args.time, rootfile, args.queue)