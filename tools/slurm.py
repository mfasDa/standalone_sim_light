#! /usr/bin/env python3

import os
import subprocess
from tools.cluster_setup import cluster_setup
from tools.run_handler import runhandler

class ScriptNotInitializedException(Exception):

    def __init__(self):
        super(self).__init__()
        
    def __str__(self):
        return "Job script not initialized - call init_jobscript first"

class slurm:

    def __init__(self, jobname: str, logfile: str, timelimit: str, memlimit: str):
        self.__account = None
        self.__partition = "gpu"
        self.__numnodes = 1
        self.__numtasks = 1
        self.__numcores = 1
        self.__memlimit = memlimit
        self.__timelimit = timelimit
        self.__jobname = jobname
        self.__logfile = logfile
        self.__modules = []
        self.__workdir = None
        self.__filesForWorkdir = []
        self.__arraysize = 0
        self.__dependency = None
        self.__scriptwriter = None
        self.__scriptname = None
        self.__clusterconfig = None

    def configure_from_setup(self, batchsetup: cluster_setup):
        self.__clusterconfig = batchsetup
        self.__account = batchsetup.account()
        if batchsetup.basemodules():
            self.__modules = batchsetup.basemodules()

    def add_module(self, module: str):
        self.__modules.append(module)

    def add_modules(self, modules: list):
        self.__modules = self.__modules + modules

    def init_jobscript(self, scriptname):
        self.__scriptname = scriptname
        self.__scriptwriter = open(scriptname, "w")
        self.write_instruction("#! /bin/bash")
        if self.__account:
             self.write_instruction("#SBATCH -A {ACCOUNT}".format(ACCOUNT=self.__account))
        self.write_instruction("#SBATCH -N {NUMNODES}".format(NUMNODES=self.__numnodes))
        self.write_instruction("#SBATCH -n {NUMTASKS}".format(NUMTASKS=self.__numtasks))
        self.write_instruction("#SBATCH -c {NUMCORES}".format(NUMCORES=self.__numcores))
        if self.__arraysize > 0:
            self.write_instruction("#SBATCH --array=0-{MAXSLOTS}".format(MAXSLOTS=self.__arraysize-1))
        if self.__dependency:
            self.write_instruction("#SBATCH --dependency={DEPENDENCY}".format(DEPENDENCY=self.__dependency))
        self.write_instruction("#SBATCH -p {PARTITION}".format(PARTITION=self.__partition))
        self.write_instruction("#SBATCH -J {JOBNAME}".format(JOBNAME=self.__jobname))
        self.write_instruction("#SBATCH -o {LOGFILE}".format(LOGFILE=self.__logfile))
        if self.__clusterconfig and self.__clusterconfig.hasTimeLimit():
            self.write_instruction("#SBATCH -t {TIMELIMIT}".format(TIMELIMIT=self.__timelimit))
        if self.__clusterconfig and self.__clusterconfig.hasMemResource():
            self.write_instruction("#SBATCH --mem={MEMLIMIT}".format(MEMLIMIT=self.__memlimit))
        for module in self.__modules:
            self.write_instruction("module load {MODULE}".format(MODULE=module))
        self.message("Preparing working directories and configurations ...")
        if self.__workdir:
            if self.__arraysize > 0:
                self.write_instruction("WORKDIR=$(printf \"{WORKDIR}/%04d\" $SLURM_ARRAY_TASK_ID)".format(WORKDIR=self.__workdir))
            else:
                self.write_instruction("WORKDIR={WORKDIR}".format(WORKDIR=self.__workdir))
            self.write_instruction("if [ ! -d $WORKDIR ]; then mkdir -p $WORKDIR; fi")
            if len(self.__filesForWorkdir):
                for infile in self.__filesForWorkdir:
                    self.write_instruction("cp {INPUTFILE} $WORKDIR/{FILEBASE}".format(infile, os.path.basebame(infile)))
            self.enter_workdir()

    def write_instruction(self, instruction: str):
        if not self.__scriptwriter:
            raise ScriptNotInitializedException()
        self.__scriptwriter.write("{}\n".format(instruction))

    def message(self, message: str):
        self.write_instruction("echo \"{}\"".format(message))

    def enter_workdir(self):
        self.write_instruction("cd $WORKDIR")

    def launch(self, processrunner: runhandler):
        self.write_instruction(processrunner.launch())

    def remove(self, filename: str, verbose: bool = True, recursive: bool = False):
        cmd = "rm "
        if recursive:
            cmd += "-r "
        if verbose:
            cmd += "-f "
        cmd += filename
        self.write_instruction(cmd)

    def finish_jobscript(self):
        if not self.__scriptwriter:
            raise ScriptNotInitializedException()
        self.__scriptwriter.close()
    
    def set_accout(self, account: str):
        self.__account = account

    def set_arraysize(self, arraysize: int):
        self.__arraysize = arraysize

    def set_dependency(self, dependency: int):
        self.__dependency = dependency

    def set_partition(self, partition: str):
        self.__partition = partition

    def set_numnodes(self, numnodes: int):
        self.__numnodes = numnodes

    def set_numtasks(self, numtasks: int):
        self.__numtasks = numtasks

    def set_numcores(self, numcores: int):
        self.__numcores = numcores
    
    def set_timelimit(self, timelimit: str):
        self.__timelimit = timelimit

    def set_memlimit(self, memlimit: str):
        self.__memlimit = memlimit

    def set_jobname(self, jobname: str):
        self.__jobname = jobname
    
    def set_logfile(self, logfile: str):
        self.__logfile = logfile

    def set_workdir(self, workdir: str):
        self.__workdir = workdir

    def set_files_for_workdir(self, inputfiles: list):
        self.__filesForWorkdir = inputfiles

    def add_file_for_workdir(self, inputfile: str):
        self.__filesForWorkdir.append(inputfile)
    
    def add_files_for_workdir(self, inputfiles: list):
        for fl in inputfiles:
            self.add_file_for_workdir(fl)
    
    def get_accout(self) -> str:
        return self.__account

    def get_jobscriptname(self)-> str:
        return self.__scriptname

    def get_arraysize(self) -> int:
        return self.__arraysize

    def get_dependency(self) -> int:
        return self.__dependency

    def get_partition(self) -> str:
        return self.__partition

    def get_numnodes(self) -> str:
        return self.__numnodes

    def get_numtasks(self) -> str:
        return self.__numtasks

    def get_numcores(self) -> str:
        return self.__numcores
    
    def get_timelimit(self) -> str:
        return self.__timelimit

    def get_memlimit(self) -> str:
        return self.__memlimit

    def get_jobname(self) -> str:
        return self.__jobname
    
    def get_logfile(self) -> str:
        return self.__logfile

    def get_workdir(self) -> str:
        return self.__workdir

    def get_files_for_workdir(self) -> list:
        return self.__filesForWorkdir

    account = property(fget=get_accout, fset=set_accout)
    arraysize = property(fget=get_arraysize, fset=set_arraysize)
    dependency = property(fget=get_dependency, fset=set_dependency)
    partition = property(fget=get_partition, fset=set_partition)
    numnodes = property(fget=get_numnodes, fset=set_numnodes)
    numtasks = property(fget=get_numtasks, fset=set_numtasks)
    numcores = property(fget=get_numcores, fset=set_numcores)
    timelimit = property(fget=get_timelimit, fset=set_timelimit)
    memlimit = property(fget=get_memlimit, fset=set_memlimit)
    jobname = property(fget=get_jobname, fset=set_jobname)
    logfile = property(fget=get_logfile, fset=set_logfile)
    workdir = property(fget=get_workdir, fset=set_workdir)
    filesForWorkdir = property(fget=get_files_for_workdir, fset=set_files_for_workdir)


def launch_job(jobscript: str):
    resultSlots = subprocess.run(["sbatch", jobscript], stdout=subprocess.PIPE)
    soutSlots = resultSlots.stdout.decode("utf-8")
    toks = soutSlots.split(" ")
    jobid = int(toks[len(toks)-1])
    print("Submitted batch job {JOBID}".format(JOBID=jobid))
    return jobid