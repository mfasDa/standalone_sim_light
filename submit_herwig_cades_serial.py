#! /usr/bin/env python3
import argparse
import logging
import os
import sys

from tools.cluster_factory import cluster_factory
from tools.slurm import slurm, launch_job
from tools.run_handler import runhandler
from tools.singularity import singularity_engine
from submit_merge import submit_merge

sourcedir = os.path.dirname(os.path.abspath(sys.argv[0]))

def GenerateHerwigInput(cms_energy: float, process: str, events: int, outputdir: str, tune: str):
    # See (minimum-bias): http://mcplots.cern.ch/dat/pp/jets/pt/atlas3-akt4/7000/herwig++/2.7.1/default.params
    # See (jet): http://mcplots.cern.ch/dat/pp/jets/pt/cms2011-y0.5/7000/herwig++/2.7.1/default.params
    # See also for minimum-bias: Chapter B.2 https://arxiv.org/abs/0803.0883
    fname = "{}/herwig.in".format(outputdir)
    with open(fname, "w") as myfile:
        myfile.write("read snippets/PPCollider.in\n") # Markus: Take PPCollider.in fron Herwig repositiory instead of custom version
        myfile.write("set /Herwig/Generators/EventGenerator:EventHandler:LuminosityFunction:Energy %f\n" %(cms_energy))
        if process == "mb":
            # MB tune from Herwig repo
            myfile.write("set /Herwig/Shower/ShowerHandler:IntrinsicPtGaussian 2.2*GeV\n")
            myfile.write("read snippets/MB.in\n")
            myfile.write("read snippets/Diffraction.in\n")
        else:
            # Use SoftTune as UE tune for Herwig7 (>= 7.1) based on https://herwig.hepforge.org/tutorials/mpi/tunes.html
            myfile.write("read {}.in\n".format(tune))
            # Set PDF (LO)
            myfile.write("set /Herwig/Partons/HardLOPDF:PDFName CT14lo\n")
            myfile.write("set /Herwig/Partons/ShowerLOPDF:PDFName CT14lo\n")
            myfile.write("set /Herwig/Partons/MPIPDF:PDFName CT14lo\n")
            myfile.write("set /Herwig/Partons/RemnantPDF:PDFName CT14lo\n")
            kthardmin = 0.
            kthardmax = 0.
            if process == "beauty" or process == "charm":
                quarktye = 4 if process == "charm" else 5
                myfile.write("set /Herwig/MatrixElements/MEHeavyQuark:QuarkType {}\n".format(quarktye))
                myfile.write("insert /Herwig/MatrixElements/SubProcess:MatrixElements[0] /Herwig/MatrixElements/MEHeavyQuark\n")
                kthardmin = 0.
                kthardmax = float(cms_energy)
            elif process == "dijet_lo":
                myfile.write("insert /Herwig/MatrixElements/SubProcess:MatrixElements[0] /Herwig/MatrixElements/MEQCD2to2\n")
                kthardmin = 5.
                kthardmax = float(cms_energy)
            elif "ktmin" in process:
                myfile.write("insert /Herwig/MatrixElements/SubProcess:MatrixElements[0] /Herwig/MatrixElements/MEQCD2to2\n")
                kthardmin = int(process.replace("ktmin_", ""))
                kthardmax = float(cms_energy)
            elif "pthard" in process:
                pthardbins = {0: [0., 5.], 1: [5., 7.], 2: [7., 9.], 3: [9., 12.], 4: [12., 16.], 5: [16., 21.], 6: [21., 28.], 7: [28., 36.], 8: [36., 45.],
                              9: [45., 57], 10: [57., 70], 11: [70., 85.], 12: [85., 99.], 13: [99., 115.], 14: [115., 132.], 15: [132., 150.],
                              16: [150., 169], 17: [169., 190.], 18: [190, 212], 19: [212., 235.], 20: [235., 1000.]}
                pthardbin = int(process.replace("pthard_", ""))
                myfile.write("insert /Herwig/MatrixElements/SubProcess:MatrixElements[0] /Herwig/MatrixElements/MEQCD2to2\n")
                kthardmin = pthardbins[pthardbin][0]
                kthardmax = pthardbins[pthardbin][1]
            else:
                print("Process '{}' not implemented for HERWIG!".format(process))
                exit(1)
            myfile.write("set /Herwig/Cuts/JetKtCut:MinKT %f*GeV\n" %(kthardmin))
            myfile.write("set /Herwig/Cuts/JetKtCut:MaxKT %f*GeV\n" %(kthardmax))
            myfile.write("set /Herwig/Cuts/Cuts:MHatMax %f*GeV\n" %(cms_energy))
            myfile.write("set /Herwig/Cuts/Cuts:MHatMin 0.0*GeV\n")
            myfile.write("set /Herwig/UnderlyingEvent/MPIHandler:IdenticalToUE -1\n")

        # Stable particles with a lifetime > 10 mm (decay externally)
        myfile.write("set /Herwig/Decays/DecayHandler:MaxLifeTime 10*mm\n")
        myfile.write("set /Herwig/Decays/DecayHandler:LifeTimeOption Average\n")

        #HEP MC writer
        myfile.write("read snippets/HepMC.in\n")
        myfile.write("set /Herwig/Analysis/HepMC:Filename events.hepmc\n")
        myfile.write("set /Herwig/Analysis/HepMC:PrintEvent {}\n".format(events))
        myfile.write('saverun herwig /Herwig/Generators/EventGenerator\n')

        myfile.close
    return fname

def createJobscript(outputdir: str, maxtime: str, nslots: int, nevents: int, macro: str, queue: str = ""):
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

    batchhandler = slurm("herwig", logfile, maxtime, "4G")
    batchhandler.arraysize = nslots
    if len(queue):
        batchhandler.partition = queue
    batchhandler.configure_from_setup(cluster_config)
    batchhandler.workdir = outputdir
    configdir = os.path.join(sourcedir, "HerwigIn")
    inputfiles = [os.path.join(configdir, fname) for fname in os.listdir(configdir)]
    inputfiles.append(os.path.join(outputdir, "herwig.in"))
    batchhandler.filesForWorkdir = inputfiles
    batchhandler.init_jobscript(jobscriptname)
    batchhandler.message("Running simulation ...")
    batchhandler.write_instruction("SEED=$SLURM_JOBID")
    process_runner = runhandler(os.path.join(sourcedir, "run_herwig_general.sh"), [nevents, "$SEED", macroname])
    process_runner.initialize(cluster_config)
    process_runner.set_logfile("run_herwig.log")
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
    GenerateHerwigInput(2 * energy, process, events, outputdir, uetune)
    jobid = launch_job(createJobscript(outputdir, timelimit, jobs, events, macro, queue))
    if rootfile:
        submit_merge(outputdir, rootfile, jobid, queue)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("submit_herwig.py", "Submitter for POWHEG dijet process")
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
