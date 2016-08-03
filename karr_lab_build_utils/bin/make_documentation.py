#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Command line program to make HTML documentation """

    parser = argparse.ArgumentParser(description='Make HTML coverage report')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.make_documentation()

if __name__ == "__main__":
    main()