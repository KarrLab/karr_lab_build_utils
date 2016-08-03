#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Install requirements """

    parser = argparse.ArgumentParser(description='Install requirements')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.install_requirements()

if __name__ == "__main__":
    main()
