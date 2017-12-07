Installation
============

Pre-requisities
---------------

#. Run this command to install the required packages on Ubuntu::

    apt-get install \
        libffi-dev \
        libgit \
        python \
        python-pip

#. Optionally, create an SSH key for GitHub. This is needed to run tests using Docker and CircleCI.

    #. Create an SSH key and save it to ``~/.ssh/id_rsa``::

        ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
        eval $(ssh-agent -s)
        ssh-add ~/.ssh/id_rsa

    #. Copy the contents of ``~/.ssh/id_rsa.pub`` and use it to add your SSH key to GitHub following the instructions at `https://help.github.com/articles/adding-a-new-ssh-key-to-your-github-account <https://help.github.com/articles/adding-a-new-ssh-key-to-your-github-account>`_.

#. Optionally install Docker by following the `installation instructions <http://intro-to-wc-modeling.readthedocs.io/en/latest/installation.html>`_ in "An Introduction to Whole-Cell Modeling." This is needed to run tests using Docker and CircleCI.
#. Optionally, install the CircleCI command line tool by following the `installation instructions <http://intro-to-wc-modeling.readthedocs.io/en/latest/installation.html>`_ in "An Introduction to Whole-Cell Modeling." This is needed to run tests using CircleCI.
#. Optionally, create a PyPI account at `https://pypi.python.org <https://pypi.python.org>`_. This is needed to upload packages to PyPI.
#. Optionally, save your PyPI credentials to ``~/.pypirc``. This is needed to upload packages to PyPI.::

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
