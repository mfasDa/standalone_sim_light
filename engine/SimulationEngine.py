#! /usr/bin/env python3

class SimulationEngine:

    def __init__(self, repo: str, runcard: str):
        self._repo = repo
        self._runcard = runcard
        self._generator = ""
        self._inputfiles = []

    def set_repo(self, repo: str):
        self._repo = repo

    def set_runcard(self, runcard: str):
        self._runcard = runcard
        
    def set_generator(self, generator: str):
        self._generator = generator

    def set_inputfiles(self, inputfiles: list):
        self._inputfiles = inputfiles

    def get_repo(self) -> str:
        return self._repo

    def get_runcard(self) -> str:
        return self._runcard

    def get_generator(self) -> str:
        return self._generator

    def get_inputfiles(self) -> list:
        return self._inputfiles

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