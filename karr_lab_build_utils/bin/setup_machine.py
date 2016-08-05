#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Command line program to setup machine (e.g. set python version) """

    parser = argparse.ArgumentParser(description='Setup machine')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.setup_machine()

if __name__ == "__main__":
    main()
