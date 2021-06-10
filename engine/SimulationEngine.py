#! /usr/bin/env python3

class RunCard:

    def __init__(self, name: str):
        self.__writer = open(name, "w")

    def write_instruction(self, instruction: str):
        self.__writer.write("{}\n".format(instruction))
    
    def __del__(self):
        self.__writer.close()

class Process:

    def __init__(self):
        pass

    def encode(self, runcard: RunCard):
        pass


class SimulationParam:

    def __init__(self):
        self.__cms_energy: float = 0
        self.__beam_energy: float = 0
        self.__events: int = 0
        self.__process: str = ""
        self.__pdfset: str = ""
        self.__pthardbin: int = -1
        self.__ktmin: float = 0.
        self.__tune: str = ""
        self.__hepmcfile: str = ""

    def set_energy_cms(self, energy: float):
        self.__cms_energy = energy
        self.__beam_energy = energy / 2.

    def set_energy_beam(self, energy: float):
        self.__cms_energy = energy * 2
        self.__beam_energy = energy

    def set_events(self, events: int):
        self.__events = events

    def set_process(self, process: str):
        self.__process = process

    def set_pdfset(self, pdfset: str):
        self.__pdfset = pdfset

    def set_pthardbin(self, pthardbin: int):
        self.__pthardbin = pthardbin

    def set_ktmin(self, ktmin: float):
        self.__ktmin = ktmin

    def set_tune(self, tune: str):
        self.__tune = tune

    def set_hepmcfile(self, hepmcfile: str):
        self.__hepmcfile = hepmcfile

    def get_energy_cms(self) -> float:
        return self.__cms_energy

    def get_energy_beam(self) -> float:
        return self.__beam_energy

    def get_events(self) -> int:
        return self.__events

    def get_process(self) ->str:
        return self.__process

    def get_pdfset(self) -> str:
        return self.__pdfset

    def get_pthardbin(self) -> int:
        return self.__pthardbin

    def get_ktmin(self) -> float:
        return self.__ktmin

    def get_tune(self) -> str:
        return self.__tune

    def get_hepmcfile(self) -> str:
        return self.__hepmcfile

    cms_energy = property(fset=set_energy_cms, fget=get_energy_cms)
    beam_energy = property(fset=set_energy_beam, fget=get_energy_beam)
    events = property(fset=set_events, fget=get_events)
    process = property(fset=set_process, fget=get_process)
    pdfset = property(fset=set_pdfset, fget=get_pdfset)
    pthardbin = property(fset=set_pthardbin, fget=get_pthardbin)
    ktmin = property(fset=set_ktmin, fget=get_ktmin)
    tune = property(fset=set_tune, fget=get_tune)
    hepmcfile = property(fset=set_hepmcfile, fget=get_hepmcfile)


class PtHardHandler:

    def __init__(self):
        self.__pthardbins = {0: [0., 5.], 1: [5., 7.], 2: [7., 9.], 3: [9., 12.], 4: [12., 16.], 5: [16., 21.], 6: [21., 28.], 7: [28., 36.], 8: [36., 45.],
                             9: [45., 57], 10: [57., 70], 11: [70., 85.], 12: [85., 99.], 13: [99., 115.], 14: [115., 132.], 15: [132., 150.],
                             16: [150., 169], 17: [169., 190.], 18: [190, 212], 19: [212., 235.], 20: [235., 1000.]}

    def get_limits(self, pthardbin: int) -> list:
        if not pthardbin in self.__pthardbins.keys():
            return []
        return self.__pthardbins[pthardbin]

class SimulationEngine:

    def __init__(self, repo: str, runcard: str):
        self._repository = repo
        self._runcard = runcard
        self._generator = ""
        self._inputfiles = []

    def set_repo(self, repo: str):
        self._repository = repo

    def set_runcard(self, runcard: str):
        self._runcard = runcard
        
    def set_generator(self, generator: str):
        self._generator = generator

    def set_inputfiles(self, inputfiles: list):
        self._inputfiles = inputfiles

    def get_repo(self) -> str:
        return self._repository

    def get_runcard(self) -> str:
        return self._runcard

    def get_generator(self) -> str:
        return self._generator

    def get_inputfiles(self) -> list:
        return self._inputfiles

    def generate_runcard(self, params: SimulationParam):
        pass

    repo = property(fset=set_repo, fget=get_repo)
    runcard = property(fset=set_runcard, fget=get_runcard)
    generator = property(fset=set_generator, fget=get_generator)
    inputfiles = property(fset=set_inputfiles, fget=get_inputfiles)

class SimulationRunner:

    def __init__(self, runcard: str, events: int, seed: int):
        self._runcard = runcard
        self._events = events
        self._seed = seed
        self._modules = []

    def launch(self):
        pass

    def set_runcard(self, runcard: str):
        self._runcard = runcard

    def set_events(self, events: int):
        self._events = events

    def set_seed(self, seed):
        self._seed = seed

    def set_modules(self, modules: list):
        self._modules = modules

    def get_runcard(self) -> str:
        return self._runcard

    def get_events(self) -> int:
        return self._events

    def get_seed(self) -> int:
        return self._seed

    def get_modules(self) -> list:
        return self._modules

    runcard = property(fget=get_runcard, fset=set_runcard)
    events = property(fget=get_events, fset=set_events)
    seed = property(fget=get_seed, fset=set_seed)
    modules = property(fget=get_modules, fset=set_modules)