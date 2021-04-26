#! /usr/bin/env python3

import argparse
import logging
import sys

from engine.Analysis import AnalysisRunner
from engine.Herwig import HerwigRunner
from engine.SimulationEngine import SimulationRunner

def run_simulation(generator: str, runcard:str, events: int, seed: int) -> bool:
    engine: SimulationRunner = None
    if generator == "herwig":
        engine = HerwigRunner(runcard, events, seed)
    if not engine:
        logging.error("Engine for generator %s not initialized", generator)
        return False
    engine.launch()
    return True

def run_analysis(macro: str, hepmcfile: str):
    engine = AnalysisRunner(macro, hepmcfile)
    engine.launch()

if __name__ == "__main__":
    logging.basicConfig(format='[%(levelname)s]: %(message)s', level=logging.INFO)
    parser = argparse.ArgumentParser("runtask.py", description="Task runner")
    parser.add_argument("-c", "--runcard", metavar="RUNCARD", type=str, default="", help="Runcard")
    parser.add_argument("-g", "--generator", metavar="GENERATOR", type=str, default="", help="Generator")
    parser.add_argument("-e", "--events", metavar="EVENTS", type=int, default=100, help="Number of events")
    parser.add_argument("-s", "--seed", metavar="SEED", type=int, default=123456789, help="Random seed")
    parser.add_argument("-f", "--hepmcfile", metavar="HEPMCFILE", type=str, default="events.hepmc", help="File with HepMC events")
    parser.add_argument("-m", "--macro", metavar="MACRO", type=str, default="", help="Analysis macro")
    args = parser.parse_args()
    
    simulationStatus = True
    if len(args.generator):
        simulationStatus = run_simulation(args.generator, args.runcard, args.events, args.seed)
    
    if not simulationStatus:
        logging.error("Failed running simulation")
        sys.exit(1)

    if len(args.macro):
        run_analysis(args.macro, args.hepmcfile)
