""" Karr Lab build utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-08-02
:Copyright: 2016, Karr Lab
:License: MIT
"""

from codeclimate_test_reporter.components.runner import Runner as CodeClimateRunner
from datetime import datetime
from jinja2 import Template
from pylint import epylint
from sphinx import build_main as sphinx_build
from sphinx.apidoc import main as sphinx_apidoc
from mock import patch
from six.moves import configparser
from xml.dom import minidom
import abduct
import attrdict
import capturer
import coverage
import coveralls
import dateutil.parser
import email
import email.header
import email.message
import email.utils
import enum
import fnmatch
import glob
import graphviz
# import instrumental.api
import json
import karr_lab_build_utils
import logging
import mock
import networkx
import nose
import os
import pip
import pip_check_reqs
import pip_check_reqs.find_extra_reqs
import pip_check_reqs.find_missing_reqs
# import pkg_utils # pkg_utils is not imported globally so that we can use
# karr_lab_build_utils to properly calculate its coverage; :todo: figure
# out how to fix this
import pkg_resources
import pytest
import re
import requests
import shutil
import smtplib
import subprocess
import sys
import tempfile
import time
import twine.commands.upload
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

        test_server_token (:obj:`str`): test history report server token
        coveralls_token (:obj:`str`): Coveralls token
        code_climate_token (:obj:`str`): Code Climate token

        github_api_token (obj:`str`): GitHub API token
        circleci_api_token (:obj:`str`): CircleCI API token

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

        COVERALLS_ENABLED (:obj:`bool`): if :obj:`True`, upload coverage reports to coveralls
        CODE_CLIMATE_ENABLED (:obj:`bool`): if :obj:`True`, upload coverage reports to code climate
    """

    INITIAL_PACKAGE_VERSION = '0.0.1'
    DEFAULT_BUILD_IMAGE_VERSION = '0.0.11'

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
    DEFAULT_BUILD_IMAGE = 'karrlab/build:latest'

    GITHUB_API_ENDPOINT = 'https://api.github.com'
    CIRCLE_API_ENDPOINT = 'https://circleci.com/api/v1.1'

    COVERALLS_ENABLED = True
    CODE_CLIMATE_ENABLED = True

    def __init__(self):
        """ Construct build helper """

        # get settings from environment variables
        self.test_runner = os.getenv('TEST_RUNNER', self.DEFAULT_TEST_RUNNER)
        if self.test_runner not in ['pytest', 'nose']:
            raise Exception('Unsupported test runner {}'.format(self.test_runner))

        self.repo_type = 'github'
        self.repo_name = os.getenv('CIRCLE_PROJECT_REPONAME')
        self.repo_owner = os.getenv('CIRCLE_PROJECT_USERNAME')
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

        self.test_server_token = os.getenv('TEST_SERVER_TOKEN')
        self.coveralls_token = os.getenv('COVERALLS_REPO_TOKEN')
        self.code_climate_token = os.getenv('CODECLIMATE_REPO_TOKEN')

        self.github_username = os.getenv('GITHUB_USERNAME')
        self.github_password = os.getenv('GITHUB_PASSWORD')
        self.circleci_api_token = os.getenv('CIRCLECI_API_TOKEN')

    #####################
    # Create a repository
    #####################
    def create_repository(self, dirname='.', url=None, build_image_version=None):
        """ Create a Git repository with the default directory structure

        Args:
            dirname (:obj:`str`, optional): directory for the repository
            url (:obj:`str`, optional): URL for the repository
            build_image_version (:obj:`str`, optional): build image version
        """

        name = os.path.basename(os.path.abspath(dirname))
        if not re.match('^[a-z][a-z0-9_]*$', name):
            raise Exception('Repository names should start with a letter and only include lower case letters, numbers, and underscores')

        if not build_image_version:
            build_image_version = self.DEFAULT_BUILD_IMAGE_VERSION

        # create a directory for the repository
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        # initialize Git
        import pygit2
        repo = pygit2.init_repository(dirname, origin_url=url or None)

        # setup repository
        self.setup_repository(dirname=dirname, build_image_version=build_image_version)

    def setup_repository(self, dirname='.', build_image_version=None):
        """ Setup Git repository with the default directory structure

        Args:
            dirname (:obj:`str`, optional): directory name
            build_image_version (:obj:`str`, optional): build image version
        """

        name = os.path.basename(os.path.abspath(dirname))
        if not re.match('^[a-z][a-z0-9_]*$', name):
            raise Exception('Repository names should start with a letter and only include lower case letters, numbers, and underscores')

        if not build_image_version:
            build_image_version = self.DEFAULT_BUILD_IMAGE_VERSION

        # create a directory for the repository
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        # create directories
        os.mkdir(os.path.join(dirname, name))
        os.mkdir(os.path.join(dirname, 'tests'))
        os.mkdir(os.path.join(dirname, 'tests', 'fixtures'))
        os.mkdir(os.path.join(dirname, 'tests', 'fixtures', 'secret'))
        os.mkdir(os.path.join(dirname, 'docs'))
        os.mkdir(os.path.join(dirname, 'docs', '_static'))
        os.mkdir(os.path.join(dirname, '.circleci'))

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
            '.circleci/config.yml',
            '.readthedocs.yml',
        )

        context = {
            'name': name,
            'version': self.INITIAL_PACKAGE_VERSION,
            'year': datetime.now().year,
            'build_image_version': build_image_version,
        }

        for filename in filenames:
            with open(pkg_resources.resource_filename(
                    'karr_lab_build_utils',
                    os.path.join('templates', filename)), 'r') as file:
                template = Template(file.read())
            template.stream(**context).dump(os.path.join(dirname, filename))

        with open(pkg_resources.resource_filename(
                'karr_lab_build_utils',
                os.path.join('templates', 'package', '__init__.py')), 'r') as file:
            template = Template(file.read())
        template.stream(**context).dump(os.path.join(dirname, name, '__init__.py'))

        with open(pkg_resources.resource_filename(
                'karr_lab_build_utils',
                os.path.join('templates', 'package', 'VERSION')), 'r') as file:
            template = Template(file.read())
        template.stream(**context).dump(os.path.join(dirname, name, 'VERSION'))

        self.create_documentation_template(dirname)

    ###########################
    # Register repo on CircleCI
    ###########################
    def create_circleci_build(self, repo_type=None, repo_owner=None, repo_name=None, circleci_api_token=None):
        """ Create CircleCI build for a repository

        Args:
            repo_type (:obj:`str`, optional): repository type
            repo_owner (:obj:`str`, optional): repository owner
            repo_name (:obj:`str`, optional): repository name
            circleci_api_token (:obj:`str`, optional): CircleCI API token

        Raises:
            :obj:`ValueError`: if a CircleCI build wasn't created and didn't already exist
        """
        if repo_type is None:
            repo_type = self.repo_type

        if repo_owner is None:
            repo_owner = self.repo_owner

        if repo_name is None:
            repo_name = self.repo_name

        if circleci_api_token is None:
            circleci_api_token = self.circleci_api_token

        result = self.run_circleci_api('/follow',
                                       method='post', repo_type=repo_type, repo_owner=repo_owner, repo_name=repo_name,
                                       circleci_api_token=circleci_api_token)
        if 'following' not in result or not result['following']:
            raise ValueError(
                'Unable to create CircleCI build for repository {}/{}'.format(repo_owner, repo_name))

    def get_circleci_environment_variables(self, repo_type=None, repo_owner=None, repo_name=None, circleci_api_token=None):
        """ Get the CircleCI environment variables for a repository and their partial values

        Args:
            repo_type (:obj:`str`, optional): repository type
            repo_owner (:obj:`str`, optional): repository owner
            repo_name (:obj:`str`, optional): repository name
            circleci_api_token (:obj:`str`, optional): CircleCI API token

        Returns:
            :obj:`dict`: dictionary of environment variables and their partial values
        """
        if repo_type is None:
            repo_type = self.repo_type

        if repo_owner is None:
            repo_owner = self.repo_owner

        if repo_name is None:
            repo_name = self.repo_name

        if circleci_api_token is None:
            circleci_api_token = self.circleci_api_token

        vars = self.run_circleci_api('/envvar',
                                     repo_type=repo_type, repo_owner=repo_owner, repo_name=repo_name,
                                     circleci_api_token=circleci_api_token)
        return {var['name']: var['value'] for var in vars}

    def set_circleci_environment_variables(self, vars, repo_type=None, repo_owner=None, repo_name=None, circleci_api_token=None):
        """ Set the CircleCI environment variables for a repository

        Args:
            vars (:obj:`dict`): dictionary of environment variables to set
            repo_type (:obj:`str`, optional): repository type
            repo_owner (:obj:`str`, optional): repository owner
            repo_name (:obj:`str`, optional): repository name
            circleci_api_token (:obj:`str`, optional): CircleCI API token

        Returns:
            :obj:`dict`: dictionary of environment variables and their values
        """
        if repo_type is None:
            repo_type = self.repo_type

        if repo_owner is None:
            repo_owner = self.repo_owner

        if repo_name is None:
            repo_name = self.repo_name

        if circleci_api_token is None:
            circleci_api_token = self.circleci_api_token

        # get current environment variables
        old_vars = self.get_circleci_environment_variables(
            repo_type=repo_type, repo_owner=repo_owner, repo_name=repo_name,
            circleci_api_token=circleci_api_token)

        # update environment variables
        for name, value in vars.items():
            # delete environment variables which we want to overwrite
            if name in old_vars:
                self.delete_circleci_environment_variable(name,
                                                          repo_type=repo_type, repo_owner=repo_owner, repo_name=repo_name,
                                                          circleci_api_token=circleci_api_token)

            # add environment variable
            self.run_circleci_api('/envvar',
                                  method='post', repo_type=repo_type, repo_owner=repo_owner, repo_name=repo_name,
                                  circleci_api_token=circleci_api_token, data={'name': name, 'value': value})

    def delete_circleci_environment_variable(self, var, repo_type=None, repo_owner=None, repo_name=None, circleci_api_token=None):
        """ Delete a CircleCI environment variable for a repository

        Args:
            var (:obj:`str`): name of variable to delete
            repo_type (:obj:`str`, optional): repository type
            repo_owner (:obj:`str`, optional): repository owner
            repo_name (:obj:`str`, optional): repository name
            circleci_api_token (:obj:`str`, optional): CircleCI API token
        """
        if repo_type is None:
            repo_type = self.repo_type

        if repo_owner is None:
            repo_owner = self.repo_owner

        if repo_name is None:
            repo_name = self.repo_name

        if circleci_api_token is None:
            circleci_api_token = self.circleci_api_token

        self.run_circleci_api('/envvar/{}'.format(var),
                              method='delete', repo_type=repo_type, repo_owner=repo_owner, repo_name=repo_name,
                              circleci_api_token=circleci_api_token)

    def create_codeclimate_github_webhook(self, repo_type=None, repo_owner=None, repo_name=None,
                                          github_username=None, github_password=None):
        """ Create GitHub webhook for CodeClimate

        Args:
            repo_type (:obj:`str`, optional): repository type
            repo_owner (:obj:`str`, optional): repository owner
            repo_name (:obj:`str`, optional): repository name
            github_username (:obj:`str`, optional): GitHub username
            github_password (:obj:`str`, optional): GitHub password

        Raises:
            :obj:`ValueError`: if webhook wasn't created and didn't already exist
        """
        if repo_type is None:
            repo_type = self.repo_type

        if repo_owner is None:
            repo_owner = self.repo_owner

        if repo_name is None:
            repo_name = self.repo_name

        if github_username is None:
            github_username = self.github_username

        if github_password is None:
            github_password = self.github_password

        url = '{}/repos/{}/{}/hooks'.format(self.GITHUB_API_ENDPOINT, repo_owner, repo_name)
        response = requests.post(url, auth=(github_username, github_password), json={
            'name': 'web',
            'config': {
                'url': 'https://codeclimate.com/webhooks',
                'content_type': 'form',
            },
            'events': [
                'push',
                'pull_request'
            ],
            'active': True,
        })
        if response.status_code != 201:
            if 'errors' in response.json():
                msg = response.json()['errors'][0]['message']
            else:
                msg = response.json()['message']
            raise ValueError('Unable to create webhook for {}/{}: {}'.format(repo_owner, repo_name, msg))

    #########################
    # Installing dependencies
    #########################
    def install_requirements(self):
        """ Install requirements """

        # upgrade pip, setuptools
        self.run_method_and_capture_stderr(pip.main, ['install', '-U', 'pip', 'setuptools'])

        # requirements for package
        self._install_requirements_helper('requirements.txt')
        self._install_requirements_helper('requirements.optional.txt', ignore_options=True)
        self._install_requirements_helper(os.path.join(self.proj_tests_dir, 'requirements.txt'))
        self._install_requirements_helper(os.path.join(self.proj_docs_dir, 'requirements.txt'))

    def _install_requirements_helper(self, filename, ignore_options=False):
        """ Install the packages in a requirements.txt file, including all optional dependencies

        Args:
            filename (:obj:`str`): path to requirements file
            ignore_options (:obj:`bool`, optional): if :obj:`True`, ignore option headings
                (e.g. for requirements.optional.txt)
        """
        if not os.path.isfile(filename):
            return

        # create a temporary file that has the optional markings removed
        if ignore_options:
            sanitized_file, sanitized_filename = tempfile.mkstemp(suffix='.txt')
            os.close(sanitized_file)

            with open(filename, 'r') as file:
                with open(sanitized_filename, 'w') as sanitized_file:
                    for line in file:
                        line = line.strip()
                        if line and line[0] == '[':
                            continue
                        sanitized_file.write(line + '\n')

            filename = sanitized_filename

        self.run_method_and_capture_stderr(pip.main, ['install', '-U', '--process-dependency-links', '-r', filename])

        # cleanup temporary file
        if ignore_options:
            os.remove(sanitized_filename)

    def upgrade_requirements(self):
        """ Upgrade requirements from the Karr Lab's GitHub organization 

        Returns:
            :obj:`list` of :obj:`str`: upgraded requirements from the Karr Lab's GitHub organization
        """

        # get requirements
        with abduct.captured(abduct.out(), abduct.err()) as (stdout, stderr):
            result = pip.main(['freeze'])
            out = stdout.getvalue()
            err = stderr.getvalue()

        if result != 0:
            sys.stderr.write(err)
            sys.stderr.flush()
            sys.exit(1)

        reqs = []
        for line in out.split('\n'):
            if 'github.com/KarrLab' in line and not line.startswith('-e'):
                reqs.append(line.partition('@')[0])

        # ugrade requirements
        self.run_method_and_capture_stderr(pip.main, ['install', '-U', '--process-dependency-links'] + reqs)

        return reqs

    ########################
    # Running tests
    ########################
    def run_tests(self, dirname='.', test_path='tests', verbose=False, with_xunit=False, with_coverage=False, coverage_dirname='.',
                  coverage_type=CoverageType.statement, environment=Environment.local, exit_on_failure=True,
                  ssh_key_filename='~/.ssh/id_rsa'):
        """ Run unit tests located at `test_path`.

        Optionally, generate a coverage report.
        Optionally, save the results to a file

        To configure coverage, place a .coveragerc configuration file in the root directory
        of the repository - the same directory that holds .coverage. Documentation of coverage
        configuration is in https://coverage.readthedocs.io/en/coverage-4.2/config.html

        Args:
            dirname (:obj:`str`, optional): path to package that should be tested
            test_path (:obj:`str`, optional): path to tests that should be run
            verbose (:obj:`str`, optional): if :obj:`True`, display stdout from tests
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            coverage_type (:obj:`CoverageType`, optional): type of coverage to run when :obj:`with_coverage` is :obj:`True`
            environment (:obj:`str`, optional): environment to run tests (local, docker, or circleci-local-executor)
            exit_on_failure (:obj:`bool`, optional): whether or not to exit on test failure
            ssh_key_filename (:obj:`str`, optional): path to GitHub SSH key; needed for Docker environment

        Raises:
            :obj:`BuildHelperError`: If the environment is not supported or the package directory not set
        """
        if environment == Environment.local:
            self._run_tests_local(dirname=dirname, test_path=test_path, verbose=verbose, with_xunit=with_xunit,
                                  with_coverage=with_coverage, coverage_dirname=coverage_dirname,
                                  coverage_type=coverage_type, exit_on_failure=exit_on_failure)
        elif environment == Environment.docker:
            self._run_tests_docker(dirname=dirname, test_path=test_path, verbose=verbose, with_xunit=with_xunit,
                                   with_coverage=with_coverage, coverage_dirname=coverage_dirname,
                                   coverage_type=coverage_type, ssh_key_filename=ssh_key_filename)
        elif environment == Environment.circleci:
            self._run_tests_circleci(dirname=dirname, test_path=test_path, verbose=verbose, ssh_key_filename=ssh_key_filename)
        else:
            raise BuildHelperError('Unsupported environment: {}'.format(environment))

    def _run_tests_local(self, dirname='.', test_path='tests', verbose=False, with_xunit=False, with_coverage=False, coverage_dirname='.',
                         coverage_type=CoverageType.statement, exit_on_failure=True):
        """ Run unit tests located at `test_path` locally

        Optionally, generate a coverage report.
        Optionally, save the results to a file

        To configure coverage, place a .coveragerc configuration file in the root directory
        of the repository - the same directory that holds .coverage. Documentation of coverage
        configuration is in https://coverage.readthedocs.io/en/coverage-4.2/config.html

        Args:
            dirname (:obj:`str`, optional): path to package that should be tested
            test_path (:obj:`str`, optional): path to tests that should be run
            verbose (:obj:`str`, optional): if :obj:`True`, display stdout from tests
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            coverage_type (:obj:`CoverageType`, optional): type of coverage to run when :obj:`with_coverage` is :obj:`True`
            exit_on_failure (:obj:`bool`, optional): whether or not to exit on test failure

        Raises:
            :obj:`BuildHelperError`: If the package directory not set
        """

        py_v = self.get_python_version()
        abs_xml_latest_filename = os.path.join(
            self.proj_tests_xml_dir, '{0}.{1}.xml'.format(self.proj_tests_xml_latest_filename, py_v))

        if with_coverage:
            if coverage_type == CoverageType.statement:
                cov = coverage.coverage(data_file=os.path.join(coverage_dirname, '.coverage'),
                                        data_suffix=py_v, config_file=True)
                cov.start()
            elif coverage_type == CoverageType.branch:
                cov = coverage.coverage(data_file=os.path.join(coverage_dirname, '.coverage'),
                                        data_suffix=py_v, config_file=True, branch=True)
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
            test_path = re.sub('::(.+?)(\.)', r'::\1::', test_path)

            argv = [test_path]
            if verbose:
                argv.append('--capture=no')
            if with_xunit:
                argv.append('--junitxml=' + abs_xml_latest_filename)

            result = pytest.main(argv)
        elif self.test_runner == 'nose':
            test_path = test_path.replace('::', ':', 1)
            test_path = test_path.replace('::', '.', 1)

            argv = ['nosetests', test_path]
            if verbose:
                argv.append('--nocapture')
            if with_xunit:
                argv += ['--with-xunit', '--xunit-file', abs_xml_latest_filename]

            result = int(not nose.run(argv=argv))
        else:
            raise Exception('Unsupported test runner {}'.format(self.test_runner))

        if with_coverage:
            cov.stop()  # pragma: no cover # this line can't be covered
            cov.save()

        if exit_on_failure and result != 0:
            sys.exit(1)

    def _run_tests_docker(self, dirname='.', test_path='tests', verbose=False, with_xunit=False, with_coverage=False, coverage_dirname='.',
                          coverage_type=CoverageType.statement, ssh_key_filename='~/.ssh/id_rsa'):
        """ Run unit tests located at `test_path` using a Docker image:

        #. Create a container based on the build image (e.g, karrlab/build:latest)
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
            verbose (:obj:`str`, optional): if :obj:`True`, display stdout from tests
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            coverage_type (:obj:`CoverageType`, optional): type of coverage to run when :obj:`with_coverage` is :obj:`True`
            ssh_key_filename (:obj:`str`, optional): path to GitHub SSH key
        """

        ssh_key_filename = os.path.expanduser(ssh_key_filename)

        # pick container name
        basename = os.path.basename(os.path.abspath(dirname))
        now = datetime.now()
        container = 'build-{0}-{1.year}-{1.month}-{1.day}-{1.hour}-{1.minute}-{1.second}'.format(basename, now)

        # get Python version
        py_v = '{}.{}'.format(sys.version_info[0], sys.version_info[1])

        # create container
        print('\n\n')
        print('=====================================')
        print('== Creating container')
        print('=====================================')
        self._run_docker_command(['run', '-it', '-d', '--name', container, self.build_image, 'bash'])

        # copy GitHub SSH key to container
        print('\n\n')
        print('=====================================')
        print('== Copying SSH key to container')
        print('=====================================')
        self._run_docker_command(['cp', ssh_key_filename, container + ':/root/.ssh/'])

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

        # install pkg_utils
        print('\n\n')
        print('=====================================')
        print('== Install pkg_utils')
        print('=====================================')
        build_utils_uri = 'git+https://github.com/KarrLab/pkg_utils.git#egg=pkg_utils'
        self._run_docker_command(['exec', container, 'bash', '-c',
                                  'pip{} install -U --process-dependency-links {}'.format(py_v, build_utils_uri)])

        # install Karr Lab build utils
        print('\n\n')
        print('=====================================')
        print('== Install karr_lab_build_utils')
        print('=====================================')
        build_utils_uri = 'git+https://github.com/KarrLab/karr_lab_build_utils.git#egg=karr_lab_build_utils'
        self._run_docker_command(['exec', container, 'bash', '-c',
                                  'pip{} install -U --process-dependency-links {}'.format(py_v, build_utils_uri)])

        # install package
        print('\n\n')
        print('=====================================')
        print('== Install package')
        print('=====================================')
        self._run_docker_command(['exec', container, 'bash', '-c',
                                  'cd /root/project && pip{} install --process-dependency-links -e .'.format(py_v)])

        # install dependencies
        print('\n\n')
        print('=====================================')
        print('== Install dependencies')
        print('=====================================')
        self._run_docker_command(['exec', container, 'bash', '-c',
                                  'cd /root/project && karr_lab_build_utils{} upgrade-requirements'.format(py_v)])

        # test package in container
        print('\n\n')
        print('=====================================')
        print('== Running tests')
        print('=====================================')
        options = []

        options += ['--test-path', test_path]

        if with_coverage:
            options += ['--with-coverage', '--coverage-type', coverage_type.name]

        if with_xunit:
            options.append('--with-xunit')

        if verbose:
            options.append('--verbose')

        self._run_docker_command(['exec', container, 'bash', '-c',
                                  'cd /root/project && karr_lab_build_utils{} run-tests {}'.format(py_v, ' '.join(options))],
                                 raise_error=False)

        if with_coverage:
            out = self._run_docker_command(['exec', container, 'bash', '-c', 'ls -la ' +
                                            os.path.join('/root', 'project', '.coverage.{}.*'.format(py_v))])
            match = re.search('/root/project/(\.coverage\.\d+\.\d+\.\d+)', out)
            self._run_docker_command(['cp', container + ':' + match.group(0), os.path.join(coverage_dirname, match.group(1))])

        if with_xunit:
            out = self._run_docker_command(['exec', container, 'bash', '-c', 'ls -la ' +
                                            os.path.join('/root', 'project', self.DEFAULT_PROJ_TESTS_XML_DIR,
                                                         '{}.{}.*.xml'.format(self.DEFAULT_PROJ_TESTS_XML_LATEST_FILENAME, py_v))])
            match = re.search('/root/project/{}/({}\.\d+\.\d+\.\d+.xml)'.format(self.DEFAULT_PROJ_TESTS_XML_DIR,
                                                                                self.DEFAULT_PROJ_TESTS_XML_LATEST_FILENAME), out)
            self._run_docker_command(['cp', container + ':' + match.group(0), os.path.join(self.proj_tests_xml_dir, match.group(1))])

        # stop and remove container
        print('\n\n')
        print('=====================================')
        print('== Removing container')
        print('=====================================')
        self._run_docker_command(['rm', '-f', container])

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
        with capturer.CaptureOutput() as captured:
            process = subprocess.Popen(['docker'] + cmd, cwd=cwd)
            while process.poll() is None:
                time.sleep(0.5)
            out = captured.get_text()
        if process.returncode != 0 and raise_error:
            raise BuildHelperError(out)

        return out

    def _run_tests_circleci(self, dirname='.', test_path='tests', verbose=False, ssh_key_filename='~/.ssh/id_rsa'):
        """ Run unit tests located at `test_path` using the CircleCI local executor. This will run the same commands defined in
        ``.circle/config.yml`` as the cloud version of CircleCI.

        Args:
            dirname (:obj:`str`, optional): path to package that should be tested
            test_path (:obj:`str`, optional): path to tests that should be run
            verbose (:obj:`str`, optional): if :obj:`True`, display stdout from tests
            ssh_key_filename (:obj:`str`, optional): path to GitHub SSH key

        Raises:
            :obj:`BuildHelperError`: if the tests fail
        """
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
            config = yaml.load(file)

        image_name = config['jobs']['build']['docker'][0]['image']
        if image_name.endswith('.with_ssh_key'):
            image_with_ssh_key_name = image_name
            image_name = image_name[:-13]
        else:
            image_with_ssh_key_name = image_name + '.with_ssh_key'

        shutil.copyfile(circleci_config_filename, backup_circleci_config_filename)
        config['jobs']['build']['docker'][0]['image'] = image_with_ssh_key_name
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
            file.write('COPY circleci_docker_context/GITHUB_SSH_KEY /root/.ssh/id_rsa\n')
            file.write('ENV TEST_SERVER_TOKEN={}\n'.format(self.test_server_token or ''))
            file.write('RUN eval `ssh-agent` && ssh-add /root/.ssh/id_rsa\n')
            file.write('CMD bash\n')

        self._run_docker_command(['build',
                                  '--tag', image_with_ssh_key_name,
                                  '-f', os.path.join('circleci_docker_context', 'Dockerfile_Circleci'),
                                  '.'],
                                 cwd=karr_lab_build_utils_dirname)

        # test package
        with capturer.CaptureOutput() as captured:
            process = subprocess.Popen(['circleci',
                                        '--env', 'test_path={}'.format(test_path),
                                        '--env', 'verbose={:d}'.format(verbose),
                                        '--env', 'dry_run=1',
                                        'build'], cwd=dirname)
            while process.poll() is None:
                time.sleep(0.5)
            out = captured.get_text()

        # revert CircleCI config file
        os.remove(circleci_config_filename)
        shutil.move(backup_circleci_config_filename, circleci_config_filename)

        # delete docker image
        self._run_docker_command(['rmi', image_with_ssh_key_name], raise_error=False)

        # cleanup circleci context
        shutil.rmtree(circleci_context_dirname)

        # raise error if tests didn't pass
        if process.returncode != 0 or 'Task failed' in out:
            raise BuildHelperError(out.encode('utf-8'))

    def get_test_results(self):
        """ Load test results from a set of XML files

        Results:
            :obj:`TestResults`: test results
        """
        test_results = TestResults()

        filename_pattern = os.path.join(self.proj_tests_xml_dir,
                                        '{0}.*.xml'.format(self.proj_tests_xml_latest_filename))
        for filename in glob.glob(filename_pattern):
            match = re.match('^{}\.(.*?)\.xml$'.format(self.proj_tests_xml_latest_filename), os.path.basename(filename))
            python_version = match.group(1)

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

    def get_test_results_status(self, test_results, build_exit_code, reports_error, dry_run=False):
        """ Get the status of a set of results

        * Old err
        * New error
        * Fixed error
        * New downstream error

        Args:
            test_results (:obj:`TestResults`): test results
            build_exit_code (:obj:`int`): Exit code of the build
            reports_error (:obj:`bool`): :obj:`True` if there was an error generating and/or archiving the reports
            dry_run (:obj:`bool`, optional): if true, don't upload to the coveralls and code climate servers

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
        if (build_exit_code != 0 or reports_error) and test_results.get_num_tests() == 0:
            is_other_error = True
            is_new_error = False
            is_old_error = False
            is_fixed = False
        else:
            is_other_error = False
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

    def do_post_test_tasks(self, build_exit_code, dry_run=False):
        """ Do all post-test tasks for CircleCI

        * Make test and coverage reports
        * Compile documentation
        * Archive test and coverage reports to the Karr Lab test history server, Coveralls, and Code Climate
        * Trigger tests of downstream dependencies
        * Notify authors of new failures in downstream packages

        Args:
            build_exit_code (:obj:`int`): Exit code of the build
            dry_run (:obj:`bool`, optional): if true, don't upload to the coveralls and code climate servers

        Returns:
            :obj:`list` of :obj:`str`: names of triggered packages
            :obj:`dict`: status of a set of results
        """
        try:
            self.make_and_archive_reports(dry_run=dry_run)
            reports_error = False
        except Exception as exception:
            reports_error = True

        triggered_packages = self.trigger_tests_of_downstream_dependencies(dry_run=dry_run)
        status = self.send_email_notifications(build_exit_code, reports_error, dry_run=dry_run)
        return (triggered_packages, status)

    def send_email_notifications(self, build_exit_code, reports_error, dry_run=False):
        """ Send email notifications of failures, fixes, and downstream failures

        Args:
            build_exit_code (:obj:`int`): Exit code of the build
            reports_error (:obj:`bool`): :obj:`True` if there was an error generating and/or archiving the reports
            dry_run (:obj:`bool`, optional): if true, don't upload to the coveralls and code climate servers

        Returns:
            :obj:`dict`: status of a set of results
        """
        test_results = self.get_test_results()
        status = self.get_test_results_status(test_results, build_exit_code, reports_error, dry_run=dry_run)

        # stop if this is a dry run
        if dry_run:
            return status

        # build context for email
        result = self.run_circleci_api('/' + str(self.build_num))
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
        }

        if status['is_new_downstream_error']:
            upstream_repo_name = os.getenv('UPSTREAM_REPONAME', '')
            upstream_build_num = int(os.getenv('UPSTREAM_BUILD_NUM', '0'))
            result = self.run_circleci_api('/' + str(upstream_build_num), repo_name=upstream_repo_name)
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

        recipients = [{'name': 'Whole-Cell Modeling Developers', 'email': 'wholecell-developers@googlegroups.com'}]

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
            recipients.append({'name': context['upstream']['committer_name'], 'email': context['upstream']['committer_email']})
            subject = '[Builds] [{1}] commit {0} to {1} may have broken {2}'.format(
                context['upstream']['commit'], context['upstream']['repo_name'], context['repo_name'])
            self._send_notification_email(recipients, subject, 'new_downstream_error.html', context)

        return status

    def _send_notification_email(self, recipients, subject, template_filename, context, dry_run=False):
        """ Send an email notification of test results

        Args:
            recipients (:obj:`list` of :obj:`dict`): recipient names and email addresses
            subject (:obj:`str`): subject
            template_filename (obj:`str`): path to template
            context (obj:`dict`): context for template
            dry_run (:obj:`bool`, optional): if true, don't upload to the coveralls and code climate servers
        """
        full_template_filename = pkg_resources.resource_filename(
            'karr_lab_build_utils', os.path.join('templates', 'email_notifications', template_filename))
        with open(full_template_filename, 'r') as file:
            template = Template(file.read())
            body = template.render(**context)

        msg = email.message.Message()
        msg['From'] = email.utils.formataddr((str(email.header.Header('Karr Lab Build System', 'utf-8')), 'noreply@karrlab.org'))
        tos = []
        for recipient in recipients:
            tos.append(email.utils.formataddr((str(email.header.Header(recipient['name'], 'utf-8')), recipient['email'])))
        msg['To'] = ', '.join(tos)
        msg['Subject'] = subject
        msg.add_header('Content-Type', 'text/html')
        msg.set_payload(body)

        if not dry_run:
            smtp = smtplib.SMTP('smtp.gmail.com:587')
            smtp.ehlo()
            smtp.starttls()
            smtp.login('karr.lab.daemon', os.getenv('KARR_LAB_DAEMON_GMAIL_PASSWORD'))
            smtp.sendmail('noreply@karrlab.org', [recipient['email'] for recipient in recipients], msg.as_string())
            smtp.quit()

    def make_and_archive_reports(self, coverage_dirname='.', dry_run=False):
        """ Make and archive reports:

        * Upload test report to history server
        * Upload coverage report to Coveralls and Code Climate

        Args:
            coverage_dirname (:obj:`str`, optional): directory to merge coverage files
            dry_run (:obj:`bool`, optional): if true, don't upload to the coveralls and code climate servers
        """

        """ test reports """
        # Upload test report to history server
        self.archive_test_report()

        """ coverage """
        # Merge coverage reports
        # Generate HTML report
        # Upload coverage report to Coveralls and Code Climate
        self.combine_coverage_reports(coverage_dirname=coverage_dirname)
        self.archive_coverage_report(coverage_dirname=coverage_dirname, dry_run=dry_run)

        """ documentation """
        self.make_documentation()

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
            self.proj_tests_xml_dir, '{0}.*.xml'.format(self.proj_tests_xml_latest_filename))
        for abs_xml_latest_filename in glob.glob(abs_xml_latest_filename_pattern):
            match = re.match('^.*?\.(\d+\.\d+\.\d+)\.xml$', abs_xml_latest_filename)
            pyv = match.group(1)
            r = requests.post('http://tests.karrlab.org/rest/submit_report',
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
    def combine_coverage_reports(self, coverage_dirname='.'):
        """
        Args:
            coverage_dirname (:obj:`str`, optional): directory to merge coverage files
        """
        data_paths = []
        for name in glob.glob(os.path.join(coverage_dirname, '.coverage.*')):
            data_path = tempfile.mktemp()
            shutil.copyfile(name, data_path)
            data_paths.append(data_path)

        coverage_doc = coverage.coverage(data_file=os.path.join(coverage_dirname, '.coverage'))
        coverage_doc.combine(data_paths=data_paths)
        coverage_doc.save()

    def archive_coverage_report(self, coverage_dirname='.', dry_run=False):
        """ Archive coverage report:

        Args:
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            dry_run (:obj:`bool`, optional): if true, don't upload to the coveralls and code climate servers

        * Upload report to Coveralls and Code Climate
        """

        # upload to Coveralls
        if self.COVERALLS_ENABLED:
            self.upload_coverage_report_to_coveralls(coverage_dirname=coverage_dirname, dry_run=dry_run)

        # upload to Code Climate
        if self.CODE_CLIMATE_ENABLED:
            self.upload_coverage_report_to_code_climate(coverage_dirname=coverage_dirname, dry_run=dry_run)

    def upload_coverage_report_to_coveralls(self, coverage_dirname='.', dry_run=False):
        """ Upload coverage report to Coveralls

        Args:
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            dry_run (:obj:`bool`, optional): if true, don't upload to the coveralls server
        """
        if self.coveralls_token:
            runner = coveralls.Coveralls(True, repo_token=self.coveralls_token,
                                         service_name='circle-ci', service_job_id=self.build_num)

            def get_coverage():
                workman = coverage.coverage(data_file=os.path.join(coverage_dirname, '.coverage'))
                workman.load()
                workman.get_data()

                return coveralls.reporter.CoverallReporter(workman, workman.config).report()

            with patch.object(coveralls.Coveralls, 'get_coverage', return_value=get_coverage()):
                runner.wear(dry_run=dry_run)

    def upload_coverage_report_to_code_climate(self, coverage_dirname='.', dry_run=False):
        """ Upload coverage report to Code Climate

        Args:
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            dry_run (:obj:`bool`, optional): if true, don't upload to the coveralls server

        Raises:
            :obj:`BuildHelperError`: If error uploading code coverage to Code Climate
        """
        if self.code_climate_token:
            code_climate_runner = CodeClimateRunner([
                '--token', self.code_climate_token,
                '--file', os.path.join(coverage_dirname, '.coverage'),
            ])
            if not dry_run:
                self.run_method_and_capture_stderr(code_climate_runner.run)

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
            context = {
                "package": package,
                'version': self.INITIAL_PACKAGE_VERSION,
                'year': datetime.now().year,
                'package_underline': '=' * len(package),
            }

            # configuration
            with open(pkg_resources.resource_filename('karr_lab_build_utils', 'templates/docs/conf.py'), 'r') as file:
                template = Template(file.read())
            template.stream(**context).dump(os.path.join(dirname, self.proj_docs_dir, 'conf.py'))

            # requirements
            with open(pkg_resources.resource_filename('karr_lab_build_utils', 'templates/docs/requirements.txt'), 'r') as file:
                template = Template(file.read())
            template.stream(**context).dump(os.path.join(dirname, self.proj_docs_dir, 'requirements.txt'))

            # requirements
            with open(pkg_resources.resource_filename('karr_lab_build_utils', 'templates/docs/conda.environment.yml'), 'r') as file:
                template = Template(file.read())
            template.stream(**context).dump(os.path.join(dirname, self.proj_docs_dir, 'conda.environment.yml'))

            # requirements
            with open(pkg_resources.resource_filename('karr_lab_build_utils', 'templates/docs/spelling_wordlist.txt'), 'r') as file:
                template = Template(file.read())
            template.stream(**context).dump(os.path.join(dirname, self.proj_docs_dir, 'spelling_wordlist.txt'))

            # index
            with open(pkg_resources.resource_filename('karr_lab_build_utils', 'templates/docs/index.rst'), 'r') as file:
                template = Template(file.read())
            template.stream(**context).dump(os.path.join(dirname, self.proj_docs_dir, 'index.rst'))

            # references
            with open(pkg_resources.resource_filename('karr_lab_build_utils', 'templates/docs/references.rst'), 'r') as file:
                template = Template(file.read())
            template.stream(**context).dump(os.path.join(dirname, self.proj_docs_dir, 'references.rst'))

            with open(pkg_resources.resource_filename('karr_lab_build_utils', 'templates/docs/references.bib'), 'r') as file:
                template = Template(file.read())
            template.stream(**context).dump(os.path.join(dirname, self.proj_docs_dir, 'references.bib'))

            # overview
            with open(pkg_resources.resource_filename('karr_lab_build_utils', 'templates/docs/overview.rst'), 'r') as file:
                template = Template(file.read())
            template.stream(**context).dump(os.path.join(dirname, self.proj_docs_dir, 'overview.rst'))

            # installation
            with open(pkg_resources.resource_filename('karr_lab_build_utils', 'templates/docs/installation.rst'), 'r') as file:
                template = Template(file.read())
            template.stream(**context).dump(os.path.join(dirname, self.proj_docs_dir, 'installation.rst'))

            # about
            with open(pkg_resources.resource_filename('karr_lab_build_utils', 'templates/docs/about.rst'), 'r') as file:
                template = Template(file.read())
            template.stream(**context).dump(os.path.join(dirname, self.proj_docs_dir, 'about.rst'))

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

        # build HTML documentation
        self.run_method_and_capture_stderr(sphinx_build, ['sphinx-build', self.proj_docs_dir, self.proj_docs_build_html_dir])

        # run spell check
        if spell_check:
            self.run_method_and_capture_stderr(sphinx_build, [
                'sphinx-build',
                '-b', 'spelling',
                '-d', self.proj_docs_build_doctrees_dir,
                self.proj_docs_dir,
                self.proj_docs_build_spelling_dir,
            ])

    def compile_downstream_dependencies(self, dirname='.', packages_parent_dir='..', downstream_dependencies_filename=None):
        """ Compile the downstream dependencies of a package and save them to :obj:`downstream_dependencies_filename`

        Args:
            dirname (:obj:`str`, optional): path to package
            packages_parent_dir (:obj:`str`, optional): path to the parent directory of the packages
            downstream_dependencies_filename (:obj:`str`, optional): path to save list of downstream dependencies in YAML format

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
        if downstream_dependencies_filename:
            with open(downstream_dependencies_filename, 'w') as file:
                yaml.dump(downstream_dependencies, file, default_flow_style=False)

        # return the downstream dependencies
        return downstream_dependencies

    def are_package_dependencies_acyclic(self, packages_parent_dir='..'):
        """ Check if the package dependencies are acyclic so they are suported by CircleCI

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
                dep_filename = os.path.join(dirname, '.circleci/downstream_dependencies.yml')
                if os.path.isfile(dep_filename):
                    with open(dep_filename, 'r') as file:
                        deps = yaml.load(file)
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
                dep_filename = os.path.join(dirname, '.circleci/downstream_dependencies.yml')
                if os.path.isfile(dep_filename):
                    with open(dep_filename, 'r') as file:
                        deps = yaml.load(file)
                    for other_pkg in deps:
                        dot.edge(pkg, other_pkg)

        dot.render(filename=basename, cleanup=True)

    def trigger_tests_of_downstream_dependencies(self, downstream_dependencies_filename='.circleci/downstream_dependencies.yml',
                                                 dry_run=False):
        """ Trigger CircleCI to test downstream dependencies listed in :obj:`downstream_dependencies_filename`

        Args:
            downstream_dependencies_filename (:obj:`str`, optional): path to YAML file which contains a list of downstream dependencies
            dry_run (:obj:`bool`, optional): if true, don't upload to the coveralls and code climate servers

        Returns:
            :obj:`list` of :obj:`str`: names of triggered packages

        :todo: support branches
        """

        # stop if this is a dry run
        if dry_run:
            return []

        # stop if the tests didn't pass
        test_results = self.get_test_results()
        if test_results.get_num_errors() > 0 or test_results.get_num_failures() > 0:
            return []

        # read downstream dependencies
        with open(downstream_dependencies_filename, 'r') as file:
            packages = yaml.load(file)

        # stop if there are no downstream dependencies
        if not packages:
            return []

        upstream_repo_name = os.getenv('UPSTREAM_REPONAME', '')
        upstream_build_num = os.getenv('UPSTREAM_BUILD_NUM', '0')
        if not upstream_repo_name:
            upstream_repo_name = self.repo_name
            upstream_build_num = str(self.build_num)

        result = self.run_circleci_api('/' + str(upstream_build_num), repo_name=upstream_repo_name)
        upstream_build_time = dateutil.parser.parse(result['all_commit_details'][0]['committer_date'])

        triggered_packages = []
        for package in packages:
            branch = 'master'

            # get summary of recent builds
            builds = self.run_circleci_api('', repo_name=package)

            # don't trigger build if a build has already been triggered from the same upstream build
            # this prevents building the same project multiple times, including infinite looping
            already_queued = False

            for build in builds:
                # don'trigger a build if this is the same package which triggered the cascade
                if package == upstream_repo_name and \
                        str(build['build_num']) == upstream_build_num and \
                        build['build_num'] != self.build_num:
                    already_queued = True
                    break

                # don't trigger a build if the package already been triggered from the same upstream commit
                build_parameters = build['build_parameters']
                if build_parameters and 'UPSTREAM_REPONAME' in build_parameters and \
                        build_parameters['UPSTREAM_REPONAME'] == upstream_repo_name and \
                        build_parameters['UPSTREAM_BUILD_NUM'] == upstream_build_num:
                    already_queued = True
                    break

                # don't trigger a build if the package has already been more recently tested than the commit time
                build_start_time = build['start_time']
                if build_start_time is None or dateutil.parser.parse(build['start_time']) > upstream_build_time:
                    already_queued = True
                    break

            if already_queued:
                continue

            # trigger build
            self.run_circleci_api('/tree/{}'.format(branch), method='post', repo_name=package, data={
                'build_parameters': {
                    'UPSTREAM_REPONAME': upstream_repo_name,
                    'UPSTREAM_BUILD_NUM': upstream_build_num,
                }
            })
            triggered_packages.append(package)

        return triggered_packages

    def get_version(self):
        """ Get the version of this package

        Returns:
            :obj:`str`: the version
        """
        return '{0:s} (Python {1[0]:d}.{1[1]:d}.{1[2]:d})'.format(karr_lab_build_utils.__version__, sys.version_info)

    @staticmethod
    def get_python_version():
        """ Get the Python version

        Returns:
            :obj:`str`: the Python version
        """
        return '{0[0]:d}.{0[1]:d}.{0[2]:d}'.format(sys.version_info)

    def run_method_and_capture_stderr(self, func, *args, **kwargs):
        """ Run a method that returns a numerical error value, and exit if the return value is non-zero

        Args:
            func (:obj:`function`): function to run
        """
        with abduct.captured(abduct.err()) as stderr:
            result = func(*args, **kwargs)
            err_msg = stderr.getvalue()

        if result != 0:
            sys.stderr.write(err_msg)

            sys.stderr.flush()
            sys.exit(1)

    def analyze_package(self, package_name, messages=None):
        """ Perform static analyses of a package using Pylint.

        The default options will identify the following issues:

        * Unused imported modules, classes, functions, and variables
        * Reimported modules, classes, functions, and variables
        * Wild card imports outside of __init__.py
        * Duplicate arguments and keys
        * Missing requirements

        Args:
            package_name (:obj:`str`): name of the package to analyze
            messages (:obj:`list` of :obj:`str`): list of Pylint checks to perform
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
        epylint.lint(package_name, msg_opts + report_opts)

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

        return unuseds

    def upload_package_to_pypi(self, dirname='.', repository='pypi', pypi_config_filename='~/.pypirc'):
        """ Upload a package to PyPI

        Args:
            dirname (:obj:`str`, optional): path to package to upload
            repository (:obj:`str`, optional): repository to upload code to (section in .pypirc or a full URL)
            pypi_config_filename (:obj:`str`, optional): path to .pypirc
        """
        # cleanup
        if os.path.isdir(os.path.join(dirname, 'build')):
            shutil.rmtree(os.path.join(dirname, 'build'))
        if os.path.isdir(os.path.join(dirname, 'dist')):
            shutil.rmtree(os.path.join(dirname, 'dist'))

        # package code
        subprocess.check_call([sys.executable, os.path.join(os.path.abspath(dirname), 'setup.py'), 'sdist', 'bdist_wheel'],
                              cwd=dirname)

        # upload
        options = []

        if repository:
            options += ['--repository', repository]

        if pypi_config_filename:
            options += ['--config-file', os.path.abspath(os.path.expanduser(pypi_config_filename))]

        uploads = []
        for path in glob.glob(os.path.join(dirname, 'dist', '*')):
            uploads.append(path)
        twine.commands.upload.main(options + uploads)

        # cleanup
        shutil.rmtree(os.path.join(dirname, 'build'))
        shutil.rmtree(os.path.join(dirname, 'dist'))

    def run_circleci_api(self, command, method='get', repo_type=None, repo_owner=None, repo_name=None,
                         data=None, circleci_api_token=None):
        """ Run the CircleCI API

        Args:
            command (:obj:`str`): API command
            method (:obj:`str`): type of HTTP request (get, post, delete)
            repo_type (:obj:`str`, optional): repository type (e.g., github)
            repo_owner (:obj:`str`, optional): repository owner
            repo_name (:obj:`str`, optional): repository name
            data (:obj:`str`, optional): data
            circleci_api_token (:obj:`str`, optional): CircleCI API token

        Returns:
            :obj:`dict`: CircleCI result
        """
        if not repo_type:
            repo_type = self.repo_type
        if not repo_owner:
            repo_owner = self.repo_owner
        if not repo_name:
            repo_name = self.repo_name
        if not circleci_api_token:
            circleci_api_token = self.circleci_api_token

        url = '{}/project/{}/{}/{}{}?circle-token={}'.format(
            self.CIRCLE_API_ENDPOINT, repo_type, repo_owner, repo_name, command, circleci_api_token)
        request_method = getattr(requests, method)

        response = request_method(url, json=data)
        response.raise_for_status()
        return response.json()


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
        classname (obj:`str`): name of the class of the test case
        name (obj:`str`): name of the test case
        filename (obj:`str`): file where the test was defined
        line (obj:`int`): line where the test was defined
        python_version (obj:`str`): python version which ran the test
        type (obj:`TestCaseResultType`): type of the result (pass, skip, error, failure)
        subtype (obj:`str`): detailed type of the result
        message (obj:`str`): message from the result
        details (obj:`str`): detailed message from the result
        time (obj:`float`): duration of the time in seconds
        stdout (obj:`str`): standard output
        stderr (obj:`str`): standard error
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
