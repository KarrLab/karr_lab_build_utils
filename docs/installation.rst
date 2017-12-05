Installation
============

Prerequisites
--------------------------

* libffi-dev
* libgit
* Python
* Pip


Create a PyPI account and save your PyPI credentials to ``~/.pypirc``
---------------------------------------------------------------------

Save your PyPI credentials to ``~/.pypirc``::

    [distutils]
    index-servers =
        pypi

    [pypi]
    repository: https://upload.pypi.org/legacy/
    username: <username>
    password: <password>


Install the latest revision from GitHub
---------------------------------------

Run the following command to install the latest version from GitHub::

    pip install git+git://github.com/KarrLab/karr_lab_build_utils.git#egg=karr_lab_build_utils
