#! /usr/bin/env python3

import argparse
import os
import shutil
import sys

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="store_output.py", description="Moving results to persistent location")
    parser.add_argument("inputdir", metavar="INPUTDIR", type=str, help="Input location")
    parser.add_argument("outputdir", metavar="OUTPUTDIR", type=str, help="Output location")
    parser.add_argument("-r", "--rootfile", metavar="ROOTFILE", type=str, default="jetspectrum.root", help="Name of the rootfile")
    args = parser.parse_args()

    inputbase = args.inputdir
    if not os.path.exists(inputbase):
        print("Input location %s does not exist" %inputbase)
        sys.exit(1)
    outputbase = args.outputdir
    if not os.path.exists(outputbase):
        os.makedirs(outputbase, 0o755)
    rootfile = args.rootfile
    print("Copying files {} from {} to {} ...".format(rootfile, inputbase, outputbase))

    for dr in os.listdir(inputbase):
        if not os.path.isdir(os.path.join(inputbase, dr)):
            continue
        if not dr.isdigit() and not "bin" in dr:
            continue 
        inputfile = os.path.join(inputbase, dr, rootfile)
        if not os.path.exists(inputfile):
            continue
        outputdir = os.path.join(outputbase, dr)
        os.makedirs(outputdir, 0o755)
        outputfile = os.path.join(outputdir, rootfile)
        shutil.copyfile(inputfile, outputfile)