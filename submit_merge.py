#! /usr/bin/env python3

import argparse
import logging
import os
import sys
from tools.cluster_factory import cluster_factory
from tools.run_handler import runhandler
from tools.slurm import launch_job, slurm

repo = os.path.dirname(os.path.abspath(sys.argv[0]))

def create_jobscript(workdir: str, rootfile: str , maxtime: str, dependency=None, queue: str = ""):
    cluster_setup = cluster_factory()
    workerscript = os.path.join(repo, "run_merge.sh")
    jobscriptname = os.path.join(workdir, "jobscript_merge.sh")
    logfile = os.path.join(workdir, "merge.log")
    batchhandler = slurm("merge_sim", logfile, maxtime, "2G")
    batchhandler.configure_from_setup(cluster_setup)
    batchhandler.workdir = workdir
    if dependency:
        batchhandler.dependency = dependency
    if len(queue):
        batchhandler.partition = queue
    batchhandler.init_jobscript(jobscriptname)
    process_runner = runhandler(workerscript, [workdir, rootfile])
    process_runner.initialize(cluster_setup)
    batchhandler.launch(process_runner)
    batchhandler.remove(jobscriptname)
    batchhandler.message("Done ...")
    batchhandler.finish_jobscript()
    return jobscriptname

def submit_merge(outputdir: str, rootfilename: str, dependency=None, queue: str = ""):
    launch_job(create_jobscript(outputdir, rootfilename, "01:00:00", dependency, queue))

if __name__ == "__main__":
    logging.basicConfig(format='[%(levelname)s]: %(message)s', level=logging.INFO)
    parser = argparse.ArgumentParser("submit_merge.py", "Submitter for merge process") 
    parser.add_argument("-o", "--outputdir", metavar="OUTPUTDIR", type=str, required=True, help="Output directory")
    parser.add_argument("-r", "--rootfilename", metavar="ROOTFILENAME", type=str, required=True, help="ROOT filename")
    parser.add_argument("-d", "--dependency", metavar="DEPENDENCY", type=int, default=0, help="Job dependency")
    parser.add_argument("-q", "--queue", metavar="QUEUE", default="gpu", help="Queue/Partition (default: gpu)")
    parser.add_argument("--debug", metavar="DEBUG", action="store_true", help="Enable debug messages")
    args = parser.parse_args()
    loglevel = logging.INFO
    if args.debug:
        loglevel = logging.DEBUG
    logging.basicConfig(format='[%(levelname)s]: %(message)s', level=loglevel)
    dependency = None
    if args.dependency > 0:
        dependency = args.dependency
    submit_merge(args.outputdir, args.rootfilename, dependency, args.queue)