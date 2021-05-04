#! /usr/bin/env python3
import argparse
from tools.cluster_setup import cluster_setup
from engine.SimulationEngine import SimulationEngine, SimulationParam
import logging
import os
import sys

from engine.Herwig import HerwigEngine
from tools.cluster_factory import cluster_factory
from tools.slurm import slurm, launch_job
from tools.run_handler import runhandler
from submit_merge import submit_merge

sourcedir = os.path.dirname(os.path.abspath(sys.argv[0]))

def createJobscript(outputdir: str, maxtime: str, nslots: int, nevents: int, macro: str, engine: SimulationEngine, queue: str = ""):
    cluster_config = cluster_factory()
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

    batchhandler = slurm(engine.generator, logfile, maxtime, "4G")
    batchhandler.arraysize = nslots
    if len(queue):
        batchhandler.partition = queue
    batchhandler.configure_from_setup(cluster_config)
    batchhandler.workdir = outputdir
    batchhandler.filesForWorkdir = engine.inputfiles
    batchhandler.init_jobscript(jobscriptname)
    batchhandler.message("Running simulation ...")
    batchhandler.write_instruction("SEED=$SLURM_JOBID")
    process_runner = runhandler(sourcedir, os.path.join(sourcedir, "simrun.sh"), [cluster_config.name(), engine.generator, os.path.basename(engine.runcard), nevents, "$SEED", macroname])
    process_runner.initialize(cluster_config)
    process_runner.set_logfile("run_{GENERATOR}.log".format(GENERATOR=engine.generator))
    batchhandler.launch(process_runner)
    batchhandler.remove(jobscriptname)
    batchhandler.message("Job done ...")
    batchhandler.finish_jobscript() 
    return jobscriptname

def submit_herwig_cades(outputdir: str, jobs: int, events: int, energy: float, process: str, macro: str, timelimit: str, uetune: str, rootfile=None, queue: str = ""):
    logging.basicConfig(format='[%(levelname)s]: %(message)s', level=logging.INFO)
    support_tunes = ["SoftTune", "DefaultTune"]
    if not uetune in support_tunes:
        logging.error("Tune %s not supported - select either SoftTune (default) or DefaultTune ...", uetune)
        return
    if not os.path.exists(outputdir):
        os.makedirs(outputdir, 0o755)

    engine = HerwigEngine(sourcedir, os.path.join(outputdir, "herwig.in"))
    params = SimulationParam()
    params.beam_energy = energy
    params.events = events
    params.pdfset = "CT14lo"
    params.hepmcfile = "events.hepmc"
    params.tune = uetune
    if "pthard" in process:
        params.process = "pthard"
        params.pthardbin = int(process.replace("pthard_", ""))
    elif "ktmin" in process:
        params.process = "ktmin"
        params.kthardmin = int(process.replace("ktmin_", ""))
    else:
        params.process = process
    engine.generate_runcard(params)
    jobid = launch_job(createJobscript(outputdir, timelimit, jobs, events, macro, engine, queue))
    if rootfile:
        submit_merge(outputdir, rootfile, jobid, queue)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_herwig.py", "Submitter for HERWIG dijet process")
    parser.add_argument("-j", "--jobs", metavar="NJOBS", type=int, default = 10, help="Number of jobs")
    parser.add_argument("-n", "--nevents", metavar="NEVENTS", type=int, default=50000, help="Number of events")
    parser.add_argument("-e", "--ebeam", metavar="EBEAM", type=float, default=6500, help="Beam energy")
    parser.add_argument("-p", "--process", metavar="PROCESS", type=str, default="mb", help="Beam energy")
    parser.add_argument("-m", "--macro", metavar="MACRO", type=str, default="makeJetSpectrumAndSoftDrop.C", help="run macro")
    parser.add_argument("-o", "--outputdir", metavar="OUTPUTDIR", type=str, required=True, help="Output directory")
    parser.add_argument("-r", "--rootfile", metavar="ROOTFILE", type=str, default="", help="ROOT file name (for merging, optional)")
    parser.add_argument("-t", "--time", metavar="TIME", default="10:00:00", help="Max. time")
    parser.add_argument("-q", "--queue", metavar="QUEUE", default="gpu", help="Queue/Partition (default: gpu)")
    parser.add_argument("-d" ,"--debug", action="store_true", help="Enable debug printouts")
    parser.add_argument("-u", "--uetune", metavar="UETUNE", type=str, default="SoftTune", help="Underlying event tune (SoftTune or DefaultTune)")
    args = parser.parse_args()
    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(format='[%(levelname)s]: %(message)s', level=loglevel)
    rootfile = None
    if len(args.rootfile):
        rootfile = args.rootfile
    submit_herwig_cades(args.outputdir, args.jobs, args.nevents, args.ebeam, args.process, args.macro, args.time, args.uetune, rootfile)
