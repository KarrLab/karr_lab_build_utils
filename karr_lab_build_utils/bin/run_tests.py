#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from karr_lab_build_utils.core import BuildHelper
import argparse


def main():
    """ Run unit tests located at `test_path`. 
    Optionally, generate a coverage report. 
    Optionally, save the results to `xml_file`.
    """

    parser = argparse.ArgumentParser(description='Run unit tests located at `test_path`')
    parser.add_argument('--test_path', default='tests', type=str,
                        help='path to tests that should be run')
    parser.add_argument('--with_xml_report', default=False, dest='with_xml_report', action='store_true',
                        help='True/False to save test results to XML file')
    parser.add_argument('--with_coverage', default=False, dest='with_coverage', action='store_true',
                        help='True/False to assess code coverage')
    args = parser.parse_args()

    buildHelper = BuildHelper()
    buildHelper.run_tests(test_path=args.test_path, with_xml_report=args.with_xml_report, with_coverage=args.with_coverage)

if __name__ == "__main__":
    main()
