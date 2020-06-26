""" Karr Lab build utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-08-02
:Copyright: 2016-2018, Karr Lab
:License: MIT
"""
from ._version import __version__
from datetime import datetime
from jinja2 import Template
from pylint import epylint
from sphinx.cmdline import main as sphinx_main
from mock import patch
from xml.dom import minidom
import abduct
import attrdict
import click
import configparser
import coverage
import coveralls
import dateutil.parser
import email
import email.header
import email.message
import email.utils
import enum
import fnmatch
import ftputil
import git
import github
import glob
import graphviz
# import instrumental.api
import io
import json
import karr_lab_build_utils.config.core
import logging
import mock
import natsort
import networkx
import nose
import os
import pypandoc
import pip._internal.commands.show
import pip._internal.operations.freeze
import pip_check_reqs
import pip_check_reqs.find_extra_reqs
import pip_check_reqs.find_missing_reqs
# import pkg_utils
# pkg_utils is not imported globally so that we can use karr_lab_build_utils to properly calculate its coverage
# :todo: figure out how to fix this
import pkg_resources
import pytest
import _pytest
import quilt3
import re
import requests
import sphinx.ext.apidoc
import shutil
import smtplib
import stat
import subprocess
import sys
import tempfile
import time
import twine.commands.upload
import unittest
import warnings
import wc_utils
import whichcraft
import yaml


class CoverageType(enum.Enum):
    """ Types of coverage """
    statement = 0
    branch = 1
    multiple_condition = 2
    decision = 2


class Environment(enum.Enum):
    """ Environments to run tests """
    local = 0
    docker = 1
    circleci = 2


class BuildHelper(object):
    """ Utility class to help build projects:

    * Run tests
    * Archive reports to test history server, Coveralls, and Code Climate

    Attributes:
        test_runner (:obj:`str`): name of test runner {pytest, nose}

        repo_name (:obj:`str`): repository name
        repo_owner (:obj:`str`): name of the repository owner
        repo_branch (:obj:`str`): repository branch name
        repo_revision (:obj:`str`): sha of repository revision
        build_num (:obj:`int`): CircleCI build number

        proj_tests_dir (:obj:`str`): local directory with test code
        proj_tests_xml_dir (:obj:`str`): local directory to store latest XML test report
        proj_tests_xml_latest_filename (:obj:`str`): file name to store latest XML test report
        proj_docs_dir (:obj:`str`): local directory with Sphinx configuration
        proj_docs_static_dir (:obj:`str`): local directory of static documentation files
        proj_docs_source_dir (:obj:`str`): local directory of source documentation files created by sphinx-apidoc
        proj_docs_build_doctrees_dir (:obj:`str`): local directory where doc trees should be saved
        proj_docs_build_html_dir (:obj:`str`): local directory where generated HTML documentation should be saved
        proj_docs_build_spelling_dir (:obj:`str`): local directory where spell check results should be saved
        build_image (:obj:`str`): Docker image to use to run tests

        configs_repo_url (:obj:`str`): URL to Git repository with passwords
        configs_repo_username (:obj:`str`): username for Git repository with passwords
        configs_repo_password (:obj:`str`): password for Git repository with passwords
        configs_repo_path (:obj:`str`): path to clone Git repository with passwords

        github_api_token (:obj:`str`): GitHub API token
        circleci_api_token (:obj:`str`): CircleCI API token
        test_server_token (:obj:`str`): test history report server token
        email_hostname (:obj:`str`): hostname and port for email server
        email_username (:obj:`str`): username for email server
        email_password (:obj:`str`): password for :obj:`email_username`
        code_server_hostname (:obj:`str`): code server host name
        code_server_directory (:obj:`str`): code server directory
        code_server_username (:obj:`str`): code server username
        code_server_password (:obj:`str`): code server password
        docs_server_hostname (:obj:`str`): docs server host name
        docs_server_directory (:obj:`str`): docs server directory
        docs_server_username (:obj:`str`): docs server username
        docs_server_password (:obj:`str`): docs server password
        pypi_repository (:obj:`str`): PyPI repository name or URL
        pypi_config_filename (:obj:`str`): path to PyPI configuration file

        coveralls_token (:obj:`str`): Coveralls token
        code_climate_token (:obj:`str`): Code Climate token

        INITIAL_PACKAGE_VERSION (:obj:`str`): initial package version
        DEFAULT_BUILD_IMAGE_VERSION (:obj:`str`): default build image version

        DEFAULT_TEST_RUNNER (:obj:`str`): default test runner {pytest, nose}
        DEFAULT_PROJ_TESTS_DIR (:obj:`str`): default local directory with test code
        DEFAULT_PROJ_TESTS_XML_DIR (:obj:`str`): default local directory where the test reports generated should be saved
        DEFAULT_PROJ_TESTS_XML_LATEST_FILENAME (:obj:`str`): default file name to store latest XML test report
        DEFAULT_PROJ_DOCS_DIR (:obj:`str`): default local directory with Sphinx configuration
        DEFAULT_PROJ_DOCS_STATIC_DIR (:obj:`str`): default local directory of static documentation files
        DEFAULT_PROJ_DOCS_SOURCE_DIR (:obj:`str`): default local directory of source documentation files created by sphinx-apidoc
        DEFAULT_PROJ_DOCS_SPELLING_DIR (:obj:`str`): default local directory where spell check results should be saved
        DEFAULT_PROJ_DOCS_BUILD_HTML_DIR (:obj:`str`): default local directory where generated HTML documentation should be saved
        DEFAULT_BUILD_IMAGE (:obj:`str`): default Docker image to use to run tests

        GITHUB_API_ENDPOINT (:obj:`str`): GitHub API endpoint
        CIRCLE_API_ENDPOINT (:obj:`str`): CircleCI API endpoint

        COVERALLS_ENABLED (:obj:`bool`): if :obj:`True`, upload coverage reports to Coveralls
        CODE_CLIMATE_ENABLED (:obj:`bool`): if :obj:`True`, upload coverage reports to Code Climate
    """

    INITIAL_PACKAGE_VERSION = '0.0.1'
    DEFAULT_BUILD_IMAGE_VERSION = 'latest'

    DEFAULT_TEST_RUNNER = 'pytest'
    DEFAULT_PROJ_TESTS_DIR = 'tests'
    DEFAULT_PROJ_TESTS_XML_DIR = 'tests/reports'
    DEFAULT_PROJ_TESTS_XML_LATEST_FILENAME = 'latest'
    DEFAULT_PROJ_DOCS_DIR = 'docs'
    DEFAULT_PROJ_DOCS_STATIC_DIR = 'docs/_static'
    DEFAULT_PROJ_DOCS_SOURCE_DIR = 'docs/source'
    DEFAULT_PROJ_DOCS_BUILD_DOCTREES_DIR = 'docs/_build/doctrees'
    DEFAULT_PROJ_DOCS_BUILD_HTML_DIR = 'docs/_build/html'
    DEFAULT_PROJ_DOCS_BUILD_SPELLING_DIR = 'docs/_build/spelling'
    DEFAULT_BUILD_IMAGE = 'karrlab/wc_env_dependencies:latest'

    GITHUB_API_ENDPOINT = 'https://api.github.com'
    CIRCLE_API_ENDPOINT = 'https://circleci.com/api'

    COVERALLS_ENABLED = True
    CODE_CLIMATE_ENABLED = True

    PATCHED_PACKAGES = (
        'log',
        'pip-check-reqs',
    )

    def __init__(self):
        """ Construct build helper """

        # get settings from environment variables
        self.test_runner = os.getenv('TEST_RUNNER', self.DEFAULT_TEST_RUNNER)
        if self.test_runner not in ['pytest', 'nose']:
            raise BuildHelperError('Unsupported test runner {}'.format(self.test_runner))

        self.repo_type = 'github'
        self.repo_name = os.getenv('CIRCLE_PROJECT_REPONAME')
        self.repo_owner = os.getenv('CIRCLE_PROJECT_USERNAME') or 'KarrLab'
        self.repo_branch = os.getenv('CIRCLE_BRANCH')
        self.repo_revision = os.getenv('CIRCLE_SHA1')
        try:
            self.build_num = int(float(os.getenv('CIRCLE_BUILD_NUM')))
        except (TypeError, ValueError, ):
            self.build_num = 0

        self.proj_tests_dir = self.DEFAULT_PROJ_TESTS_DIR
        self.proj_tests_xml_dir = self.DEFAULT_PROJ_TESTS_XML_DIR
        self.proj_tests_xml_latest_filename = self.DEFAULT_PROJ_TESTS_XML_LATEST_FILENAME
        self.proj_docs_dir = self.DEFAULT_PROJ_DOCS_DIR
        self.proj_docs_static_dir = self.DEFAULT_PROJ_DOCS_STATIC_DIR
        self.proj_docs_source_dir = self.DEFAULT_PROJ_DOCS_SOURCE_DIR
        self.proj_docs_build_doctrees_dir = self.DEFAULT_PROJ_DOCS_BUILD_DOCTREES_DIR
        self.proj_docs_build_html_dir = self.DEFAULT_PROJ_DOCS_BUILD_HTML_DIR
        self.proj_docs_build_spelling_dir = self.DEFAULT_PROJ_DOCS_BUILD_SPELLING_DIR
        self.build_image = self.DEFAULT_BUILD_IMAGE

        config = karr_lab_build_utils.config.core.get_config()['karr_lab_build_utils']
        self.configs_repo_url = config['configs_repo_url']
        self.configs_repo_username = config['configs_repo_username']
        self.configs_repo_password = config['configs_repo_password']
        self.configs_repo_path = os.path.expanduser(config['configs_repo_path'])

        self.download_package_config_files()
        self.install_package_config_files()
        config = karr_lab_build_utils.config.core.get_config()['karr_lab_build_utils']
        self.configs_repo_url = config['configs_repo_url']
        self.configs_repo_username = config['configs_repo_username']
        self.configs_repo_password = config['configs_repo_password']
        self.configs_repo_path = os.path.expanduser(config['configs_repo_path'])
        self.github_api_token = config['github_api_token']
        self.circleci_api_token = config['circleci_api_token']
        self.test_server_token = config['test_server_token']
        self.email_hostname = config['email_hostname']
        self.email_username = config['email_username']
        self.email_password = config['email_password']
        self.code_server_hostname = config['code_server_hostname']
        self.code_server_directory = config['code_server_directory']
        self.code_server_username = config['code_server_username']
        self.code_server_password = config['code_server_password']
        self.docs_server_hostname = config['docs_server_hostname']
        self.docs_server_directory = config['docs_server_directory']
        self.docs_server_username = config['docs_server_username']
        self.docs_server_password = config['docs_server_password']
        self.pypi_repository = config['pypi_repository']
        self.pypi_config_filename = os.path.expanduser(config['pypi_config_filename'])

        self.coveralls_token = os.getenv('COVERALLS_REPO_TOKEN')
        self.code_climate_token = os.getenv('CODECLIMATE_REPO_TOKEN')

        # setup logging
        self.logger = logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        log_dir = os.path.expanduser('~/.wc/log/')
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        handler = logging.FileHandler(os.path.join(log_dir, 'karr_lab_build_utils.log'))
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s')
        handler.setFormatter(formatter)

    #####################
    # Create a package
    #####################
    def create_package(self, pypi_repository=None):
        """ Create a package

        * Create a local Git repository
        * Create a remote GitHub repository
        * Add the repository to Code Climate
        * Add the repository to Coveralls
        * Add the repository to CircleCI project (by following the GitHub repository)

            * Add environment variable for tokens for code.karrlab.org, Coveralls, Code Climate, and CircleCI
            * Add environment variable for password for karr.lab.daemon@gmail.com
            * Generate API token for status badge

        * If the repository is not private, add the repository to Read the Docs
        * Add the package to code.karrlab.org

            * Add JSON-formatted file to ``ssh://code.karrlab.org:/home/karrlab_code/code.karrlab.org/repo/{{ name }}.json``

        * Add badges for Code Climate, Coveralls, CircleCI, and Read the Docs to README.md
        * Add package name to ``downstream_dependencies`` key in ``.karr_lab_build_utils.yml``

        Args:
            pypi_repository (:obj:`str`, optional): name of a repository defined in the PyPI 
                configuration file or a repository URL
        """
        # print introductory message
        print('This program will guide you through creating a new package.')
        click.confirm('Continue?', default=True, abort=True)

        # gather basic information
        name = click.prompt('Enter the name of the new package', type=str)

        description = click.prompt('Enter a brief description of the new package', type=str)

        keywords = click.prompt('Enter a comma-separated list of keywords for the new package', type=str, default=' ')
        keywords = [kw.strip() for kw in keywords.strip().split(',') if kw.strip()]

        dependencies = click.prompt(
            'Enter a comma-separated list of Karr Lab packages that the new package depends on', type=str, default=' ')
        dependencies = [dep.strip() for dep in dependencies.strip().split(',') if dep.strip()]

        private = click.confirm('Should the repository be private?', default=True)

        dirname = click.prompt('Enter the directory for the new package', type=str, default=os.path.join('.', name))

        build_image_version = click.prompt('Enter the build image version to test the package',
                                           type=str, default=self.DEFAULT_BUILD_IMAGE_VERSION)

        # create local and GitHub Git repositories
        print('Creating {} remote Git repository "{}/{}" on GitHub and cloning this repository to "{}"'.format(
            'private' if private else 'public', self.repo_owner, name, dirname))
        self.create_repository(name, description=description, private=private, dirname=dirname)

        # Code Climate
        # :todo: programmatically add repo to Code Climate and generate tokens
        print('Visit "https://codeclimate.com/dashboard" and click on the "{}" organization.'.format(
            self.repo_owner if private else 'Open source'))
        click.confirm('Continue?', default=True, abort=True)

        print('Click the "Add a repository" button')
        click.confirm('Continue?', default=True, abort=True)

        print('Click the "Sync now" button')
        click.confirm('Continue?', default=True, abort=True)

        print('Click the "Add Repo" button for the "{}" repository'.format(name))
        click.confirm('Continue?', default=True, abort=True)

        print('Click the "Repo Settings" link'.format(name))
        click.confirm('Continue?', default=True, abort=True)

        print('Cick the "Test coverage" menu item')
        click.confirm('Continue?', default=True, abort=True)
        code_climate_repo_token = click.prompt('Enter the "test reporter id"')
        if private:
            code_climate_repo_id = click.prompt(
                'Enter the repository ID (ID in the URL https://codeclimate.com/repos/<id>/settings/test_reporter)')
        else:
            code_climate_repo_id = None

        print('Cick the "Badges" menu item')
        click.confirm('Continue?', default=True, abort=True)
        code_climate_repo_badge_token = click.prompt(
            'Enter the badge token (token in the URL https://api.codeclimate.com/v1/badges/<token>/maintainability)')

        # Coveralls
        # :todo: programmatically add repo to Coveralls and generate tokens
        print('Visit "https://coveralls.io"')
        click.confirm('Continue?', default=True, abort=True)

        print('Click the "ADD REPOS" button')
        click.confirm('Continue?', default=True, abort=True)

        print('Click the "SYNC REPOS" button')
        click.confirm('Continue?', default=True, abort=True)

        print('Search for the "{}/{}" repository and click its "OFF" button'.format(self.repo_owner, name))
        click.confirm('Continue?', default=True, abort=True)

        print('Click the details button for the "{}/{}" repository'.format(self.repo_owner, name))
        click.confirm('Continue?', default=True, abort=True)

        print('Click the "Settings" menu item')
        click.confirm('Continue?', default=True, abort=True)
        coveralls_repo_token = click.prompt('Enter the "REPO TOKEN"')

        if private:
            print('Click the "README BADGE" EMBED" button')
            click.confirm('Continue?', default=True, abort=True)
            coveralls_repo_badge_token = click.prompt(
                'Enter the badge token (token in the URL https://coveralls.io/repos/github/KarrLab/{}/badge.svg?t=<token>'.format(name))
        else:
            coveralls_repo_badge_token = None

        # CircleCI
        # :todo: programmatically create CircleCI build
        # :todo: programmatically create CircleCI token for status badges
        has_private_dependencies = False
        g = github.Github(self.github_api_token)
        org = g.get_organization('KarrLab')
        for dependency in dependencies:
            try:
                repo = org.get_repo(dependency)
                has_private_dependencies = has_private_dependencies or repo.private
            except github.UnknownObjectException:
                pass

        print('Visit "https://circleci.com/add-projects/gh/KarrLab"')
        click.confirm('Continue?', default=True, abort=True)

        print('Search for the "{}" repository and click its "Set Up Project" button'.format(name))
        click.confirm('Continue?', default=True, abort=True)

        print('Click the "Start building" button. '
              'Note, the first CircleCI build will fail because no code has yet been pushed.')
        click.confirm('Continue?', default=True, abort=True)

        if has_private_dependencies or private:
            print('Click the "Project settings" icon')
            click.confirm('Continue?', default=True, abort=True)

        if has_private_dependencies:
            print('Click the "Checkout SSH keys" button')
            click.confirm('Continue?', default=True, abort=True)

            print('Click the "Authorize with GitHub" button')
            click.confirm('Continue?', default=True, abort=True)

            print('Click the "Create and add ... user key" button')
            click.confirm('Continue?', default=True, abort=True)

        if private:
            print('Click the "API permissions" menu item')
            click.confirm('Continue?', default=True, abort=True)

            print('Click the "Create Token" button')
            click.confirm('Continue?', default=True, abort=True)

            print('Select "All", enter a label, and click the "Add Token" button')
            click.confirm('Continue?', default=True, abort=True)
            circleci_repo_token = click.prompt('Enter the new token')
        else:
            circleci_repo_token = None

        vars = {
            'COVERALLS_REPO_TOKEN': coveralls_repo_token,
            'CODECLIMATE_REPO_TOKEN': code_climate_repo_token,
            'CONFIG__DOT__karr_lab_build_utils__DOT__configs_repo_password': self.configs_repo_password,
        }
        self.set_circleci_environment_variables(vars, repo_name=name)

        # Read the Docs
        if not private:
            # :todo: programmatically add repo to Read the Docs
            print('Visit "https://readthedocs.org/dashboard/import/?"')
            click.confirm('Continue?', default=True, abort=True)

            print('Click the "refresh" icon')
            click.confirm('Continue?', default=True, abort=True)

            print('Find the "{}" repository and click its "+" button'.format(name))
            click.confirm('Continue?', default=True, abort=True)

            print('Click the "Next" button')
            click.confirm('Continue?', default=True, abort=True)

            print('Click the "Admin" menu item')
            click.confirm('Continue?', default=True, abort=True)

            print('Click the "Advanced settings" menu item')
            click.confirm('Continue?', default=True, abort=True)

            print('Set the "Requirements file" to "docs/requirements.rtd.txt"')
            click.confirm('Continue?', default=True, abort=True)

            print('Set the "Python configuration file" to "docs/conf.py"')
            click.confirm('Continue?', default=True, abort=True)

            print('Set the "Python interpreter" to "CPython 3.x"')
            click.confirm('Continue?', default=True, abort=True)

            print('Click the "Maintainers" menu item')
            click.confirm('Continue?', default=True, abort=True)

            print('Add "karr-lab-daemon" to the maintainers')
            click.confirm('Continue?', default=True, abort=True)

            print('Click the "Notifications" menu item')
            click.confirm('Continue?', default=True, abort=True)

            print('Add your email address and click submit')
            click.confirm('Continue?', default=True, abort=True)

            print('Add "jonrkarr@gmail.com" and click submit')
            click.confirm('Continue?', default=True, abort=True)

        # add package to code.karrlab.org
        with open(pkg_resources.resource_filename(
            'karr_lab_build_utils',
                os.path.join('templates', 'code_server', '_package_.json')), 'r') as file:
            template = Template(file.read())

        fid, local_filename = tempfile.mkstemp()
        os.close(fid)

        context = {
            'name': name,
            'type': 'Other',
            'description': description,
            'private': private,
            'circleci_repo_token': circleci_repo_token,
            'coveralls_repo_token': coveralls_repo_token,
            'code_climate_repo_badge_token': code_climate_repo_badge_token,
            'code_climate_repo_id': code_climate_repo_id,
        }

        template.stream(**context).dump(local_filename)

        with ftputil.FTPHost(self.code_server_hostname, self.code_server_username, self.code_server_password) as ftp:
            remote_filename = ftp.path.join(self.code_server_directory, '{}.json'.format(name))
            ftp.upload(local_filename, remote_filename)

        os.remove(local_filename)

        # setup repository
        self.setup_repository(name, description=description, keywords=keywords, dependencies=dependencies,
                              private=private, build_image_version=build_image_version, dirname=dirname,
                              circleci_repo_token=circleci_repo_token, coveralls_repo_badge_token=coveralls_repo_badge_token,
                              code_climate_repo_id=code_climate_repo_id, code_climate_repo_badge_token=code_climate_repo_badge_token)

        # append package to downstream dependencies of dependencies
        parent_dirname = os.path.dirname(dirname)
        for dependency in dependencies:
            config_filename = os.path.join(parent_dirname, dependency, '.karr_lab_build_utils.yml')

            if os.path.isfile(config_filename):
                with open(config_filename, 'r') as file:
                    config = yaml.load(file, Loader=yaml.FullLoader)

                if 'downstream_dependencies' not in config or config['downstream_dependencies'] is None:
                    config['downstream_dependencies'] = []
                config['downstream_dependencies'].append(name)

                with open(config_filename, 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)

            else:
                warnings.warn(('Unable to append package to downstream dependency {} because the '
                               'downstream dependency is not available').format(dependency),
                              UserWarning)

        # reserve package in PyPI
        self.upload_package_to_pypi(dirname=dirname, repository=pypi_repository, upload_source=True, upload_build=False)

        print('Visit "https://pypi.org/manage/project/{}/releases/{}"'.format(name, self.INITIAL_PACKAGE_VERSION))
        click.confirm('Continue?', default=True, abort=True)

        print('Use the "Options" button to delete the file')
        click.confirm('Continue?', default=True, abort=True)

        print('Enter the project name "{}"'.format(name.replace('_', '-')))
        click.confirm('Continue?', default=True, abort=True)

        print('Click the "Delete file" button')
        click.confirm('Continue?', default=True, abort=True)

        print('Click the "Collaborators" button')
        click.confirm('Continue?', default=True, abort=True)

        print('Use the webform to add "karrlab" as an owner')
        click.confirm('Continue?', default=True, abort=True)

    def create_repository(self, name, description='', private=True, dirname=None):
        """ Create a GitHub repository and clone the repository locally

        Args:
            name (:obj`str`): package name
            description (:obj:`str`, optional): package description
            private (:obj:`bool`, optional): if :obj:`False`, make the GitHub repository public and set
                up documentation generation with Read the Docs
            dirname (:obj:`str`, optional): directory name for repository
        """

        # process arguments
        if not re.match('^[a-z][a-z0-9_]*$', name):
            raise BuildHelperError("'{}' not valid: Repository names should start with a letter and only include lower "
                                   "case letters, numbers, and underscores".format(name))

        dirname = dirname or os.path.join('.', name)

        # create GitHub repository
        g = github.Github(self.github_api_token)
        org = g.get_organization('KarrLab')
        org.create_repo(name=name, description=description, private=private, auto_init=True)

        # initialize Git
        git.Repo.clone_from('https://github.com/KarrLab/{}.git'.format(name), dirname)

    def setup_repository(self, name, description='', keywords=None, dependencies=None, private=True, build_image_version=None,
                         dirname=None, circleci_repo_token=None, coveralls_repo_badge_token=None, code_climate_repo_id=None,
                         code_climate_repo_badge_token=None):
        """ Setup a local Git repository with the default directory structure

        Args:
            name (:obj`str`): package name
            description (:obj:`str`, optional): package description
            keywords (:obj:`list` of :obj:`str`, optional): list of keywords
            dependencies (:obj:`list` of :obj:`str`, optional): list of Karr Lab packages that the package depends on
            private (:obj:`bool`, optional): if :obj:`False`, make the GitHub repository public and set
                up documentation generation with Read the Docs
            build_image_version (:obj:`str`, optional): build image version
            dirname (:obj:`str`, optional): directory name
            circleci_repo_token (:obj:`str`, optional): CircleCI API token (e.g. for badges) for the repository
            coveralls_repo_badge_token (:obj:`str`, optional): Coveralls badge token for the repository
            code_climate_repo_id (:obj:`str`, optional): Code Climate ID for the repository
            code_climate_repo_badge_token (:obj:`str`, optional): Code Climate for the repository
        """

        if not re.match('^[a-z][a-z0-9_]*$', name):
            raise BuildHelperError("'{}' not valid: Repository names should start with a letter and only include lower "
                                   "case letters, numbers, and underscores".format(name))

        keywords = keywords or []

        dependencies = dependencies or []

        if not build_image_version:
            build_image_version = self.DEFAULT_BUILD_IMAGE_VERSION

        dirname = dirname or os.path.join('.', name)

        # create a directory for the repository
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        # create files
        filenames = (
            '.gitignore',
            'LICENSE',
            'MANIFEST.in',
            'README.md',
            'requirements.txt',
            'requirements.optional.txt',
            'setup.py',
            'setup.cfg',
            'tests/requirements.txt',
            'tests/test_core.py',
            'tests/test_main.py',
            '.circleci/config.yml',
            '.circleci/requirements.txt',
            '.karr_lab_build_utils.yml',
            '_package_/__init__.py',
            '_package_/_version.py',
            '_package_/core.py',
            '_package_/__main__.py',
        )

        now = datetime.now()
        context = {
            'name': name,
            'description': description,
            'keywords': keywords,
            'version': self.INITIAL_PACKAGE_VERSION,
            'year': now.year,
            'date': '{}-{}-{}'.format(now.year, now.month, now.day),
            'dependencies': dependencies,
            'build_image_version': build_image_version,
            'private': private,
            'circleci_repo_token': circleci_repo_token,
            'coveralls_repo_badge_token': coveralls_repo_badge_token,
            'code_climate_repo_id': code_climate_repo_id,
            'code_climate_repo_badge_token': code_climate_repo_badge_token,
        }

        for filename in filenames:
            if os.path.dirname(filename) and not os.path.isdir(os.path.join(dirname, os.path.dirname(filename))):
                os.makedirs(os.path.join(dirname, os.path.dirname(filename)))

            with open(pkg_resources.resource_filename(
                    'karr_lab_build_utils',
                    os.path.join('templates', filename)), 'r') as file:
                template = Template(file.read())
            template.stream(**context).dump(os.path.join(dirname, filename))

        os.rename(os.path.join(dirname, '_package_'), os.path.join(dirname, name))

        self.create_documentation_template(dirname)

    ###########################
    # Register repo on CircleCI
    ###########################
    def follow_circleci_build(self, repo_type=None, repo_owner=None, repo_name=None, has_private_dependencies=False):
        """ Follow CircleCI build for a repository

        Args:
            repo_type (:obj:`str`, optional): repository type
            repo_owner (:obj:`str`, optional): repository owner
            repo_name (:obj:`str`, optional): repository name
            has_private_dependencies (:obj:`bool`, optional): if :obj:`True`, add a GitHub SSH key for the Karr Lab machine user to the build

        Raises:
            :obj:`ValueError`: if a CircleCI build wasn't followed and didn't already exist
        """
        if repo_type is None:
            repo_type = self.repo_type

        if repo_owner is None:
            repo_owner = self.repo_owner

        if repo_name is None:
            repo_name = self.repo_name

        # follow repo
        result = self.run_circleci_api('/follow',
                                       method='post', repo_type=repo_type, repo_owner=repo_owner, repo_name=repo_name)
        if 'following' not in result or not result['following']:
            raise ValueError(
                'Unable to follow CircleCI build for repository {}/{}'.format(repo_owner, repo_name))

        # add checkout key
        if has_private_dependencies:
            # :todo: add a GitHub SSH key for the Karr Lab machine user to the build
            pass  # pragma: no cover

    def get_circleci_environment_variables(self, repo_type=None, repo_owner=None, repo_name=None):
        """ Get the CircleCI environment variables for a repository and their partial values

        Args:
            repo_type (:obj:`str`, optional): repository type
            repo_owner (:obj:`str`, optional): repository owner
            repo_name (:obj:`str`, optional): repository name

        Returns:
            :obj:`dict`: dictionary of environment variables and their partial values
        """
        if repo_type is None:
            repo_type = self.repo_type

        if repo_owner is None:
            repo_owner = self.repo_owner

        if repo_name is None:
            repo_name = self.repo_name

        vars = self.run_circleci_api('/envvar',
                                     repo_type=repo_type, repo_owner=repo_owner, repo_name=repo_name)
        return {var['name']: var['value'] for var in vars}

    def set_circleci_environment_variables(self, vars, repo_type=None, repo_owner=None, repo_name=None):
        """ Set the CircleCI environment variables for a repository

        Args:
            vars (:obj:`dict`): dictionary of environment variables to set
            repo_type (:obj:`str`, optional): repository type
            repo_owner (:obj:`str`, optional): repository owner
            repo_name (:obj:`str`, optional): repository name

        Returns:
            :obj:`dict`: dictionary of environment variables and their values
        """
        if repo_type is None:
            repo_type = self.repo_type

        if repo_owner is None:
            repo_owner = self.repo_owner

        if repo_name is None:
            repo_name = self.repo_name

        # get current environment variables
        old_vars = self.get_circleci_environment_variables(
            repo_type=repo_type, repo_owner=repo_owner, repo_name=repo_name)

        # update environment variables
        for name, value in vars.items():
            # delete environment variables which we want to overwrite
            if name in old_vars:
                self.delete_circleci_environment_variable(name,
                                                          repo_type=repo_type, repo_owner=repo_owner, repo_name=repo_name)

            # add environment variable
            self.run_circleci_api('/envvar',
                                  method='post', repo_type=repo_type, repo_owner=repo_owner, repo_name=repo_name,
                                  data={'name': name, 'value': value})

    def delete_circleci_environment_variable(self, var, repo_type=None, repo_owner=None, repo_name=None):
        """ Delete a CircleCI environment variable for a repository

        Args:
            var (:obj:`str`): name of variable to delete
            repo_type (:obj:`str`, optional): repository type
            repo_owner (:obj:`str`, optional): repository owner
            repo_name (:obj:`str`, optional): repository name
        """
        if repo_type is None:
            repo_type = self.repo_type

        if repo_owner is None:
            repo_owner = self.repo_owner

        if repo_name is None:
            repo_name = self.repo_name

        self.run_circleci_api('/envvar/{}'.format(var),
                              method='delete', repo_type=repo_type, repo_owner=repo_owner, repo_name=repo_name)

    def create_code_climate_github_webhook(self, repo_type=None, repo_owner=None, repo_name=None):
        """ Create GitHub webhook for Code Climate

        Args:
            repo_type (:obj:`str`, optional): repository type
            repo_owner (:obj:`str`, optional): repository owner
            repo_name (:obj:`str`, optional): repository name            

        Raises:
            :obj:`ValueError`: if webhook wasn't created and didn't already exist
        """
        if repo_type is None:
            repo_type = self.repo_type

        if repo_owner is None:
            repo_owner = self.repo_owner

        if repo_name is None:
            repo_name = self.repo_name

        assert(repo_type == 'github')

        g = github.Github(self.github_api_token)
        org = g.get_organization(repo_owner)
        repo = org.get_repo(repo_name)

        config = {
            'url': 'https://codeclimate.com/webhooks',
            'content_type': 'form',
        }
        events = ['push', 'pull_request']
        try:
            repo.create_hook('web', config, events=events, active=True)
        except github.GithubException as error:
            if error.data['errors'][0]['message'] != 'Hook already exists on this repository':
                raise error

    #########################
    # Installing dependencies
    #########################
    def install_requirements(self, upgrade=False):
        """ Install requirements

        Args:
            upgrade (:obj:`bool`, optional): if :obj:`True`, upgrade requirements
        """
        import pkg_utils
        # pkg_utils is imported locally so that we can use karr_lab_build_utils to properly calculate its coverage;
        # :todo: figure out how to fix this

        # upgrade pip, setuptools
        py_v = '{}.{}'.format(sys.version_info[0], sys.version_info[1])

        cmd = ['pip' + py_v, 'install', 'setuptools']
        if upgrade:
            cmd.append('-U')
        subprocess.check_call(cmd)

        cmd = ['pip' + py_v, 'install', 'pip']
        if upgrade:
            cmd.append('-U')
        subprocess.check_call(cmd)

        # requirements for package
        install_requirements, extra_requirements, _, _ = pkg_utils.get_dependencies(
            '.', include_uri=True, include_extras=True, include_specs=True, include_markers=True)
        self._install_requirements_helper(install_requirements + extra_requirements['all'], upgrade=upgrade)

        # upgrade CircleCI
        if upgrade and whichcraft.which('docker') and whichcraft.which('circleci'):
            subprocess.check_call(['circleci', 'update', 'install'])
            subprocess.check_call(['circleci', 'update', 'build-agent'])

    def _install_requirements_helper(self, reqs, upgrade=False):
        """ Install the packages in a requirements.txt file, including all optional dependencies

        Args:
            reqs (:obj:`list` of :obj:`str`): list of requirements
            upgrade (:obj:`bool`, optional): if :obj:`True`, upgrade requirements
        """

        # create a temporary file that has the optional markings remove
        file, filename = tempfile.mkstemp(suffix='.txt')
        os.close(file)

        with open(filename, 'w') as file:
            for req in reqs:
                file.write(req + '\n')

        py_v = '{}.{}'.format(sys.version_info[0], sys.version_info[1])
        cmd = ['pip' + py_v, 'install', '-r', filename]
        if upgrade:
            cmd.append('-U')
        subprocess.check_call(cmd)

        # cleanup temporary file
        os.remove(filename)

    def upgrade_karr_lab_packages(self):
        """ Upgrade the packages from the Karr Lab's GitHub organization

        Returns:
            :obj:`list` of :obj:`str`: upgraded requirements from the Karr Lab's GitHub organization
        """
        # get Karr Lab requirements
        lines = pip._internal.operations.freeze.freeze()
        reqs = []
        for line in lines:
            if not line.startswith('-e') and '==' in line:
                name = line.partition('==')[0]
                try:
                    info = list(pip._internal.commands.show.search_packages_info([name]))
                except:
                    info = None
                if info and info[0]['home-page'] and 'github.com/KarrLab/' in info[0]['home-page']:
                    name = info[0]['name']
                    url = info[0]['home-page']

                    if name in self.PATCHED_PACKAGES:
                        options = ''
                    else:
                        options = '[all]'

                    reqs.append('git+{}.git#egg={}{}'.format(url, name, options))

        # upgrade Karr Lab requirements
        if reqs:
            subprocess.check_call(['pip{}.{}'.format(sys.version_info[0], sys.version_info[1]),
                                   'install', '-U'] + reqs)

        return reqs

    ########################
    # Running tests
    ########################
    def run_tests(self, dirname='.', test_path=None,
                  n_workers=1, i_worker=0,
                  verbose=False, with_xunit=False,
                  with_coverage=False, coverage_dirname='tests/reports',
                  coverage_type=CoverageType.branch, environment=Environment.local, exit_on_failure=True,
                  ssh_key_filename='~/.ssh/id_rsa', remove_docker_container=True):
        """ Run unit tests located at `test_path`.

        Optionally, generate a coverage report.
        Optionally, save the results to a file

        To configure coverage, place a .coveragerc configuration file in the root directory
        of the repository - the same directory that holds .coverage. Documentation of coverage
        configuration is in https://coverage.readthedocs.io/en/coverage-4.2/config.html

        Args:
            dirname (:obj:`str`, optional): path to package that should be tested
            test_path (:obj:`str`, optional): path to tests that should be run
            n_workers (:obj:`int`, optional): number of workers to run tests
            i_worker (:obj:`int`, optional): index of worker within {0 .. :obj:`n_workers` - 1}
            verbose (:obj:`str`, optional): if :obj:`True`, display stdout from tests
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            coverage_type (:obj:`CoverageType`, optional): type of coverage to run when :obj:`with_coverage` is :obj:`True`
            environment (:obj:`str`, optional): environment to run tests (local, docker, or circleci-local-executor)
            exit_on_failure (:obj:`bool`, optional): whether or not to exit on test failure
            ssh_key_filename (:obj:`str`, optional): path to GitHub SSH key; needed for Docker environment
            remove_docker_container (:obj:`bool`, optional): if :obj:`True`, remove Docker container

        Raises:
            :obj:`BuildHelperError`: If the environment is not supported or the package directory not set
        """
        if environment == Environment.local:
            self._run_tests_local(dirname=dirname, test_path=test_path,
                                  n_workers=n_workers, i_worker=i_worker,
                                  verbose=verbose, with_xunit=with_xunit,
                                  with_coverage=with_coverage, coverage_dirname=coverage_dirname,
                                  coverage_type=coverage_type, exit_on_failure=exit_on_failure)
        elif environment == Environment.docker:
            self._run_tests_docker(dirname=dirname, test_path=test_path,
                                   n_workers=n_workers, i_worker=i_worker,
                                   verbose=verbose, with_xunit=with_xunit,
                                   with_coverage=with_coverage, coverage_dirname=coverage_dirname,
                                   coverage_type=coverage_type, ssh_key_filename=ssh_key_filename,
                                   remove_container=remove_docker_container)
        elif environment == Environment.circleci:
            self._run_tests_circleci(dirname=dirname, test_path=test_path,
                                     n_workers=n_workers, i_worker=i_worker,
                                     verbose=verbose, ssh_key_filename=ssh_key_filename)
        else:
            raise BuildHelperError('Unsupported environment: {}'.format(environment))

    def _run_tests_local(self, dirname='.', test_path=None,
                         n_workers=1, i_worker=0,
                         verbose=False, with_xunit=False,
                         with_coverage=False, coverage_dirname='tests/reports',
                         coverage_type=CoverageType.branch, exit_on_failure=True):
        """ Run unit tests located at `test_path` locally

        Optionally, generate a coverage report.
        Optionally, save the results to a file

        To configure coverage, place a .coveragerc configuration file in the root directory
        of the repository - the same directory that holds .coverage. Documentation of coverage
        configuration is in https://coverage.readthedocs.io/en/coverage-4.2/config.html

        Args:
            dirname (:obj:`str`, optional): path to package that should be tested
            test_path (:obj:`str`, optional): path to tests that should be run
            n_workers (:obj:`int`, optional): number of workers to run tests
            i_worker (:obj:`int`, optional): index of worker within {0 .. :obj:`n_workers` - 1}
            verbose (:obj:`str`, optional): if :obj:`True`, display stdout from tests
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            coverage_type (:obj:`CoverageType`, optional): type of coverage to run when :obj:`with_coverage` is :obj:`True`
            exit_on_failure (:obj:`bool`, optional): whether or not to exit on test failure

        Raises:
            :obj:`BuildHelperError`: If the package directory not set
        """
        if test_path is None:
            test_path = os.getenv('test_path', 'tests')

        py_v = self.get_python_version()
        abs_xml_latest_filename = os.path.join(
            self.proj_tests_xml_dir, '{}.{}-{}.{}.xml'.format(
                self.proj_tests_xml_latest_filename,
                os.getenv('CIRCLE_NODE_INDEX', 0),
                os.getenv('CIRCLE_NODE_TOTAL', 1),
                py_v))

        if with_coverage:
            if not os.path.isdir(coverage_dirname):
                os.makedirs(coverage_dirname)
            data_suffix = '{}-{}.{}'.format(i_worker, n_workers, py_v)
            if coverage_type == CoverageType.statement:
                cov = coverage.Coverage(data_file=os.path.join(coverage_dirname, '.coverage'),
                                        data_suffix=data_suffix, config_file=True)
                cov.start()
            elif coverage_type == CoverageType.branch:
                cov = coverage.Coverage(data_file=os.path.join(coverage_dirname, '.coverage'),
                                        data_suffix=data_suffix, config_file=True, branch=True)
                cov.start()
            # elif coverage_type == CoverageType.multiple_condition:
            #     # :todo: support instrumental once its dependency astkit is updated for Python 3
            #     parser = configparser.ConfigParser()
            #     parser.read(os.path.join(dirname, 'setup.cfg'))
            #     targets = parser.get('coverage:run', 'source').strip().split('\n')
            #     targets = [target.strip() for target in targets]
            #
            #     opts = attrdict.AttrDict({
            #         'file': os.path.join(coverage_dirname, '.coverage.' + py_v),
            #         'report': False,
            #         'label': False,
            #         'summary': False,
            #         'statements': False,
            #         'xml': False,
            #         'html': False,
            #         'all': False,
            #         'targets': targets,
            #         'ignores': [],
            #         'report_conditions_with_literals': False,
            #         'instrument_assertions': True,
            #         'use_metadata_cache': False,
            #         'instrument_comparisons': True,
            #     })
            #     cov = instrumental.api.Coverage(opts, os.getcwd())
            #     cov.start(opts.targets, opts.ignores)
            else:
                raise BuildHelperError('Unsupported coverage type: {}'.format(coverage_type))

        if with_xunit and not os.path.isdir(self.proj_tests_xml_dir):
            os.makedirs(self.proj_tests_xml_dir)

        if self.test_runner == 'pytest':
            test_path = test_path.replace(':', '::')
            test_path = test_path.replace('::::', '::')
            test_path = re.sub(r'::(.+?)(\.)', r'::\1::', test_path)

            if not os.path.isdir('logs'):
                os.mkdir('logs')

            argv = [
                '--log-file', 'logs/tests.log',
                '--log-level', 'DEBUG',
            ]
            if verbose:
                argv.append('--capture=no')
            if with_xunit:
                argv.append('--junitxml=' + abs_xml_latest_filename)

            # collect tests
            if n_workers > 1:
                test_cases = self._get_test_cases(test_path=test_path,
                                                  n_workers=n_workers, i_worker=i_worker,
                                                  with_xunit=with_xunit,
                                                  exit_on_failure=exit_on_failure)
            else:
                test_cases = [test_path]

            # run tests
            if test_cases:
                result = pytest.main(argv + test_cases)
            else:
                result = 0
        elif self.test_runner == 'nose':
            if n_workers > 1 or i_worker != 0:
                raise BuildHelperError('Only 1 worker supported with nose')

            test_path = test_path.replace('::', ':', 1)
            test_path = test_path.replace('::', '.', 1)

            argv = ['nosetests', test_path]
            if verbose:
                argv.append('--nocapture')
            if with_xunit:
                argv += ['--with-xunit', '--xunit-file', abs_xml_latest_filename]

            result = int(not nose.run(argv=argv))
        else:
            raise BuildHelperError('Unsupported test runner {}'.format(self.test_runner))

        if with_coverage:
            cov.stop()  # pragma: no cover # this line can't be covered
            cov.save()

        if exit_on_failure and result != 0:
            sys.exit(1)

    def _get_test_cases(self, test_path=None, n_workers=1, i_worker=0,
                        with_xunit=False, exit_on_failure=True):
        """ Get test cases for worker *i* of *n* workers

        Note: Because this is implemented using unittest, this cannot discover test functions that are not methods of classes inherited from
        `unittest.TestCase`. pytest can discover such tests. Up to commit
        `c5dba3651faacead7edd353fe67d1f25f4c3fc3a <https://github.com/KarrLab/karr_lab_build_utils/commit/c5dba3651faacead7edd353fe67d1f25f4c3fc3a>`_
        a custom pytest plugin was used to discover these tests. However, this plugin was broken by pytest 5. Specifically,
        the test collection caused segmentation faults with pyjnius/Java/ChemAxon. Potentially, this can be addressed
        by updating the plugin for pytest 5.

        Args:
            test_path (:obj:`str`, optional): path to tests that should be run
            n_workers (:obj:`int`, optional): number of workers to run tests
            i_worker (:obj:`int`, optional): index of worker within {0 .. :obj:`n_workers` - 1}
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            exit_on_failure (:obj:`bool`, optional): whether or not to exit on test failure

        Returns:
            :obj:`list` of :obj:`str`: sorted list of test cases
        """
        if test_path is None:
            test_path = os.getenv('test_path', 'tests')

        if i_worker >= n_workers:
            raise BuildHelperError('`i_worker` must be less than `n_workers`')

        if not os.path.isdir(test_path):
            if i_worker == 0:
                cases = [test_path]
            else:
                cases = []
        else:
            if test_path[-1] == os.path.sep:
                test_path = test_path[0:-1]

            suites = [(test_path, suite) for suite in unittest.TestLoader().discover(test_path)._tests]
            for root, dirs, files in os.walk(test_path):
                for dir in dirs:
                    suites.extend([(os.path.join(root, dir), suite)
                                   for suite in unittest.TestLoader().discover(os.path.join(root, dir))._tests])

            cases = set()
            while suites:
                parent_dir, suite = suites.pop()
                if isinstance(suite, unittest.suite.TestSuite):
                    suites.extend([(parent_dir, s) for s in suite._tests])
                else:
                    tmp = suite.id().split('.')
                    cases.add(parent_dir + os.path.sep + os.path.sep.join(tmp[0:-2]) + '.py')

            cases = sorted(cases)
            cases = cases[i_worker::n_workers]

        return cases

    def _run_tests_docker(self, dirname='.', test_path=None,
                          n_workers=1, i_worker=0,
                          verbose=False, with_xunit=False,
                          with_coverage=False, coverage_dirname='tests/reports',
                          coverage_type=CoverageType.branch, ssh_key_filename='~/.ssh/id_rsa', remove_container=True):
        """ Run unit tests located at `test_path` using a Docker image:

        #. Create a container based on the build image (e.g, karrlab/wc_env_dependencies:latest)
        #. Copy your GitHub SSH key to the container
        #. Remove Python cache directories (``__pycache__``) from the package
        #. Copy the package to the container at ``/root/projects``
        #. Install the Karr Lab build utilities into the container
        #. Install the requirements for the package in the container
        #. Run the tests inside the container using the same version of Python that called this method
        #. Delete the container

        Args:
            dirname (:obj:`str`, optional): path to package that should be tested
            test_path (:obj:`str`, optional): path to tests that should be run
            n_workers (:obj:`int`, optional): number of workers to run tests
            i_worker (:obj:`int`, optional): index of worker within {0 .. :obj:`n_workers` - 1}
            verbose (:obj:`str`, optional): if :obj:`True`, display stdout from tests
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            coverage_type (:obj:`CoverageType`, optional): type of coverage to run when :obj:`with_coverage` is :obj:`True`
            ssh_key_filename (:obj:`str`, optional): path to GitHub SSH key
            remove_container (:obj:`bool`, optional): if :obj:`True`, remove Docker container
        """
        container = self.create_docker_container(ssh_key_filename=ssh_key_filename)
        self.install_package_to_docker_container(container, dirname=dirname)
        self.run_tests_in_docker_container(container, test_path=test_path,
                                           n_workers=n_workers, i_worker=i_worker,
                                           verbose=verbose, with_xunit=with_xunit,
                                           with_coverage=with_coverage, coverage_dirname=coverage_dirname, coverage_type=coverage_type)
        if remove_container:
            self.remove_docker_container(container)

    def create_docker_container(self, ssh_key_filename='~/.ssh/id_rsa'):
        """ Create a docker container 

        Args:
            ssh_key_filename (:obj:`str`, optional): path to GitHub SSH key

        Returns:
            :obj:`str`: container id
        """
        ssh_key_filename = os.path.expanduser(ssh_key_filename)

        # pick container name
        now = datetime.now()
        container = now.strftime('build-%Y-%m-%d-%H-%M-%S')

        # get Python version
        py_v = '{}.{}'.format(sys.version_info[0], sys.version_info[1])

        # create container
        print('\n\n')
        print('=====================================')
        print('== Creating and starting container')
        print('=====================================')
        self._run_docker_command(['run',
                                  '--detach',
                                  '--tty',
                                  '--name', container,
                                  '--volume', '{}:/root/volume'.format(container),
                                  self.build_image])

        # copy GitHub SSH key to container
        print('\n\n')
        print('=====================================')
        print('== Copying SSH key to container')
        print('=====================================')
        self._run_docker_command(['exec', container, 'mkdir', '/root/.ssh/'])
        self._run_docker_command(['cp', ssh_key_filename, container + ':/root/.ssh/'])

        # install pkg_utils
        print('\n\n')
        print('=====================================')
        print('== Install pkg_utils')
        print('=====================================')
        build_utils_uri = 'git+https://github.com/KarrLab/pkg_utils.git'
        self._run_docker_command(['exec', container, 'bash', '-c',
                                  'pip{} install -U {}'.format(py_v, build_utils_uri)])

        # install Karr Lab build utils
        print('\n\n')
        print('=====================================')
        print('== Install karr_lab_build_utils')
        print('=====================================')

        self._run_docker_command(['exec', container, 'bash', '-c',
                                  'pip{} install -U {}'.format(
                                      py_v, 'git+https://github.com/KarrLab/sphinxcontrib-googleanalytics.git')])
        self._run_docker_command(['exec', container, 'bash', '-c',
                                  'pip{} install -U {}'.format(
                                      py_v, 'git+https://github.com/KarrLab/wc_utils.git#egg=wc_utils[all]')])
        build_utils_uri = 'git+https://github.com/KarrLab/karr_lab_build_utils.git'
        self._run_docker_command(['exec', container, 'bash', '-c',
                                  'pip{} install -U {}'.format(py_v, build_utils_uri)])

        return container

    def install_package_to_docker_container(self, container, dirname='.'):
        """ Copy and install package to Docker container

        Args:
            container (:obj:`str`): container id
            dirname (:obj:`str`, optional): path to package to copy and install
        """
        # get Python version
        py_v = '{}.{}'.format(sys.version_info[0], sys.version_info[1])

        # delete __pycache__ directories
        print('\n\n')
        print('=====================================')
        print('== Deleting __pycache__ directories')
        print('=====================================')
        for root, rel_dirnames, rel_filenames in os.walk(dirname):
            for rel_dirname in fnmatch.filter(rel_dirnames, '__pycache__'):
                shutil.rmtree(os.path.join(root, rel_dirname))

        # copy package to container
        print('\n\n')
        print('=====================================')
        print('== Copying package to container')
        print('=====================================')
        self._run_docker_command(['cp', os.path.abspath(dirname), container + ':/root/project'])

        # install package
        print('\n\n')
        print('=====================================')
        print('== Install package')
        print('=====================================')
        self._run_docker_command(['exec',
                                  '-w', '/root/project',
                                  container,
                                  'bash', '-c', 'pip{} install -e .'.format(py_v),
                                  ])

        # install dependencies
        print('\n\n')
        print('=====================================')
        print('== Install and upgrade dependencies')
        print('=====================================')
        self._run_docker_command(['exec',
                                  '--env', 'CONFIG__DOT__karr_lab_build_utils__DOT__configs_repo_password={}'.format(
                                      self.configs_repo_password),
                                  '-w', '/root/project',
                                  container,
                                  'bash', '-c', (
                                      'eval $(ssh-agent -s) && '
                                      'ssh-add /root/.ssh/id_rsa && '
                                      'karr_lab_build_utils{0} install-requirements && '
                                      'karr_lab_build_utils{0} upgrade-karr-lab-packages'.format(py_v)),
                                  ])

    def run_tests_in_docker_container(self, container, test_path=None,
                                      n_workers=1, i_worker=0,
                                      verbose=False, with_xunit=False, with_coverage=False,
                                      coverage_dirname='tests/reports', coverage_type=CoverageType.branch):
        """ Test a package in a docker container

        Args:
            container (:obj:`str`): container id
            test_path (:obj:`str`, optional): path to tests that should be run
            n_workers (:obj:`int`, optional): number of workers to run tests
            i_worker (:obj:`int`, optional): index of worker within {0 .. :obj:`n_workers` - 1}
            verbose (:obj:`str`, optional): if :obj:`True`, display stdout from tests
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            coverage_type (:obj:`CoverageType`, optional): type of coverage to run when :obj:`with_coverage` is :obj:`True`
        """
        if test_path is None:
            test_path = os.getenv('test_path', 'tests')

        py_v = '{}.{}'.format(sys.version_info[0], sys.version_info[1])

        print('\n\n')
        print('=====================================')
        print('== Running tests')
        print('=====================================')
        options = []

        options += [
            '--test-path', test_path,
            '--n-workers', str(n_workers),
            '--i-worker', str(i_worker),
        ]

        if with_coverage:
            options += [
                '--with-coverage',
                '--coverage-type', coverage_type.name,
                '--coverage-dirname', 'tests/reports',
            ]

        if with_xunit:
            options.append('--with-xunit')

        if verbose:
            options.append('--verbose')

        self._run_docker_command(['exec',
                                  '--env', 'CONFIG__DOT__karr_lab_build_utils__DOT__configs_repo_password={}'.format(
                                      self.configs_repo_password),
                                  '-w', '/root/project',
                                  container,
                                  'bash', '-c', (
                                      'eval $(ssh-agent -s) && '
                                      'ssh-add /root/.ssh/id_rsa && '
                                      'karr_lab_build_utils{} run-tests {}'.format(py_v, ' '.join(options))
                                  )],
                                 raise_error=False)

        temp_dirname = tempfile.mkdtemp()
        self._run_docker_command(['cp', container + ':/root/project/logs/', temp_dirname])
        wc_utils.util.files.copytree_to_existing_destination(os.path.join(temp_dirname, 'logs'), 'logs')
        shutil.rmtree(temp_dirname)

        if with_coverage:
            out = self._run_docker_command([
                'exec', container, 'bash', '-c',
                'ls -la ' + os.path.join('/root', 'project', 'tests', 'reports', '.coverage.*-*.{}.*'.format(py_v)),
            ])
            match = re.search(r'/root/project/tests/reports/(\.coverage\.\d+\-\d+\.\d+\.\d+\.\d+)', out)
            self._run_docker_command(['cp',
                                      container + ':' + match.group(0),
                                      os.path.join(coverage_dirname, match.group(1)),
                                      ])

        if with_xunit:
            out = self._run_docker_command(['exec', container, 'bash', '-c', 'ls -la ' +
                                            os.path.join('/root', 'project', self.DEFAULT_PROJ_TESTS_XML_DIR,
                                                         '{}.*-*.{}.*.xml'.format(self.DEFAULT_PROJ_TESTS_XML_LATEST_FILENAME, py_v))])
            match = re.search(r'/root/project/{}/({}\.\d+\-\d+\.\d+\.\d+\.\d+.xml)'.format(
                self.DEFAULT_PROJ_TESTS_XML_DIR,
                self.DEFAULT_PROJ_TESTS_XML_LATEST_FILENAME), out)
            self._run_docker_command(['cp',
                                      container + ':' + match.group(0),
                                      os.path.join(self.proj_tests_xml_dir, match.group(1)),
                                      ])

    def remove_docker_container(self, container):
        """ Stop and remove a docker container

        Args:
            container (:obj:`str`): container id
        """
        print('\n\n')
        print('=====================================')
        print('== Stopping and removing container')
        print('=====================================')
        self._run_docker_command(['stop', container])
        self._run_docker_command(['rm', container])
        self._run_docker_command(['volume', 'rm', container])

    def _run_docker_command(self, cmd, cwd=None, raise_error=True):
        """ Run a docker command

        Args:
            cmd (:obj:`list`): docker command to run
            cwd (:obj:`str`, optional): directory from which to run :obj:`cmd`
            raise_error (:obj:`bool`, optional): if true, raise errors

        Returns:
            :obj:`str`: standard output

        Raises:
            :obj:`BuildHelperError`: if the docker command fails
        """
        process = subprocess.Popen(['docker'] + cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(0.5)
        out, err = process.communicate()
        if process.returncode != 0 and raise_error:
            raise BuildHelperError(err.decode())

        return out.decode()

    def _run_tests_circleci(self, dirname='.', test_path=None,
                            n_workers=1, i_worker=0,
                            verbose=False, ssh_key_filename='~/.ssh/id_rsa'):
        """ Run unit tests located at `test_path` using the CircleCI local executor. This will run the same commands defined in
        ``.circle/config.yml`` as the cloud version of CircleCI.

        Args:
            dirname (:obj:`str`, optional): path to package that should be tested
            test_path (:obj:`str`, optional): path to tests that should be run
            n_workers (:obj:`int`, optional): number of workers to run tests
            i_worker (:obj:`int`, optional): index of worker within {0 .. :obj:`n_workers` - 1}
            verbose (:obj:`str`, optional): if :obj:`True`, display stdout from tests
            ssh_key_filename (:obj:`str`, optional): path to GitHub SSH key

        Raises:
            :obj:`BuildHelperError`: if the tests fail
        """
        if test_path is None:
            test_path = os.getenv('test_path', 'tests')

        ssh_key_filename = os.path.expanduser(ssh_key_filename)
        karr_lab_build_utils_dirname = os.path.expanduser('~/Documents/karr_lab_build_utils')

        # delete __pycache__ directories
        for root, rel_dirnames, rel_filenames in os.walk(dirname):
            for rel_dirname in fnmatch.filter(rel_dirnames, '__pycache__'):
                shutil.rmtree(os.path.join(root, rel_dirname))

        # update CircleCI to use build image with SSH key
        circleci_config_filename = os.path.join(dirname, '.circleci', 'config.yml')
        backup_circleci_config_filename = os.path.join(dirname, '.circleci', 'config.yml.save')

        with open(circleci_config_filename, 'r') as file:
            config = yaml.load(file, Loader=yaml.FullLoader)

        job = config['jobs']['build']
        if 'steps' in job:
            for i_step, step in enumerate(job['steps']):
                if 'run' in step and 'command' in step['run']:
                    step['run']['command'] = 'eval $(ssh-agent -s) && ssh-add /root/.ssh/id_rsa\n' \
                        + step['run']['command']
                job['steps'][i_step] = step

        image_name = job['docker'][0]['image']
        if image_name.endswith('.with_ssh_key'):
            image_with_ssh_key_name = image_name
            image_name = image_name[:-13]
        else:
            image_with_ssh_key_name = image_name + '.with_ssh_key'

        shutil.copyfile(circleci_config_filename, backup_circleci_config_filename)
        job['docker'][0]['image'] = image_with_ssh_key_name
        with open(circleci_config_filename, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)

        # Build docker image with SSH key
        circleci_context_dirname = os.path.join(karr_lab_build_utils_dirname, 'circleci_docker_context')
        if not os.path.isdir(circleci_context_dirname):
            os.makedirs(circleci_context_dirname)
        shutil.copy(ssh_key_filename, os.path.join(circleci_context_dirname, 'GITHUB_SSH_KEY'))

        dockerfile_filename = os.path.join(circleci_context_dirname, 'Dockerfile_Circleci')
        with open(dockerfile_filename, 'w') as file:
            file.write('FROM {}\n'.format(image_name))
            file.write('COPY GITHUB_SSH_KEY /root/.ssh/id_rsa\n')
            file.write('RUN eval $(ssh-agent -s) && ssh-add /root/.ssh/id_rsa\n')
            file.write('CMD bash\n')

        self._run_docker_command(['build',
                                  '--tag', image_with_ssh_key_name,
                                  '-f', 'Dockerfile_Circleci',
                                  '.'],
                                 cwd=circleci_context_dirname)

        # test package
        process = subprocess.Popen(['circleci', 'local', 'execute',
                                    '--env', 'test_path={}'.format(test_path),
                                    '--env', 'CIRCLE_NODE_TOTAL={}'.format(n_workers),
                                    '--env', 'CIRCLE_NODE_INDEX={}'.format(i_worker),
                                    '--env', 'verbose={:d}'.format(verbose),
                                    '--env', 'dry_run=1',
                                    '--env', 'CONFIG__DOT__karr_lab_build_utils__DOT__configs_repo_password={}'.format(
                                        self.configs_repo_password),
                                    ], cwd=dirname, stderr=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(0.5)
        err = process.communicate()[1].decode()

        # revert CircleCI configuration file
        os.remove(circleci_config_filename)
        shutil.move(backup_circleci_config_filename, circleci_config_filename)

        # delete docker image
        self._run_docker_command(['rmi', image_with_ssh_key_name], raise_error=False)

        # cleanup circleci context
        shutil.rmtree(circleci_context_dirname)

        # raise error if tests didn't pass
        if process.returncode != 0 or 'Task failed' in err:
            raise BuildHelperError(err)

    def get_test_results(self):
        """ Load test results from a set of XML files

        Results:
            :obj:`TestResults`: test results
        """
        test_results = TestResults()

        filename_pattern = os.path.join(self.proj_tests_xml_dir,
                                        '{0}.*-*.*.xml'.format(self.proj_tests_xml_latest_filename))
        for filename in glob.glob(filename_pattern):
            match = re.match(r'^{}\.(.*?)\-(.*?)\.(.*?)\.xml$'.format(self.proj_tests_xml_latest_filename), os.path.basename(filename))
            python_version = match.group(3)

            doc = minidom.parse(filename)
            suite = doc.getElementsByTagName('testsuite')[0]
            for case in suite.getElementsByTagName('testcase'):
                case_result = TestCaseResult()
                case_result.classname = case.getAttribute('classname')
                case_result.name = case.getAttribute('name')
                case_result.python_version = python_version
                case_result.time = float(case.getAttribute('time'))

                if case.hasAttribute('file'):
                    case_result.file = case.getAttribute('file')

                if case.hasAttribute('line'):
                    case_result.line = int(float(case.getAttribute('line')))

                stdout = case.getElementsByTagName('system-out')
                if stdout:
                    case_result.stdout = ''.join([child.nodeValue for child in stdout[0].childNodes])

                stderr = case.getElementsByTagName('system-err')
                if stderr:
                    case_result.stderr = ''.join([child.nodeValue for child in stderr[0].childNodes])

                skip = case.getElementsByTagName('skipped')
                error = case.getElementsByTagName('error')
                failure = case.getElementsByTagName('failure')

                if skip:
                    case_result.type = TestCaseResultType.skipped
                elif error:
                    case_result.type = TestCaseResultType.error
                elif failure:
                    case_result.type = TestCaseResultType.failure
                else:
                    case_result.type = TestCaseResultType.passed

                not_pass = skip or error or failure
                if not_pass:
                    case_result.subtype = not_pass[0].getAttribute('type')
                    case_result.message = not_pass[0].getAttribute('message')
                    case_result.details = ''.join([child.nodeValue for child in not_pass[0].childNodes])

                test_results.cases.append(case_result)

        return test_results

    def get_test_results_status(self, test_results, installation_error, tests_error, other_error, dry_run=False):
        """ Get the status of a set of results

        * Old err
        * New error
        * Fixed error
        * New downstream error

        Args:
            test_results (:obj:`TestResults`): test results
            installation_error (:obj:`bool`): :obj:`True` if there were other errors during the installation
            tests_error (:obj:`bool`): obj:`False` if the tests passes
            other_error (:obj:`bool`): :obj:`True` if there were other errors during the build such as in generating and/or
                archiving the reports
            dry_run (:obj:`bool`, optional): if true, don't upload to the Coveralls and Code Climate servers

        Returns:
            :obj:`dict`: status of a set of results
        """
        if dry_run:
            return {
                'is_fixed': False,
                'is_old_error': False,
                'is_new_error': False,
                'is_other_error': False,
                'is_new_downstream_error': False,
            }

        # determine if there is an error
        if (installation_error or tests_error or other_error) and test_results.get_num_tests() == 0:
            is_other_error = True
            is_new_error = False
            is_old_error = False
            is_fixed = False
        else:
            is_other_error = other_error
            passed = test_results.get_num_errors() == 0 and test_results.get_num_failures() == 0

            # determine if error is new
            if self.build_num <= 1:
                if passed:
                    is_old_error = False
                    is_new_error = False
                    is_fixed = True
                else:
                    is_old_error = False
                    is_new_error = True
                    is_fixed = False
            else:
                prev_result = self.run_circleci_api('/' + str(self.build_num - 1))
                if passed:
                    is_old_error = False
                    is_new_error = False
                    is_fixed = prev_result['status'] not in ['success', 'fixed']
                else:
                    is_old_error = prev_result['status'] not in ['success', 'fixed']
                    is_new_error = prev_result['status'] in ['success', 'fixed']
                    is_fixed = False

        # determine if build was triggered by an upstream package
        upstream_repo_name = os.getenv('UPSTREAM_REPONAME', '')
        upstream_build_num = int(os.getenv('UPSTREAM_BUILD_NUM', '0'))

        if upstream_repo_name and is_new_error and self.build_num > 1 and not is_other_error:
            is_new_downstream_error = True
        else:
            is_new_downstream_error = False

        return {
            'is_fixed': is_fixed,
            'is_old_error': is_old_error,
            'is_new_error': is_new_error,
            'is_other_error': is_other_error,
            'is_new_downstream_error': is_new_downstream_error,
        }

    def do_post_test_tasks(self, installation_error, tests_error, dry_run=False):
        """ Do all post-test tasks for CircleCI

        * Make test and coverage reports
        * Compile documentation
        * Archive test and coverage reports to the Karr Lab test history server, Coveralls, and Code Climate
        * Trigger tests of downstream dependencies
        * Notify authors of new failures in downstream packages

        Args:
            installation_error (:obj:`bool`): :obj:`True` if there were other errors during the installation
            tests_error (:obj:`bool`): obj:`False` if the tests passes
            dry_run (:obj:`bool`, optional): if true, don't upload to the Coveralls and Code Climate servers

        Returns:
            :obj:`list` of :obj:`str`: names of triggered packages
            :obj:`dict` of :obj:`str`, :obj:`str`: dictionary which maps names of untriggered packages to the reasons 
                why they weren't triggered
            :obj:`dict`: status of a set of results
            :obj:`Exception`: exception from `make_and_archive_reports`
        """
        try:
            static_analyses = self.make_and_archive_reports(dry_run=dry_run)
            other_error = False
            other_exception = None
        except Exception as exception:
            static_analyses = {'missing_requirements': [], 'unused_requirements': []}
            other_error = True
            other_exception = exception

        triggered_packages, not_triggered_packages = self.trigger_tests_of_downstream_dependencies(dry_run=dry_run)
        status = self.send_email_notifications(installation_error, tests_error, other_error, static_analyses, dry_run=dry_run)
        return (triggered_packages, not_triggered_packages, status, other_exception)

    def send_email_notifications(self, installation_error, tests_error, other_error, static_analyses, dry_run=False):
        """ Send email notifications of failures, fixes, and downstream failures

        Args:
            installation_error (:obj:`bool`): :obj:`True` if there were other errors during the installation
            tests_error (:obj:`bool`): obj:`False` if the tests passes
            other_error (:obj:`bool`): :obj:`True` if there were other errors during the build such as in generating and/or
                archiving the reports
            static_analyses (:obj:`dict`): analyses of missing and unused requirements
            dry_run (:obj:`bool`, optional): if true, don't upload to the Coveralls and Code Climate servers

        Returns:
            :obj:`dict`: status of a set of results
        """
        test_results = self.get_test_results()
        status = self.get_test_results_status(test_results, installation_error, tests_error, other_error, dry_run=dry_run)

        # stop if this is a dry run
        if dry_run:
            return status

        # build context for email
        result = self.run_circleci_api('/' + str(self.build_num))

        if result['all_commit_details']:
            context = {
                'repo_name': self.repo_name,
                'commit': result['all_commit_details'][0]['commit'],
                'committer_name': result['all_commit_details'][0]['committer_name'],
                'committer_email': result['all_commit_details'][0]['committer_email'],
                'commit_subject': result['all_commit_details'][0]['subject'],
                'commit_url': result['all_commit_details'][0]['commit_url'],
                'build_num': self.build_num,
                'build_url': result['build_url'],
                'test_results': test_results,
                'static_analyses': static_analyses,
            }
        else:
            context = {
                'repo_name': self.repo_name,
                'commit': '',
                'committer_name': '',
                'committer_email': '',
                'commit_subject': '',
                'commit_url': '',
                'build_num': self.build_num,
                'build_url': result['build_url'],
                'test_results': test_results,
                'static_analyses': static_analyses,
            }

        if status['is_new_downstream_error']:
            upstream_repo_name = os.getenv('UPSTREAM_REPONAME', '')
            upstream_build_num = int(os.getenv('UPSTREAM_BUILD_NUM', '0'))
            result = self.run_circleci_api('/' + str(upstream_build_num), repo_name=upstream_repo_name)
            if result['all_commit_details']:
                context['upstream'] = {
                    'repo_name': upstream_repo_name,
                    'commit': result['all_commit_details'][0]['commit'],
                    'committer_name': result['all_commit_details'][0]['committer_name'],
                    'committer_email': result['all_commit_details'][0]['committer_email'],
                    'commit_subject': result['all_commit_details'][0]['subject'],
                    'commit_url': result['all_commit_details'][0]['commit_url'],
                    'build_num': upstream_build_num,
                    'build_url': result['build_url'],
                }
            else:
                context['upstream'] = {
                    'repo_name': upstream_repo_name,
                    'commit': '',
                    'committer_name': '',
                    'committer_email': '',
                    'commit_subject': '',
                    'commit_url': '',
                    'build_num': upstream_build_num,
                    'build_url': result['build_url'],
                }

        config = self.get_build_config()
        recipients = config.get('email_notifications', [])

        # send notifications
        if status['is_fixed']:
            subject = '[Builds] [{0}] {0} is fixed!'.format(context['repo_name'])
            self._send_notification_email(recipients, subject, 'fixed.html', context)
        elif status['is_old_error']:
            subject = '[Builds] [{0}] {0} is still broken!'.format(context['repo_name'])
            self._send_notification_email(recipients, subject, 'old_error.html', context)
        elif status['is_new_error']:
            subject = '[Builds] [{0}] {0} has been broken!'.format(context['repo_name'])
            self._send_notification_email(recipients, subject, 'new_error.html', context)
        elif status['is_other_error']:
            subject = '[Builds] [{0}] {0} is broken!'.format(context['repo_name'])
            self._send_notification_email(recipients, subject, 'other_error.html', context)

        if status['is_new_downstream_error']:
            recipients.append('wholecell-developers@googlegroups.com')
            subject = '[Builds] [{1}] commit {0} to {1} may have broken {2}'.format(
                context['upstream']['commit'], context['upstream']['repo_name'], context['repo_name'])
            self._send_notification_email(recipients, subject, 'new_downstream_error.html', context)

        return status

    def _send_notification_email(self, recipients, subject, template_filename, context, dry_run=False):
        """ Send an email notification of test results

        Args:
            recipients (:obj:`list` of :obj:`str`): recipient email addresses
            subject (:obj:`str`): subject
            template_filename (:obj:`str`): path to template
            context (:obj:`dict`): context for template
            dry_run (:obj:`bool`, optional): if true, don't upload to the Coveralls and Code Climate servers
        """
        if not recipients:
            return

        full_template_filename = pkg_resources.resource_filename(
            'karr_lab_build_utils', os.path.join('templates', 'email_notifications', template_filename))
        with open(full_template_filename, 'r') as file:
            template = Template(file.read())
            body = template.render(**context)

        msg = email.message.Message()

        email_domain, _, _ = self.email_hostname.partition(':')
        email_domain = '.'.join(email_domain.split('.')[-2:])
        from_addr = '{}@{}'.format(self.email_username, email_domain)
        msg['From'] = email.utils.formataddr((str(email.header.Header('Karr Lab Daemon', 'utf-8')), from_addr))

        tos = []
        for recipient in recipients:
            tos.append(email.utils.formataddr((None, recipient)))
        msg['To'] = ', '.join(tos)

        msg['Subject'] = subject

        msg.add_header('Content-Type', 'text/html')
        msg.set_payload(body, 'utf8')

        if not dry_run:
            smtp = smtplib.SMTP(self.email_hostname)
            smtp.ehlo()
            smtp.starttls()
            smtp.login(self.email_username, self.email_password)
            try:
                smtp.sendmail(from_addr, recipients, msg.as_string())
            except Exception as error:
                warnings.warn('Unable to send notification: {}'.format(str(error)), UserWarning)
            smtp.quit()

    def make_and_archive_reports(self, coverage_dirname='tests/reports', dry_run=False):
        """ Make and archive reports:

        * Upload test report to history server
        * Upload coverage report to Coveralls and Code Climate

        Args:
            coverage_dirname (:obj:`str`, optional): directory to merge coverage files
            dry_run (:obj:`bool`, optional): if true, don't upload to the Coveralls and Code Climate servers

        Returns:
            :obj:`dict`: analyses of missing and unused requirements
        """
        config = self.get_build_config()
        errors = []

        """ test reports """
        # Upload test report to history server
        self.archive_test_report()

        """ coverage """
        # Merge coverage reports
        # Generate HTML report
        # Upload coverage report to Coveralls and Code Climate
        self.combine_coverage_reports(coverage_dirname=coverage_dirname)
        self.archive_coverage_report(coverage_dirname=coverage_dirname, dry_run=dry_run)

        """ static analysis """
        self.analyze_package(self.repo_name)

        find_missing_requirements = config.get('static_analyses', {}).get('find_missing_requirements', True)
        find_unused_requirements = config.get('static_analyses', {}).get('find_unused_requirements', True)
        ignore_files = config.get('static_analyses', {}).get('ignore_files', [])

        if find_missing_requirements:
            missing_reqs = self.find_missing_requirements(self.repo_name, ignore_files=ignore_files)
            if missing_reqs:
                errors.append('The following requirements are missing:\n  {}'.format(
                    '\n  '.join(missing_req[0] for missing_req in missing_reqs)))
        else:
            missing_reqs = []

        if find_unused_requirements:
            unused_reqs = self.find_unused_requirements(self.repo_name, ignore_files=ignore_files)
            if unused_reqs:
                msg = 'The following requirements appear to be unused:\n  {}'.format('\n  '.join(unused_reqs))
                warnings.warn(msg, UserWarning)
        else:
            unused_reqs = []

        """ documentation """
        self.make_documentation()
        self.upload_documentation_to_docs_server()

        """ Log environment """
        self.log_environment()

        """ Throw error """
        if errors:
            raise BuildHelperError('\n\n'.join(errors))

        return {
            'missing_requirements': missing_reqs,
            'unused_requirements': unused_reqs,
        }

    ########################
    # Test reports
    ########################

    def archive_test_report(self):
        """ Upload test report to history server

        Raises:
            :obj:`BuildHelperError`: if there is an error uploading the report to the test history server
        """

        if not self.test_server_token or \
                self.repo_name is None or \
                self.repo_owner is None or \
                self.repo_branch is None or \
                self.repo_revision is None:
            return

        abs_xml_latest_filename_pattern = os.path.join(
            self.proj_tests_xml_dir, '{0}.*-*.*.xml'.format(self.proj_tests_xml_latest_filename))
        for abs_xml_latest_filename in glob.glob(abs_xml_latest_filename_pattern):
            match = re.match(r'^.*?\.(\d+)\-(\d+)\.(\d+\.\d+\.\d+)\.xml$', abs_xml_latest_filename)
            pyv = match.group(3)
            r = requests.post('https://tests.karrlab.org/rest/submit_report',
                              data={
                                  'token': self.test_server_token,
                                  'repo_name': self.repo_name,
                                  'repo_owner': self.repo_owner,
                                  'repo_branch': self.repo_branch,
                                  'repo_revision': self.repo_revision,
                                  'build_num': self.build_num,
                                  'report_name': pyv,
                              },
                              files={
                                  'report': open(abs_xml_latest_filename, 'rb'),
                              })
            r.raise_for_status()
            r_json = r.json()
            if 'success' not in r_json or not r_json['success']:
                raise BuildHelperError('Error uploading report to test history server: {}'.format(r_json['message']))

    ########################
    # Coverage reports
    ########################
    def combine_coverage_reports(self, coverage_dirname='tests/reports'):
        """
        Args:
            coverage_dirname (:obj:`str`, optional): directory to merge coverage files
        """
        data_paths = []
        for name in glob.glob(os.path.join(coverage_dirname, '.coverage.*')):
            data_path = tempfile.mktemp()
            shutil.copyfile(name, data_path)
            data_paths.append(data_path)

        # stop if there are no files to combine
        if not data_paths:
            warnings.warn('No coverage files exist to combine', UserWarning)
            return

        coverage_doc = coverage.Coverage(data_file=os.path.join(coverage_dirname, '.coverage'))
        coverage_doc.combine(data_paths=data_paths)
        coverage_doc.save()

    def archive_coverage_report(self, coverage_dirname='tests/reports', dry_run=False):
        """ Archive coverage report:

        * Upload report to Coveralls
        * Upload report to Code Climate

        Args:
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            dry_run (:obj:`bool`, optional): if true, don't upload to the Coveralls and Code Climate servers
        """

        # upload to Coveralls
        if self.COVERALLS_ENABLED:
            self.upload_coverage_report_to_coveralls(coverage_dirname=coverage_dirname, dry_run=dry_run)

        # upload to Code Climate
        if self.CODE_CLIMATE_ENABLED:
            self.upload_coverage_report_to_code_climate(coverage_dirname=coverage_dirname, dry_run=dry_run)

    def upload_coverage_report_to_coveralls(self, coverage_dirname='tests/reports', dry_run=False):
        """ Upload coverage report to Coveralls

        Args:
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            dry_run (:obj:`bool`, optional): if true, don't upload to the Coveralls server
        """
        # don't upload if there is no coverage file
        if not os.path.isfile(os.path.join(coverage_dirname, '.coverage')):
            warnings.warn('No coverage file exists to upload to Coveralls', UserWarning)
            return

        if self.coveralls_token:
            runner = coveralls.Coveralls(True, repo_token=self.coveralls_token,
                                         service_name='circle-ci', service_job_id=self.build_num)

            def get_coverage():
                workman = coverage.Coverage(data_file=os.path.join(coverage_dirname, '.coverage'))
                workman.load()
                workman.get_data()

                return coveralls.reporter.CoverallReporter(workman, workman.config).coverage

            with patch.object(coveralls.Coveralls, 'get_coverage', return_value=get_coverage()):
                runner.wear(dry_run=dry_run)

    def upload_coverage_report_to_code_climate(self, coverage_dirname='tests/reports', dry_run=False):
        """ Upload coverage report to Code Climate

        Args:
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            dry_run (:obj:`bool`, optional): if true, don't upload to the Coveralls server

        Raises:
            :obj:`BuildHelperError`: If error uploading code coverage to Code Climate
        """
        # don't upload if there is no coverage file
        if not os.path.isfile(os.path.join(coverage_dirname, '.coverage')):
            warnings.warn('No coverage file exists to upload to Code Climate', UserWarning)
            return

        # save coverage data to xml
        xml_cov_filename = 'coverage.xml'

        workman = coverage.Coverage(data_file=os.path.join(coverage_dirname, '.coverage'))
        workman.load()
        workman.get_data()
        workman.xml_report(outfile=xml_cov_filename)

        # download the Code Climate test reporter
        response = requests.get('https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64')
        response.raise_for_status()
        cc_path = os.path.expanduser('~/cc-test-reporter')
        with open(cc_path, 'wb') as file:
            file.write(response.content)
        os.chmod(cc_path, 0o755)

        # run the reporter
        if not dry_run:
            subprocess.check_call([cc_path, 'before-build'])
            subprocess.check_call([cc_path, 'after-build',
                                   '-t', 'coverage.py',
                                   '-r', self.code_climate_token,
                                   ])

    ########################
    # Documentation
    ########################

    def create_documentation_template(self, dirname='.'):
        """ Create Sphinx documentation template for a package

        Args:
            dirname (:obj:`str`, optional): path to package

        Raises:
            :obj:`ValueError`: if no package or more than one package is specified
        """

        parser = configparser.ConfigParser()
        parser.read(os.path.join(dirname, 'setup.cfg'))
        packages = parser.get('sphinx-apidocs', 'packages').strip().split('\n')
        if len(packages) != 1:
            raise ValueError('Sphinx configuration auto-generation only supports 1 package')

        if not os.path.isdir(os.path.join(dirname, self.proj_docs_dir)):
            os.mkdir(os.path.join(dirname, self.proj_docs_dir))

        for package in packages:
            filenames = [
                'conf.py',
                'requirements.txt',
                'requirements.rtd.txt',
                'spelling_wordlist.txt',
                'index.rst',
                'overview.rst',
                'installation.rst',
                'about.rst',
                'references.rst',
                'references.bib',
            ]

            context = {
                "package": package,
                'version': self.INITIAL_PACKAGE_VERSION,
                'year': datetime.now().year,
                'package_underline': '=' * len(package),
            }

            for filename in filenames:
                template_filename = pkg_resources.resource_filename('karr_lab_build_utils', os.path.join('templates', 'docs', filename))
                with open(template_filename, 'r') as file:
                    template = Template(file.read())
                template.stream(**context).dump(os.path.join(dirname, self.proj_docs_dir, filename))

    def make_documentation(self, spell_check=False):
        """ Make HTML documentation using Sphinx for one or more packages. Save documentation to `proj_docs_build_html_dir`

        Args:
            spell_check (:obj:`bool`): if :obj:`True`, run spell checking

        Raises:
            :obj:`BuildHelperError`: If project name not set
        """

        # create `proj_docs_static_dir`, if necessary
        if not os.path.isdir(self.proj_docs_static_dir):
            os.mkdir(self.proj_docs_static_dir)

        # compile API docs
        self.make_api_documentation()

        # build HTML documentation
        def handle_exception(app, args, exception, stderr=sys.stderr):
            raise

        with patch('sphinx.cmdline.handle_exception', handle_exception):
            self.run_method_and_capture_stderr(sphinx_main,
                                               [self.proj_docs_dir, self.proj_docs_build_html_dir])

            # run spell check
            if spell_check:
                self.run_method_and_capture_stderr(sphinx_main, [
                    '-b', 'spelling',
                    '-d', self.proj_docs_build_doctrees_dir,
                    self.proj_docs_dir,
                    self.proj_docs_build_spelling_dir,
                ])

    def make_api_documentation(self):
        """ Compile API documentation """
        config = self.get_build_config().get('docs', {})
        if config.get('api_docs', True):
            parser = configparser.ConfigParser()
            parser.read('setup.cfg')
            packages = parser.get('sphinx-apidocs', 'packages').strip().split('\n')
            for package in packages:
                self.run_method_and_capture_stderr(sphinx.ext.apidoc.main,
                                                   argv=['-f', '-P', '-o', os.path.join(self.proj_docs_dir, 'source'), package])

    def upload_documentation_to_docs_server(self, dirname='.'):
        """ Upload compiled documentation to the lab server

        Args:
            dirname (:obj:`str`, optional): path to package
        """
        with ftputil.FTPHost(self.docs_server_hostname, self.docs_server_username, self.docs_server_password) as ftp:
            with open(os.path.join(dirname, self.repo_name, '_version.py'), 'r') as file:
                mo = re.search("^__version__ = ['\"]([^'\"]*)['\"]", file.read(), re.M)
                if mo:
                    version = mo.group(1)
                else:
                    raise Exception("A version file must be defined")
            remote_root = ftp.path.join(self.docs_server_directory, self.repo_name, self.repo_branch, version)

            # delete old files
            if ftp.path.isdir(remote_root):
                ftp.rmtree(remote_root)

            # create directory for new files
            if not ftp.path.isdir(remote_root):
                ftp.makedirs(remote_root)

            # copy files to server
            local_root = os.path.join(dirname, self.proj_docs_build_html_dir)
            for root, dirnames, filenames in os.walk(local_root):
                rel_root = os.path.relpath(root, local_root)

                for dirname in dirnames:
                    rel_dirname = os.path.join(rel_root, dirname)
                    remote_dir = ftp.path.join(remote_root, rel_dirname)
                    if not ftp.path.isdir(remote_dir):
                        ftp.makedirs(remote_dir)

                for filename in filenames:
                    local_filename = os.path.join(local_root, rel_root, filename)
                    remote_filename = os.path.join(remote_root, rel_root, filename)
                    ftp.upload(local_filename, remote_filename)

            self.setup_docs_htaccess_files()

    def setup_docs_htaccess_files(self):
        """ Setup htaccess files for docs server """
        with ftputil.FTPHost(self.docs_server_hostname, self.docs_server_username, self.docs_server_password) as ftp:
            dirname = ftp.path.join(self.docs_server_directory, self.repo_name, self.repo_branch)
            lastest_version = self.get_latest_docs_version(ftp, dirname)

            context = {
                'package': self.repo_name,
                'branch': self.repo_branch,
                'version': lastest_version,
            }

            with open(pkg_resources.resource_filename('karr_lab_build_utils',
                                                      os.path.join('templates', 'docs.htaccess')), 'r') as file:
                template = Template(file.read())
            filename = ftp.path.join(self.docs_server_directory, self.repo_name, '.htaccess')
            with ftp.open(filename, 'w') as fobj:
                fobj.write(template.render(**context))

            with open(pkg_resources.resource_filename('karr_lab_build_utils',
                                                      os.path.join('templates', 'docs.branch.htaccess')), 'r') as file:
                template = Template(file.read())
            filename = ftp.path.join(self.docs_server_directory, self.repo_name, self.repo_branch, '.htaccess')
            with ftp.open(filename, 'w') as fobj:
                fobj.write(template.render(**context))

    def get_latest_docs_version(self, ftp, dirname):
        versions = list(filter(lambda subdirname: subdirname != '.htaccess', ftp.listdir(dirname)))
        if versions:
            versions.sort(key=natsort.natsort_keygen(alg=natsort.IGNORECASE))
            return versions[-1]
        else:
            raise BuildHelperError("The directory must contain documentation for at least one version")

    def log_environment(self):
        """ Log environment 

        * pip packages
        * Quilt packages
        """
        log_dir = os.path.expanduser('~/.wc/log/package-versions')
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)

        # pip packages
        lines = pip._internal.operations.freeze.freeze()
        with open(os.path.join(log_dir, 'pip.log'), 'w') as file:
            file.write('\n'.join(lines) + '\n')

        # Quilt packages
        with open(os.path.join(log_dir, 'quilt.log'), 'w') as file:
            file.write('Package' + '\t' + 'Date' + '\t' + 'Hash' + '\n')
            for pkg in quilt3.list_packages():
                for version in quilt3.list_package_versions(pkg):
                    try:
                        date = datetime.fromtimestamp(int(float(version[0]))).strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        date = version[0]
                    file.write(pkg + '\t' + date + '\t' + version[0] + '\n')

    def compile_downstream_dependencies(self, dirname='.', packages_parent_dir='..', config_filename=None):
        """ Compile the downstream dependencies of a package and save them to :obj:`config_filename`

        Args:
            dirname (:obj:`str`, optional): path to package
            packages_parent_dir (:obj:`str`, optional): path to the parent directory of the packages
            config_filename (:obj:`str`, optional): path to save configuration with list of downstream dependencies
                in YAML format

        Returns:
            :obj:`list` of :obj:`str`: downstream dependencies

        Raises:
            :obj:`BuildHelperError`: if a package has more than one module
        """
        import pkg_utils
        # pkg_utils is imported locally so that we can use karr_lab_build_utils to properly calculate its coverage;
        # :todo: figure out how to fix this

        packages_parent_dir = os.path.abspath(packages_parent_dir)

        # get the name of the current package
        parser = configparser.ConfigParser()
        parser.read(os.path.join(dirname, 'setup.cfg'))
        tmp = parser.get('coverage:run', 'source').strip().split('\n')
        if len(tmp) != 1:
            raise BuildHelperError('Package should have only one module')
        this_pkg_name = tmp[0]

        # collect the downstream dependencies by analyzing the requirements files of other packages
        # :todo: support branches
        downstream_dependencies = []
        for dirname in glob.glob(os.path.join(packages_parent_dir, '*')):
            if os.path.isdir(dirname) and os.path.isfile(os.path.join(dirname, '.circleci/config.yml')):
                other_pkg_name = dirname[len(packages_parent_dir) + 1:]
                install_requires, extras_require, _, _ = pkg_utils.get_dependencies(
                    dirname, include_extras=False, include_specs=False, include_markers=False)
                if this_pkg_name in install_requires or this_pkg_name in extras_require['all']:
                    downstream_dependencies.append(other_pkg_name)

        # save the downstream dependencies to a file
        if config_filename:
            config = {}
            if os.path.isfile(config_filename):
                with open(config_filename, 'r') as file:
                    config = yaml.load(file, Loader=yaml.FullLoader)

            config['downstream_dependencies'] = downstream_dependencies

            with open(config_filename, 'w') as file:
                yaml.dump(config, file, default_flow_style=False)

        # return the downstream dependencies
        return downstream_dependencies

    def are_package_dependencies_acyclic(self, packages_parent_dir='..'):
        """ Check if the package dependencies are acyclic so they are supported by CircleCI

        Args:
            packages_parent_dir (:obj:`str`, optional): path to the parent directory of the packages

        Returns:
            :obj:`bool`: :obj:`True` if the package dependencies are acyclic
        """
        graph = networkx.DiGraph()

        for dirname in glob.glob(os.path.join(packages_parent_dir, '*')):
            if os.path.isdir(dirname) and os.path.isfile(os.path.join(dirname, '.circleci/config.yml')):
                # get package name
                pkg = dirname[len(packages_parent_dir) + 1:]

                # create node for package
                graph.add_node(pkg)

                # create edges for dependencies
                config_filename = os.path.join(dirname, '.karr_lab_build_utils.yml')
                if os.path.isfile(config_filename):
                    with open(config_filename, 'r') as file:
                        config = yaml.load(file, Loader=yaml.FullLoader)
                    deps = config.get('downstream_dependencies', [])
                    for other_pkg in deps:
                        graph.add_edge(pkg, other_pkg)

        try:
            networkx.algorithms.cycles.find_cycle(graph)
            return False
        except networkx.NetworkXNoCycle:
            return True

    def visualize_package_dependencies(self, packages_parent_dir='..', out_filename='../package_dependencies.pdf'):
        """ Visualize downstream package dependencies as a graph

        Args:
            packages_parent_dir (:obj:`str`, optional): path to the parent directory of the packages
            out_filename (:obj:`str`, optional): path to save visualization
        """

        basename, format = os.path.splitext(out_filename)
        dot = graphviz.Digraph(format=format[1:])

        for dirname in glob.glob(os.path.join(packages_parent_dir, '*')):
            if os.path.isdir(dirname) and os.path.isfile(os.path.join(dirname, '.circleci/config.yml')):
                # get package name
                pkg = dirname[len(packages_parent_dir) + 1:]

                # create node for package
                dot.node(pkg, pkg)

                # create edges for dependencies
                config_filename = os.path.join(dirname, '.karr_lab_build_utils.yml')
                if os.path.isfile(config_filename):
                    with open(config_filename, 'r') as file:
                        config = yaml.load(file, Loader=yaml.FullLoader)
                    deps = config.get('downstream_dependencies', [])
                    for other_pkg in deps:
                        dot.edge(pkg, other_pkg)

        dot.render(filename=basename, cleanup=True)

    def trigger_tests_of_downstream_dependencies(self, config_filename='.karr_lab_build_utils.yml',
                                                 dry_run=False):
        """ Trigger CircleCI to test downstream dependencies listed in :obj:`config_filename`

        Args:
            config_filename (:obj:`str`, optional): path to YAML configuration file which contains a list of
                downstream dependencies
            dry_run (:obj:`bool`, optional): if true, don't upload to the Coveralls and Code Climate servers

        Returns:
            :obj:`list` of :obj:`str`: names of triggered packages
            :obj:`dict` of :obj:`str`, :obj:`str`: dictionary which maps names of untriggered packages to the reasons 
                why they weren't triggered

        :todo: support branches
        """

        self.logger.info("Triggering tests of downstream dependencies ...")

        # stop if this is a dry run
        if dry_run:
            self.logger.info("\tDon't trigger tests because this is a dry run")
            return (None, None)

        # stop if the tests didn't pass
        test_results = self.get_test_results()
        if test_results.get_num_errors() > 0 or test_results.get_num_failures() > 0:
            self.logger.info("\tDon't trigger tests because the tests didn't succeed")
            return (None, None)

        # read downstream dependencies
        with open(config_filename, 'r') as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
        packages = config.get('downstream_dependencies', [])

        # stop if there are no downstream dependencies
        if not packages:
            self.logger.info("\tDon't trigger tests because there are no downstream dependencies")
            return ([], {})

        upstream_repo_name = os.getenv('UPSTREAM_REPONAME', '')
        upstream_build_num = os.getenv('UPSTREAM_BUILD_NUM', '0')
        if not upstream_repo_name:
            upstream_repo_name = self.repo_name
            upstream_build_num = str(self.build_num)

        result = self.run_circleci_api('/' + str(upstream_build_num), repo_name=upstream_repo_name)
        upstream_build_time_str = result['start_time']
        upstream_build_time = dateutil.parser.parse(upstream_build_time_str)

        triggered_packages = []
        not_triggered_packages = {}
        for package in packages:
            branch = 'master'

            # get summary of recent builds
            builds = self.run_circleci_api('', repo_name=package)

            # don't trigger build if a build has already been triggered from the same upstream build
            # this prevents building the same project multiple times, including infinite looping
            already_queued = False

            for build in builds:
                response = self.run_circleci_api('/{}'.format(build['build_num']), repo_name=package)
                stream = io.StringIO(response['circle_yml']['string'])
                jobs = yaml.load(stream).get('jobs', {})
                for job in jobs.values():
                    for step in job.get('steps', []):
                        if 'run' in step and isinstance(step['run'], dict):
                            env = step['run'].get('environment', {})
                            if 'UPSTREAM_REPONAME' in env:
                                build['build_parameters']['UPSTREAM_REPONAME'] = env.get('UPSTREAM_REPONAME')
                                build['build_parameters']['UPSTREAM_BUILD_NUM'] = env.get('UPSTREAM_BUILD_NUM')

                # don'trigger a build if this is the same package which triggered the cascade
                if package == upstream_repo_name and \
                        str(build['build_num']) == upstream_build_num and \
                        build['build_num'] != self.build_num:
                    already_queued = True
                    msg = ("don't trigger tests because this package already triggered the "
                           "current build cascade\n"
                           "\t\tbuild: {}\n"
                           "\t\tbuild time: {}\n"
                           "\t\tbuild status: {}\n"
                           "\t\tupstream repo: {}\n"
                           "\t\tupstream build: {}\n"
                           "\t\tupstream build time: {}").format(build['build_num'], build['start_time'], build['status'],
                                                                 upstream_repo_name, upstream_build_num, upstream_build_time_str)
                    not_triggered_packages[package] = msg
                    self.logger.info("\t{}: {}".format(package, msg))
                    break

                # don't trigger a build if the package already been triggered from the same upstream commit
                build_parameters = build['build_parameters']
                if build_parameters and 'UPSTREAM_REPONAME' in build_parameters and \
                        build_parameters['UPSTREAM_REPONAME'] == upstream_repo_name and \
                        build_parameters['UPSTREAM_BUILD_NUM'] == upstream_build_num:
                    already_queued = True
                    msg = ("don't trigger tests because this package has already been triggered "
                           "by the current build cascade\n"
                           "\t\tbuild: {}\n"
                           "\t\tbuild time: {}\n"
                           "\t\tbuild status: {}\n"
                           "\t\tupstream repo: {}\n"
                           "\t\tupstream build: {}\n"
                           "\t\tupstream build time: {}").format(build['build_num'], build['start_time'], build['status'],
                                                                 upstream_repo_name, upstream_build_num, upstream_build_time_str)
                    not_triggered_packages[package] = msg
                    self.logger.info("\t{}: {}".format(package, msg))
                    break

                # don't trigger a build if the package has already been more recently tested than the commit time
                build_start_time = build['start_time']
                if (build_start_time is None and
                    build['status'] in ['queued', 'scheduled', 'not_running']) or \
                    (build['start_time'] is not None and
                        dateutil.parser.parse(build['start_time']) > upstream_build_time and
                        build['status'] not in ['canceled', 'infrastructure_fail', 'not_run']):
                    already_queued = True
                    msg = ("don't trigger tests because this package has already been tested since "
                           "the commit time of the current build cascade\n"
                           "\t\tbuild: {}\n"
                           "\t\tbuild time: {}\n"
                           "\t\tbuild status: {}\n"
                           "\t\tupstream repo: {}\n"
                           "\t\tupstream build: {}\n"
                           "\t\tupstream build time: {}").format(build['build_num'], build['start_time'], build['status'],
                                                                 upstream_repo_name, upstream_build_num, upstream_build_time_str)
                    not_triggered_packages[package] = msg
                    self.logger.info("\t{}: {}".format(package, msg))
                    break

            if already_queued:
                continue

            # trigger build
            self.run_circleci_api('/pipeline', version="2", method='post', repo_name=package, data={
                'branch': branch,
                'parameters': {
                    'upstream_repo_name': upstream_repo_name,
                    'upstream_build_num': int(upstream_build_num),
                }
            })
            triggered_packages.append(package)
            self.logger.info(("\t{}: trigger tests").format(package))

        return (triggered_packages, not_triggered_packages)

    def get_version(self):
        """ Get the version of this package

        Returns:
            :obj:`str`: the version
        """
        return '{0:s} (Python {1[0]:d}.{1[1]:d}.{1[2]:d})'.format(__version__, sys.version_info)

    @staticmethod
    def get_python_version():
        """ Get the Python version

        Returns:
            :obj:`str`: the Python version
        """
        return '{0[0]:d}.{0[1]:d}.{0[2]:d}'.format(sys.version_info)

    def run_method_and_capture_stdout(self, func, *args, **kwargs):
        """ Run a method that returns a numerical error value, and exit if the return value is non-zero

        Args:
            func (:obj:`function`): function to run
            *args: arguments to :obj:`func`
            **kwargs: keyword arguments to obj:`func`

        Returns:
            :obj:`str`: stdout
        """
        with abduct.captured(abduct.out(), abduct.err()) as (stdout, stderr):
            result = func(*args, **kwargs)
            out_msg = stdout.getvalue()
            err_msg = stderr.getvalue()

        if result != 0:
            sys.stderr.write(err_msg)

            sys.stderr.flush()
            sys.exit(1)

        return out_msg

    def run_method_and_capture_stderr(self, func, *args, **kwargs):
        """ Run a method that returns a numerical error value, and exit if the return value is non-zero

        Args:
            func (:obj:`function`): function to run
            *args: arguments to :obj:`func`
            **kwargs: keyword arguments to obj:`func`
        """
        with abduct.captured(abduct.err()) as stderr:
            result = func(*args, **kwargs)
            err_msg = stderr.getvalue()

        if result != 0:
            sys.stderr.write(err_msg)

            sys.stderr.flush()
            sys.exit(1)

    def analyze_package(self, package_name, messages=None, config_filename=None, verbose=False):
        """ Perform static analyses of a package using Pylint.

        The default options will identify the following issues:

        * Unused imported modules, classes, functions, and variables
        * Reimported modules, classes, functions, and variables
        * Wild card imports outside of __init__.py
        * Duplicate arguments and keys
        * Missing requirements

        Args:
            package_name (:obj:`str`): name of the package to analyze
            messages (:obj:`list` of :obj:`str`, optional): list of Pylint checks to perform
            config_filename (:obj:`str`, optional): path to Pylist configuration file (rcfile)
            verbose (:obj:`bool`, optional): if :obj:`True`, display extra Pylint information

        Returns:
            :obj:`int`: pylint return code
        """

        if messages is None:
            messages = [
                # variables
                'W0611',  # unused-import
                'W0614',  # unused-wildcard-import
                'W0613',  # unused-argument
                'W0612',  # unused-variable

                # imports
                'W0404',  # reimported
                'W0401',  # wildcard-import

                # similarities
                'E0108',  # duplicate-argument-name
                'W0109',  # duplicate-key
            ]
        msg_opts = [
            '--disable=all',
            '--enable=' + ','.join(messages),
        ]

        report_opts = [
            '--reports=n',
            '--score=n',
        ]
        other_opts = []
        if config_filename:
            other_opts.append('--rcfile={}'.format(config_filename))
        if verbose:
            other_opts.append('--verbose')
        return epylint.lint(package_name, msg_opts + report_opts + other_opts)

    def find_missing_requirements(self, package_name, dirname='.', ignore_files=None):
        """ Finding missing requirements

        Args:
            package_name (:obj:`str`): name of the package to analyze
            dirname (:obj:`str`, optional): path to package
            ignore_files (:obj:`list`, optional): files to ignore

        Returns:
            :obj:`list`: list of missing dependencies and their occurences in the code
        """
        import pkg_utils
        # pkg_utils is imported locally so that we can use karr_lab_build_utils to properly calculate its coverage;
        # :todo: figure out how to fix this

        options = attrdict.AttrDict()
        options.paths = [package_name]
        options.ignore_files = pip_check_reqs.common.ignorer(ignore_files or [])
        options.ignore_mods = pip_check_reqs.common.ignorer([])
        options.verbose = False
        options.debug = False
        options.version = False
        pip_check_reqs.find_missing_reqs.log.setLevel(logging.ERROR)

        missing = pip_check_reqs.find_missing_reqs.find_missing_reqs(options)

        # filter out optional dependencies
        install_requires, extras_require, _, _ = pkg_utils.get_dependencies(
            dirname, include_extras=False, include_specs=False, include_markers=False)
        all_deps = install_requires
        for option, opt_deps in extras_require.items():
            if option not in ['all', 'tests', 'docs']:
                all_deps += opt_deps
        missing = list(filter(lambda m: m[0].replace('-', '_') not in all_deps, missing))

        # sort missing
        missing.sort(key=natsort.natsort_keygen(key=lambda m: m[0], alg=natsort.IGNORECASE))

        return missing

    def find_unused_requirements(self, package_name, dirname='.', ignore_files=None):
        """ Finding unused_requirements

        Args:
            package_name (:obj:`str`): name of the package to analyze
            dirname (:obj:`str`, optional): path to package
            ignore_files (:obj:`list`, optional): files to ignore

        Returns:
            :obj:`list`: name of the unused dependencies
        """
        import pkg_utils
        # pkg_utils is imported locally so that we can use karr_lab_build_utils to properly calculate its coverage;
        # :todo: figure out how to fix this

        options = attrdict.AttrDict()
        options.paths = [package_name]
        options.ignore_files = pip_check_reqs.common.ignorer(ignore_files or [])
        options.ignore_mods = pip_check_reqs.common.ignorer([])
        options.ignore_reqs = pip_check_reqs.common.ignorer([])
        options.verbose = False
        options.debug = False
        options.version = False
        pip_check_reqs.find_extra_reqs.log.setLevel(logging.ERROR)

        # get all requirements
        install_requires, extras_require, _, _ = pkg_utils.get_dependencies(
            dirname, include_extras=False, include_specs=False, include_markers=False)
        all_deps = set(install_requires)
        for option, opt_deps in extras_require.items():
            if option not in ['all', 'tests', 'docs']:
                all_deps = all_deps | set(opt_deps)
        all_deps = [dep.replace('_', '-') for dep in all_deps]

        # find unused requirements
        with mock.patch('pip_check_reqs.common.find_required_modules', return_value=all_deps):
            unuseds = pip_check_reqs.find_extra_reqs.find_extra_reqs(options)

        # correct for editablly-installed packages
        useds = pip_check_reqs.common.find_imported_modules(options).keys()
        useds = [used.partition('.')[0].replace('_', '-') for used in useds]
        unuseds = list(set(unuseds).difference(set(useds)))

        # return canonical names
        unuseds = [unused.replace('-', '_') for unused in unuseds]

        # sort unuseds
        unuseds.sort(key=natsort.natsort_keygen(alg=natsort.IGNORECASE))

        return unuseds

    def upload_package_to_pypi(self, dirname='.', repository=None, upload_source=True, upload_build=True):
        """ Upload a package to PyPI

        Args:
            dirname (:obj:`str`, optional): path to package to upload
            repository (:obj:`str`, optional): name of a repository defined in the PyPI 
                configuration file or a repository URL
            upload_source (:obj:`bool`, optional): if :obj:`True`, upload source code
            upload_build (:obj:`bool`, optional): if :obj:`True`
        """
        repository = repository or self.pypi_repository
        config_filename = os.path.abspath(os.path.expanduser(self.pypi_config_filename))

        # cleanup
        if (upload_source or upload_build) and os.path.isdir(os.path.join(dirname, 'dist')):
            shutil.rmtree(os.path.join(dirname, 'dist'))
        if upload_build and os.path.isdir(os.path.join(dirname, 'build')):
            shutil.rmtree(os.path.join(dirname, 'build'))

        # convert README.md to README.rt
        pypandoc.convert_file(os.path.join(dirname, 'README.md'), 'rst', outputfile=os.path.join(dirname, "README.rst"))

        # package code
        if upload_source:
            subprocess.check_call([sys.executable, os.path.join(os.path.abspath(dirname), 'setup.py'), 'sdist'],
                                  cwd=dirname)

        if upload_build:
            subprocess.check_call([sys.executable, os.path.join(os.path.abspath(dirname), 'setup.py'), 'bdist_wheel'],
                                  cwd=dirname)

        if upload_source or upload_build:
            uploads = [os.path.join(dirname, 'dist', '*')]
        else:
            uploads = []

        # set options
        options = []

        if repository:
            options += ['--repository', repository]

        if config_filename:
            options += ['--config-file', config_filename]

        # upload
        twine.commands.upload.main(options + uploads)

        # cleanup
        os.remove(os.path.join(dirname, 'README.rst'))
        if upload_source:
            shutil.rmtree(os.path.join(dirname, 'dist'))
        if upload_build:
            shutil.rmtree(os.path.join(dirname, 'build'))

    def run_circleci_api(self, command, version="1.1", method='get', repo_type=None, repo_owner=None, repo_name=None,
                         data=None):
        """ Run the CircleCI API

        Args:
            command (:obj:`str`): API command
            version (:obj:`str`, optional): version of the API to use
            method (:obj:`str`, optional): type of HTTP request (get, post, delete)
            repo_type (:obj:`str`, optional): repository type (e.g., github)
            repo_owner (:obj:`str`, optional): repository owner
            repo_name (:obj:`str`, optional): repository name
            data (:obj:`str`, optional): data

        Returns:
            :obj:`dict`: CircleCI result

        Raises:
            :obj:`requests.exceptions.HTTPError`: if the HTTP request to CircleCI does not succeed
        """
        if not repo_type:
            repo_type = self.repo_type
        if not repo_owner:
            repo_owner = self.repo_owner
        if not repo_name:
            repo_name = self.repo_name

        url = '{}/v{}/project/{}/{}/{}{}?circle-token={}'.format(
            self.CIRCLE_API_ENDPOINT, version, repo_type, repo_owner, repo_name, command, self.circleci_api_token)
        request_method = getattr(requests, method)

        response = request_method(url, json=data)
        response.raise_for_status()
        return response.json()

    def get_build_config(self):
        """ Get build configuration

        Returns:
            :obj:`dict`: build configuration
        """
        with open('.karr_lab_build_utils.yml', 'r') as file:
            return yaml.load(file, Loader=yaml.FullLoader)

    def download_package_config_files(self):
        """ Download the configuration repository 

        Args:
            update (:obj:`bool`, optional): if :obj:`True`, update the configuration
        """
        # clone or update repo
        if os.path.isdir(self.configs_repo_path):
            try:
                repo = git.Repo(path=self.configs_repo_path)
                repo.remotes['origin'].pull()
            except git.exc.InvalidGitRepositoryError:
                temp_dir_name = tempfile.mkdtemp()
                git.Repo.clone_from(self.configs_repo_url, temp_dir_name)
                wc_utils.util.files.copytree_to_existing_destination(self.configs_repo_path, temp_dir_name)
                shutil.rmtree(self.configs_repo_path)
                os.rename(temp_dir_name, self.configs_repo_path)
        else:
            try:
                git.Repo.clone_from(self.configs_repo_url, self.configs_repo_path)
            except git.exc.GitCommandError:
                url = self.configs_repo_url.replace('://', '://{}:{}@'.format(
                    self.configs_repo_username, self.configs_repo_password))
                git.Repo.clone_from(url, self.configs_repo_path)

    def install_package_config_files(self, overwrite=False):
        """ Copy third party configs to their appropriate paths from the configs repository 

        Args:
            overwrite (:obj:`bool`, optional): if :obj:`True`, overwrite existing configuration files
        """
        filename = os.path.join(self.configs_repo_path, 'third_party', 'paths.yml')
        with open(filename, 'r') as file:
            paths = yaml.load(file, Loader=yaml.FullLoader)

        for rel_src, abs_dest in paths.items():
            abs_dest = os.path.expanduser(abs_dest)
            abs_dest_dir = os.path.dirname(abs_dest)
            if not os.path.isdir(abs_dest_dir):
                os.makedirs(abs_dest_dir)
            abs_src = os.path.join(self.configs_repo_path, 'third_party', rel_src)
            if not os.path.isfile(abs_dest) or overwrite:
                shutil.copyfile(abs_src, abs_dest)
                if rel_src == 'id_rsa':
                    os.chmod(abs_dest, stat.S_IRUSR | stat.S_IWUSR)


class TestResults(object):
    """ Unit test results

    Attributes:
        cases (:obj:`list` of :obj:`TestCase`): test case results
    """

    def __init__(self):
        self.cases = []

    @property
    def num_tests(self):
        return self.get_num_tests()

    @property
    def num_passed(self):
        return self.get_num_passed()

    @property
    def num_skipped(self):
        return self.get_num_skipped()

    @property
    def num_errors(self):
        return self.get_num_errors()

    @property
    def num_failures(self):
        return self.get_num_failures()

    def get_num_tests(self):
        """ Get the number of tests

        Returns:
            :obj:`int`: number of tests
        """
        return len(self.cases)

    def get_num_passed(self):
        """ Get the number of tests that passed

        Returns:
            :obj:`int`: number of tests that passed
        """
        return len(list(filter(lambda case: case.type == TestCaseResultType.passed, self.cases)))

    def get_num_skipped(self):
        """ Get the number of skipped tests

        Returns:
            :obj:`int`: number of skipped tests
        """
        return len(list(filter(lambda case: case.type == TestCaseResultType.skipped, self.cases)))

    def get_num_errors(self):
        """ Get the number of tests with errors

        Returns:
            :obj:`int`: number of tests with errors
        """
        return len(list(filter(lambda case: case.type == TestCaseResultType.error, self.cases)))

    def get_num_failures(self):
        """ Get the number of tests with failures

        Returns:
            :obj:`int`: number of tests with failures
        """
        return len(list(filter(lambda case: case.type == TestCaseResultType.failure, self.cases)))


class TestCaseResult(object):
    """ The result of a test case

    Attributes:
        classname (:obj:`str`): name of the class of the test case
        name (:obj:`str`): name of the test case
        filename (:obj:`str`): file where the test was defined
        line (:obj:`int`): line where the test was defined
        python_version (:obj:`str`): python version which ran the test
        type (:obj:`TestCaseResultType`): type of the result (pass, skip, error, failure)
        subtype (:obj:`str`): detailed type of the result
        message (:obj:`str`): message from the result
        details (:obj:`str`): detailed message from the result
        time (:obj:`float`): duration of the time in seconds
        stdout (:obj:`str`): standard output
        stderr (:obj:`str`): standard error
    """

    def __init__(self):
        self.classname = None
        self.name = None
        self.filename = None
        self.line = None
        self.python_version = None
        self.time = None
        self.stdout = None
        self.stderr = None
        self.type = None
        self.subtype = None
        self.message = None
        self.details = None


class TestCaseResultType(enum.Enum):
    """ Type of test case result """
    passed = 0
    skipped = 1
    error = 2
    failure = 3


class BuildHelperError(Exception):
    """ Represents :obj:`BuildHelper` errors """
    pass
