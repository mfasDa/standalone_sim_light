#! /usr/bin/env python3

import os
from tools.processRunner import ProcessRunner
from engine.SimulationEngine import PtHardHandler, SimulationEngine, SimulationParam, SimulationRunner

class HerwigEngine(SimulationEngine):

    def __init__(self, repository: str, runcard: str):
        super().__init__(repository, runcard)
        self.generator = "herwig"
        self.inputfiles = [self._runcard] + [os.path.join(self._repository, inputfile) for inputfile in os.listdir(self._repository, "HerwigIn")]

    def generate_runcard(self, params: SimulationParam):
        # See (minimum-bias): http://mcplots.cern.ch/dat/pp/jets/pt/atlas3-akt4/7000/herwig++/2.7.1/default.params
        # See (jet): http://mcplots.cern.ch/dat/pp/jets/pt/cms2011-y0.5/7000/herwig++/2.7.1/default.params
        # See also for minimum-bias: Chapter B.2 https://arxiv.org/abs/0803.0883
        with open(self._runcard, "w") as myfile:
            myfile.write("read snippets/PPCollider.in\n") # Markus: Take PPCollider.in fron Herwig repositiory instead of custom version
            myfile.write("set /Herwig/Generators/EventGenerator:EventHandler:LuminosityFunction:Energy %f\n" %(params.cms_energy))
            if params.process == "mb":
                # MB tune from Herwig repo
                myfile.write("set /Herwig/Shower/ShowerHandler:IntrinsicPtGaussian 2.2*GeV\n")
                myfile.write("read snippets/MB.in\n")
                myfile.write("read snippets/Diffraction.in\n")
            else:
                # Use SoftTune as UE tune for Herwig7 (>= 7.1) based on https://herwig.hepforge.org/tutorials/mpi/tunes.html
                myfile.write("read {}.in\n".format(params.tune))
                # Set PDF (LO)
                self.__configure_pdfset(myfile, params.pdfset)
                kthardmin = 0.
                kthardmax = 0.
                self.__configure_Matrixelement(myfile, params.process)
                if params.process == "beauty" or params.process == "charm":
                    kthardmin = 0.
                    kthardmax = params.cms_energy
                elif params.process == "dijet_lo":
                    kthardmin = 5.
                    kthardmax = params.cms_energy
                elif params.process == "ktmin":
                    kthardmin = params.ktmin
                    kthardmax = params.cms_energy
                elif params.process == "pthard":
                    pthardhandler = PtHardHandler()
                    pthardlimits = pthardhandler.get_limits(params.pthardbin)
                    kthardmin = pthardlimits[0]
                    kthardmax = pthardlimits[1]
                else:
                    print("Process '{}' not implemented for HERWIG!".format(params.process))
                    exit(1)
                if kthardmax > 0.:
                    self.__configure_kthardrange(myfile, kthardmin, kthardmax, params.cms_energy)
                myfile.write("set /Herwig/UnderlyingEvent/MPIHandler:IdenticalToUE -1\n")

            # Stable particles with a lifetime > 10 mm (decay externally)
            myfile.write("set /Herwig/Decays/DecayHandler:MaxLifeTime 10*mm\n")
            myfile.write("set /Herwig/Decays/DecayHandler:LifeTimeOption Average\n")

            #HEP MC writer
            myfile.write("read snippets/HepMC.in\n")
            myfile.write("set /Herwig/Analysis/HepMC:Filename {}\n".format(params.hepmcfile))
            myfile.write("set /Herwig/Analysis/HepMC:PrintEvent {}\n".format(params.events))
            myfile.write('saverun herwig /Herwig/Generators/EventGenerator\n')

            myfile.close()

    def __configure_Matrixelement(self, runcard, process: str):
        mename = ""
        if process == "dijet_lo" or process == "ktmin" or process == "pthard":
            mename = "MEQCD2to2"
        elif process == "charm" or process == "beauty":
            mename = "MEHeavyQuark"
            runcard.write("set /Herwig/MatrixElements/MEHeavyQuark:QuarkType {}\n".format(4 if process == "charm" else 5))
        runcard.write("insert /Herwig/MatrixElements/SubProcess:MatrixElements[0] /Herwig/MatrixElements/{}\n".format(mename))

    def __configure_pdfset(self, runcard, pdfset: str):
        runcard.write("set /Herwig/Partons/HardLOPDF:PDFName {}\n".format(pdfset))
        runcard.write("set /Herwig/Partons/ShowerLOPDF:PDFName {}\n".format(pdfset))
        runcard.write("set /Herwig/Partons/MPIPDF:PDFName {}\n".format(pdfset))
        runcard.write("set /Herwig/Partons/RemnantPDF:PDFName {}\n".format(pdfset))

    def __configure_kthardrange(self, runcard, ktmin: float, ktmax: float, mhat_max: float):
        runcard.write("set /Herwig/Cuts/JetKtCut:MinKT %f*GeV\n" %(ktmin))
        runcard.write("set /Herwig/Cuts/JetKtCut:MaxKT %f*GeV\n" %(ktmax))
        runcard.write("set /Herwig/Cuts/Cuts:MHatMax %f*GeV\n" %(mhat_max))
        runcard.write("set /Herwig/Cuts/Cuts:MHatMin 0.0*GeV\n")

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
        runsteer.source_script("$HOME/lhapdf_data_setenv")
        runsteer.write_instruction("Herwig --repo={REPO} read {RUNCARD} &> hw_setup.log".format(REPO=herwig_repository, RUNCARD=self.runcard))
        runsteer.write_instruction("Herwig --repo={REPO} run herwig.run -N {EVENTS} -s {SEED} &> hw_run.log".format(REPO=herwig_repository, EVENTS=self.events, SEED=self.seed))
        runsteer.execute()