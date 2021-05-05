#! /usr/bin/env python3

import os
from tools.processRunner import ProcessRunner
from engine.SimulationEngine import Process, RunCard, PtHardHandler, SimulationEngine, SimulationParam, SimulationRunner

class HerwigRuncard(RunCard):

    class MBProcess(Process):

        def __init__(self):
            super().__init__()

        def encode(self, runcard: RunCard):
            runcard.write_instruction("set /Herwig/Shower/ShowerHandler:IntrinsicPtGaussian 2.2*GeV")
            runcard.write_instruction("read snippets/MB.in")
            runcard.write_instruction("read snippets/Diffraction.in")

    class HardProcess(Process):

        def __init__(self):
            super().__init__()
            self.__ktmin = -1.
            self.__ktmax = -1.
            self.__mtmax = -1.
            self.__pdfset = ""
            self.__tune = ""

        def configure(self, ktmin: float, ktmax: float, mtmax: float):
            self.__ktmin = ktmin
            self.__ktmax = ktmax
            self.__mtmax = mtmax

        def set_tune(self, tune):
            self.__tune = tune

        def encode(self, runcard: RunCard):
            self._build_matrixelement(runcard)
            if len(self.__tune):
                runcard.write_instruction("read {}.in".format(self.__tune))
            self.__build_kthardrange(runcard)
            self.__build_pdfset(runcard)
            runcard.write_instruction("set /Herwig/UnderlyingEvent/MPIHandler:IdenticalToUE -1")

        def _build_matrixelement(self, runcard: RunCard):
            pass

        def __build_pdfset(self, runcard: RunCard):
            runcard.write_instruction("set /Herwig/Partons/HardLOPDF:PDFName {}".format(self.__pdfset))
            runcard.write_instruction("set /Herwig/Partons/ShowerLOPDF:PDFName {}".format(self.__pdfset))
            runcard.write_instruction("set /Herwig/Partons/MPIPDF:PDFName {}".format(self.__pdfset))
            runcard.write_instruction("set /Herwig/Partons/RemnantPDF:PDFName {}".format(self.__pdfset))

        def __build_kthardrange(self, runcard: RunCard):
            runcard.write_instruction("set /Herwig/Cuts/JetKtCut:MinKT %f*GeV" %(self.__ktmin))
            runcard.write_instruction("set /Herwig/Cuts/JetKtCut:MaxKT %f*GeV" %(self.__ktmax))
            runcard.write_instruction("set /Herwig/Cuts/Cuts:MHatMax %f*GeV" %(self.__mtmax))
            runcard.write_instruction("set /Herwig/Cuts/Cuts:MHatMin 0.0*GeV")


    class DijetProcess(HardProcess):
        
        def __init__(self):
            super().__init__()

        def _build_matrixelement(self, runcard: RunCard):
            runcard.write_instruction("insert /Herwig/MatrixElements/SubProcess:MatrixElements[0] /Herwig/MatrixElements/MEQCD2to2")

    class HeavyFlavourProcess(HardProcess):

        def __init__(self, quarktype: str):
            super().__init__()
            self.__quarktype = quarktype

        def _build_matrixelement(self, runcard: RunCard):
            quarktype = 4 if self.__quarktype == "charm" else 5
            runcard.write_instruction("set /Herwig/MatrixElements/MEHeavyQuark:QuarkType {}".format(quarktype))
            runcard.write_instruction("insert /Herwig/MatrixElements/SubProcess:MatrixElements[0] /Herwig/MatrixElements/MEHeavyQuark")

    def __init__(self, name: str):
        super().__init__(name)
        self.__cmsenergy = 0.
        self.__hepmcfile = ""
        self.__events = 0
        self.__processes = []

    def set_hepmcfile(self, hepmcfile: str):
        self.__hepmcfile = hepmcfile

    def set_events(self, events: int):
        self.__events = events

    def set_cmsenergy(self, energy: float):
        self.__cmsenergy = energy

    def add_process(self, process: Process):
        self.__processes.append(process)

    def build(self):
        self.write_instruction("read snippets/PPCollider.in")
        self.write_instruction("set /Herwig/Generators/EventGenerator:EventHandler:LuminosityFunction:Energy %f" %(self.__cmsenergy))
        for proc in self.__processes:
            proc.encode()

        # Stable particles with a lifetime > 10 mm (decay externally)
        self.write_instruction("set /Herwig/Decays/DecayHandler:MaxLifeTime 10*mm")
        self.write_instruction("set /Herwig/Decays/DecayHandler:LifeTimeOption Average")

        #HEP MC writer
        self.write_instruction("read snippets/HepMC.in\n")
        self.write_instruction("set /Herwig/Analysis/HepMC:Filename {}".format(self.__hepmcfile))
        self.write_instruction("set /Herwig/Analysis/HepMC:PrintEvent {}".format(self.__events))
        self.write_instruction('saverun herwig /Herwig/Generators/EventGenerator')

class HerwigEngine(SimulationEngine):

    def __init__(self, repository: str, runcard: str):
        super().__init__(repository, runcard)
        self.generator = "herwig"
        self.inputfiles = [self._runcard] + [os.path.join(self._repository, inputfile) for inputfile in os.listdir(self._repository, "HerwigIn")]
        self.__runcard = HerwigRuncard(self._runcard)

    def generate_runcard(self, params: SimulationParam):
        # See (minimum-bias): http://mcplots.cern.ch/dat/pp/jets/pt/atlas3-akt4/7000/herwig++/2.7.1/default.params
        # See (jet): http://mcplots.cern.ch/dat/pp/jets/pt/cms2011-y0.5/7000/herwig++/2.7.1/default.params
        # See also for minimum-bias: Chapter B.2 https://arxiv.org/abs/0803.0883
        self.__runcard.set_cmsenergy(params.cms_energy)
        if params.process == "mb":
            self.__runcard.add_process(HerwigRuncard.MBProcess())
        else:
            process: HerwigRuncard.HardProcess = None
            ktmin = 0 
            ktmax = params.cms_energy
            if params.process == "charm" or params.process == "beauty":
                process = HerwigRuncard.HeavyFlavourProcess(params.process)
            elif params.process == "dijet_lo":
                process = HerwigRuncard.DijetProcess()
                ktmin = 5.
            elif params.process == "ktmin":
                process = HerwigRuncard.DijetProcess()
                ktmin = params.ktmin
            elif params.process == "pthard":
                pthardhandler = PtHardHandler()
                pthardlimits = pthardhandler.get_limits(params.pthardbin)
                ktmin = pthardlimits[0]
                ktmax = pthardlimits[1]                
                process = HerwigRuncard.DijetProcess()
            else:       
                print("Process '{}' not implemented for HERWIG!".format(params.process))
                exit(1)
            process.configure(ktmin, ktmax, 0.)
            process.set_tune(params.tune)
            self.__runcard.add_process(process)
        self.__runcard.build()


class HerwigRunner(SimulationRunner):

    def __init__(self, runcard: str, events: int, seed: int):
        super().__init__(runcard, events, seed)
        self.modules = ["Herwig/latest"]

    def launch(self):
        herwig_repository="$HERWIG_ROOT/share/Herwig/HerwigDefaults.rpo"
        runsteer = ProcessRunner()
        for module in self.modules:
            runsteer.load_module(module)
        runsteer.print_modules()
        runsteer.source_script("$CLUSTER_HOME/lhapdf_data_setenv")
        runsteer.write_instruction("Herwig --repo={REPO} read {RUNCARD} &> hw_setup.log".format(REPO=herwig_repository, RUNCARD=self._runcard))
        runsteer.write_instruction("Herwig --repo={REPO} run herwig.run -N {EVENTS} -s {SEED} &> hw_run.log".format(REPO=herwig_repository, EVENTS=self._events, SEED=self._seed))
        runsteer.execute()