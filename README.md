[//]: # ( [![PyPI package](https://img.shields.io/pypi/v/karr_lab_build_utils.svg)](https://pypi.python.org/pypi/karr_lab_build_utils) )
[![Documentation](https://img.shields.io/badge/docs-latest-green.svg)](http://docs.karrlab.org/karr_lab_build_utils)
[![Test results](https://circleci.com/gh/KarrLab/karr_lab_build_utils.svg?style=shield)](https://circleci.com/gh/KarrLab/karr_lab_build_utils)
[![Test coverage](https://coveralls.io/repos/github/KarrLab/karr_lab_build_utils/badge.svg)](https://coveralls.io/github/KarrLab/karr_lab_build_utils)
[![Code analysis](https://api.codeclimate.com/v1/badges/423e5ef078681ee55979/maintainability)](https://codeclimate.com/github/KarrLab/karr_lab_build_utils)
[![License](https://img.shields.io/github/license/KarrLab/karr_lab_build_utils.svg)](LICENSE)
![Analytics](https://ga-beacon.appspot.com/UA-86759801-1/karr_lab_build_utils/README.md?pixel)

# Karr Lab build utilities

This package performs several aspects of the Karr Lab's build system:

* Create repositories with our default directory structure and files

  * Files for packaging Python code
  * Sphinx documentation configuration
  * CircleCI build configuration

* Tests code with Python 2 and 3 using pytest locally, using a Docker image, or using the CircleCI local executor
* Uploads test reports to our test history server
* Uploads coverage report to Coveralls
* Generates HTML API documentation using Sphinx

The build system is primarily designed for:

* Code that is implemented with Python 2/3
* Tests that can be run with pytest
* Code that is documented with Sphinx in Napolean/Google style
* Continuous integration with CircleCI

## Installation
Please see the [documentation](http://docs.karrlab.org/karr_lab_build_utils).

## Documentation
Please see the [documentation](http://docs.karrlab.org/karr_lab_build_utils).

## License
The build utilities are released under the [MIT license](LICENSE).

## Development team
This package was developed by [Jonathan Karr](http://www.karrlab.org) at the Icahn School of Medicine at Mount Sinai in New York, USA.

## Questions and comments
Please contact the [Jonathan Karr](http://www.karrlab.org) with any questions or comments.
