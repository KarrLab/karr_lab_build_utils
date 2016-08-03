#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Archive documentation:
    * Upload documentation to lab server
    """

    parser = argparse.ArgumentParser(description='Archive documentation')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.archive_documentation()

if __name__ == "__main__":
    main()