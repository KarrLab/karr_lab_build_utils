Installation
============

Pre-requisites
---------------

#. Run these commands to install the required packages on Ubuntu::

    # install OS packages
    apt-get update
    apt-get install \
        cmake \
        enchant \
        gcc \
        git \
        graphviz \
        openssh-client \
        pandoc \
        python \
        python-pip \
        wget

    # install libgit2 (version in apt repository is old)
    pushd /tmp
    wget https://github.com/libgit2/libgit2/archive/v0.26.3.tar.gz -O /tmp/libgit2-0.26.3.tar.gz
    tar -xvvf /tmp/libgit2-0.26.3.tar.gz
    cd /tmp/libgit2-0.26.3
    cmake .
    make
    make install
    ldconfig
    cd /tmp
    export LIBGIT2=/usr/local
    echo "" >> ~/.bashrc
    echo "# libgit2" >> ~/.bashrc
    echo "export LIBGIT2=/usr/local" >> ~/.bashrc
    source ~/.bashrc
    rm /tmp/libgit2-0.26.3.tar.gz
    rm -r /tmp/libgit2-0.26.3
    popd

#. Run this command to upgrade pip and setuptools::

    pip install -U pip setuptools

#. Optionally, create ``~/.wc/karr_lab_build_utils.cfg`` to configure the package (see configuration options in ``karr_lab_build_utils/config/core.schema.cfg``). We recommend that Karr Lab members start by copying the shared configuration file from ``karr_lab_build_config/karr_lab_build_utils.cfg``.

#. Optionally, create an SSH key for GitHub. This is needed to run tests using Docker and CircleCI.

    #. Create an SSH key and save it to ``~/.ssh/id_rsa``::

        ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
        eval $(ssh-agent -s)
        ssh-add ~/.ssh/id_rsa

    #. Copy the contents of ``~/.ssh/id_rsa.pub`` and use it to add your SSH key to GitHub following the instructions at `https://help.github.com/articles/adding-a-new-ssh-key-to-your-github-account <https://help.github.com/articles/adding-a-new-ssh-key-to-your-github-account>`_.

    #. Configure git to use SSH by saving the following to ``~/.gitconfig``::

        [url "ssh://git@github.com/"]
            insteadOf = https://github.com/

#. Optionally install Docker by following the `installation instructions <https://docs.karrlab.org/intro_to_wc_modeling/latest/installation.html>`_ in "An Introduction to Whole-Cell Modeling." This is needed to run tests using Docker and CircleCI.
#. Optionally, install the CircleCI command line tool by following the `installation instructions <https://docs.karrlab.org/intro_to_wc_modeling/latest/installation.html>`_ in "An Introduction to Whole-Cell Modeling." This is needed to run tests using CircleCI.
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

    git clone https://github.com/KarrLab/karr_lab_build_utils.git
    cd karr_lab_build_utils
    pip install -e .[all]
