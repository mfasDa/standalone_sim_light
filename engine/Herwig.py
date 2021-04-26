#! /usr/bin/env python3

import os
from tools.processRunner import ProcessRunner
from engine.SimulationEngine import SimulationEngine, SimulationRunner

class HerwigEngine(SimulationEngine):

    def __init__(self, repository: str, runcard: str):
        super(SimulationEngine).init(repository, runcard)
        self.generator = "herwig"
        self.inputfiles = [self.__runcard] + [os.path.join(self.__repository, inputfile) for inputfile in os.listdir(self.__repository, "HerwigIn")]

    def GenerateRuncard(self, cms_energy: float, process: str, events: int, tune: str):
        # See (minimum-bias): http://mcplots.cern.ch/dat/pp/jets/pt/atlas3-akt4/7000/herwig++/2.7.1/default.params
        # See (jet): http://mcplots.cern.ch/dat/pp/jets/pt/cms2011-y0.5/7000/herwig++/2.7.1/default.params
        # See also for minimum-bias: Chapter B.2 https://arxiv.org/abs/0803.0883
        with open(self.__runcard, "w") as myfile:
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

class HerwigRunner(SimulationRunner):

    def __init__(self, runcard: str, events: int, seed: int):
        super(SimulationRunner).__init__(runcard, events, seed)
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