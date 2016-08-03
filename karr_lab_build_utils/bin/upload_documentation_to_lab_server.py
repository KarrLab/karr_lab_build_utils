#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Upload documentation to lab server """

    parser = argparse.ArgumentParser(description='Upload documentation to lab server')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.upload_documentation_to_lab_server()

if __name__ == "__main__":
    main()
