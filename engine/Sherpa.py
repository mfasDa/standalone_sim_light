#! /usr/bin/env python3

import os
from engine.SimulationEngine import RunCard, SimulationEngine, SimulationRunner, SimulationParam
from tools.processRunner import ProcessRunner

class SherpaRuncard(RunCard):

    class Beam:

        def __init__(self, id: int, pdg: int, energy: int):
            self.__id = id
            self.__pdg = pdg
            self.__energy = energy

        def encode(self) -> str:
            return "BEAM_{ID} {PDG}: BEAM_ENERGY_{ID} {ENERGY};".format(ID=self.__id, PDG=self.__pdg, ENERGY=self.__energy)

    class JetSelector:

        def __init__(self, algorithm: str, njets: int, radius:float, ptmin: float, etmin: float):
            self.__algorithm = algorithm
            self.__njets = njets
            self.__ptmin = ptmin
            self.__etmin = etmin
            self.__radius = radius

        def encode(self) -> str:
            algorithms = {"kt": 1, "antikt": -1}
            if not self.__algorithm in algorithms:
                return ""
            algorithm = algorithms[self.__algorithm]
            return "NJetFinder {NJET} {PTMIN} {ETMIN} {RADIUS} {ALGORITHM}".format(NJET=self.__njets, PTMIN=self.__ptmin, ETMIN=self.__etmin, RADIUS=self.__radius, ALGORITHM=algorithm)

    class Process:

        def __init__(self):
            pass

        def encode(self, runcard: RunCard):
            pass

    class DijetProcess(Process):

        def __init__(self):
            super().__init__()

        def encode(self, runcard: RunCard):
            runcard.write_instruction("  Process 93 93 -> 93 93 93{0}")
            runcard.write_instruction("  Order (*,0);")
            runcard.write_instruction("  CKKW sqr(20/E_CMS)")
            runcard.write_instruction("  Integration_Error 0.02;")
            runcard.write_instruction("  End process;")

    def __init__(self, name: str):
        super().__init__(name)
        self.__beams=[]
        self.__hepmcfile = ""
        self.__pdfset = ""
        self.__selectors = []
        self.__processes = []

    def set_beam(self, id: int, pdg: int, energy: int):
        self.__beams.append(self.Beam(id, pdg, energy))

    def set_hepmcfile(self, filename: str):
        self.__hepmcfile = filename

    def set_pdfset(self, pdfset: str):
        self.__pdfset = pdfset

    def add_process(self, process: Process):
        self.__processes.append(process)

    def add_selector(self, selector):
        self.__selectors.append(selector)

    def build(self):
        self.__build_run()
        self.__build_process()
        self.__build_selector()

    def __build_run(self):
        self.write_instruction("(run){")
        for beam in self.__beams:
            self.write_instruction(" {}".format(beam.encode()))
        hepmcfile = os.path.basename(self.__hepmcfile)
        if hepmcfile.find("."):
            hepmcfile = hepmcfile[:hepmcfile.find(".")-1]
        self.write_instruction("  EVENT_OUTPUT=HepMC_GenEvent[{HEPMCFILE}]]".format(HEPMCFILE=hepmcfile))
        if len(self.__pdfset):
            self.write_instruction("  PDF_LIBRARY={}".format(self.__pdfset))
        self.write_instruction("}(run)")

    def __build_process(self):
        if len(self.__processes):
            self.write_instruction("(process){")
            for proc in self.__processes:
                proc.encode(self)
            self.write_instruction("}(process)")

    def __build_selector(self):
        if len(self.__selectors):
            self.write_instruction("(selector){")
            for selector in self.__selectors:
                self.write_instruction("  {}".format(selector.encode()))
            self.write_instruction("}(selector)")

class SherpaEngine(SimulationEngine):

    def __init__(self, repository: str, runcard: str):
        super().__init__(repository, runcard)
        self._generator = "sherpa"
        self._inputfiles = [runcard]
        self.__runcard = SherpaRuncard(runcard)

    def generate_runcard(self, params: SimulationParam):
        self.__runcard.set_beam(1, 2212, params.get_energy_beam())
        self.__runcard.set_beam(2, 2212, params.get_energy_beam())
        self.__runcard.set_hepmcfile(params.get_hepmcfile())
        if len(params.pdfset):
            self.__runcard.set_pdfset(params.pdfset)
        if params.process == "dijet_lo":
            self.__runcard.add_process(SherpaRuncard.DijetProcess())
            ptmin = 0
            if params.ktmin > 0:
                ptmin = params.ktmin
            self.__runcard.add_selector(SherpaRuncard.JetSelector("antikt", 2, 0.7, ptmin, 0.))
        self.__runcard.build()

class SherpaRunner(SimulationRunner):
    
    def __init__(self, runcard: str, events: int, seed: int):
        super().__init__(runcard, events, seed)
        self._modules = ["Sherpa/latest"]

    def launch(self):
        runsteer = ProcessRunner()
        for module in self.modules:
            runsteer.load_module(module)
        runsteer.print_modules()
        runsteer.source_script("$CLUSTER_HOME/lhapdf_data_setenv")
        runsteer.write_instruction("Sherpa -f {RUNCARD} -e {EVENTS} -R {SEED} &> sherpa_run.log".format(RUNCARD=self._runcard, EVENTS=self._events, SEED=self._seed))
        runsteer.execute()
