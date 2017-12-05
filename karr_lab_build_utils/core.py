""" Karr Lab build utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-08-02
:Copyright: 2016, Karr Lab
:License: MIT
"""

from codeclimate_test_reporter.components.runner import Runner as CodeClimateRunner
from configparser import ConfigParser
from coverage import coverage
from datetime import datetime
from jinja2 import Template
from sphinx import build_main as sphinx_build
from sphinx.apidoc import main as sphinx_apidoc
from mock import patch
import abduct
import coveralls
import glob
import karr_lab_build_utils
import nose
import os
import pip
import pkg_resources
import pytest
import re
import requests
import shutil
import subprocess
import sys
import tempfile
import time
import twine.commands.upload
import yaml


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
        circle_api_token (:obj:`str`): CircleCI API token

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
        self.circle_api_token = os.getenv('CIRCLE_API_TOKEN')

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
    def create_circleci_build(self):
        """ Create CircleCI build for a repository 

        Raises:
            :obj:`ValueError`: if a CircleCI build wasn't created and didn't already exist
        """
        url = '{}/project/{}/{}/{}/follow?circle-token={}'.format(
            self.CIRCLE_API_ENDPOINT, self.repo_type, self.repo_owner, self.repo_name, self.circle_api_token)
        response = requests.post(url)
        response.raise_for_status()
        response_json = response.json()
        if 'following' not in response_json or not response_json['following']:
            raise ValueError(
                'Unable to create CircleCI build for repository {}/{}'.format(self.repo_owner, self.repo_name))

    def create_codeclimate_github_webhook(self):
        """ Create GitHub webhook for CodeClimate

        Raises:
            :obj:`ValueError`: if webook wasn't created and didn't already exist
        """
        url = '{}/repos/{}/{}/hooks'.format(self.GITHUB_API_ENDPOINT, self.repo_owner, self.repo_name)
        response = requests.post(url, auth=(self.github_username, self.github_password), json={
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
            raise ValueError('Unable to create webhook for {}/{}: {}'.format(self.repo_owner, self.repo_name, msg))

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

        self.run_method_and_capture_stderr(pip.main, ['install', '-U', '-r', filename])

        # cleanup temporary file
        if ignore_options:
            os.remove(sanitized_filename)

    ########################
    # Running tests
    ########################
    def run_tests(self, test_path='tests', with_xunit=False, with_coverage=False, coverage_dirname='.',
                  environment='local', exit_on_failure=True):
        """ Run unit tests located at `test_path`.

        Optionally, generate a coverage report.
        Optionally, save the results to a file

        To configure coverage, place a .coveragerc configuration file in the root directory
        of the repository - the same directory that holds .coverage. Documentation of coverage
        configuration is in https://coverage.readthedocs.io/en/coverage-4.2/config.html

        Args:
            test_path (:obj:`str`, optional): path to tests that should be run            
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            environment (:obj:`str`, optional): environment to run tests (local, docker, or circleci-local-executor)
            exit_on_failure (:obj:`bool`, optional): whether or not to exit on test failure

        Raises:
            :obj:`BuildHelperError`: If the environment is not supported or the package directory not set
        """
        if environment == 'local':
            self._run_tests_local(test_path=test_path, with_xunit=with_xunit,
                                  with_coverage=with_coverage, coverage_dirname=coverage_dirname,
                                  exit_on_failure=exit_on_failure)
        elif environment == 'docker':
            self._run_tests_docker(test_path=test_path, with_xunit=with_xunit,
                                   with_coverage=with_coverage, coverage_dirname=coverage_dirname,
                                   exit_on_failure=exit_on_failure)
        elif environment == 'circleci-local-executor':
            self._run_tests_circleci(test_path=test_path, with_xunit=with_xunit,
                                     with_coverage=with_coverage, coverage_dirname=coverage_dirname,
                                     exit_on_failure=exit_on_failure)
        else:
            raise BuildHelperError('Unsupported environment: {}'.format(environment))

    def _run_tests_local(self, test_path='tests', with_xunit=False, with_coverage=False, coverage_dirname='.',
                         exit_on_failure=True):
        """ Run unit tests located at `test_path` locally

        Optionally, generate a coverage report.
        Optionally, save the results to a file

        To configure coverage, place a .coveragerc configuration file in the root directory
        of the repository - the same directory that holds .coverage. Documentation of coverage
        configuration is in https://coverage.readthedocs.io/en/coverage-4.2/config.html

        Args:
            test_path (:obj:`str`, optional): path to tests that should be run            
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            exit_on_failure (:obj:`bool`, optional): whether or not to exit on test failure

        Raises:
            :obj:`BuildHelperError`: If the package directory not set
        """

        py_v = self.get_python_version()
        abs_xml_latest_filename = os.path.join(
            self.proj_tests_xml_dir, '{0}.{1}.xml'.format(self.proj_tests_xml_latest_filename, py_v))

        if with_coverage:
            cov = coverage(data_file=os.path.join(coverage_dirname, '.coverage'), data_suffix=py_v, config_file=True)
            cov.start()

        if with_xunit and not os.path.isdir(self.proj_tests_xml_dir):
            os.makedirs(self.proj_tests_xml_dir)

        if self.test_runner == 'pytest':
            test_path = test_path.replace(':', '::')
            test_path = re.sub('::(.+?)(\.)', r'::\1::', test_path)

            argv = [test_path]
            if with_xunit:
                argv.append('--junitxml=' + abs_xml_latest_filename)

            result = pytest.main(argv)
        elif self.test_runner == 'nose':
            test_path = test_path.replace('::', ':', 1)
            test_path = test_path.replace('::', '.', 1)

            argv = ['nosetests', test_path]
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

    def _run_tests_docker(self, test_path='tests', with_xunit=False, with_coverage=False, coverage_dirname='.',
                          exit_on_failure=True):
        """ Run unit tests located at `test_path` using a Docker image

        Optionally, generate a coverage report.
        Optionally, save the results to a file

        To configure coverage, place a .coveragerc configuration file in the root directory
        of the repository - the same directory that holds .coverage. Documentation of coverage
        configuration is in https://coverage.readthedocs.io/en/coverage-4.2/config.html

        Args:
            test_path (:obj:`str`, optional): path to tests that should be run            
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            exit_on_failure (:obj:`bool`, optional): whether or not to exit on test failure

        Raises:
            :obj:`BuildHelperError`: If the package directory not set
        """
        # create container
        process = subprocess.Popen(['docker', 'run', '-it', '-d', '--name', 'build', self.build_image, 'bash'],
                                   stdout=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(0.5)
        if process.returncode and process.returncode != 0:
            raise Exception(process.communicate()[1])

        # copy GitHub ssh key to container
        process = subprocess.Popen(['docker', 'cp', os.path.expanduser(os.path.join('~', '.ssh', 'id_rsa')), 'build:/root/.ssh/'],
                                   stdout=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(0.5)
        if process.returncode and process.returncode != 0:
            raise Exception(process.communicate()[1])

        # copy scripts to container
        process = subprocess.Popen(['docker', 'cp', os.path.join(os.path.dirname(__file__), 'test_package.sh'), 'build:/root/'],
                                   stdout=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(0.5)
        if process.returncode and process.returncode != 0:
            raise Exception(process.communicate()[1])

        # copy package to container
        process = subprocess.Popen(['docker', 'cp', os.path.join(os.path.dirname(__file__), '..', '..', package), 'build:/root/'],
                                   stdout=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(0.5)
        if process.returncode and process.returncode != 0:
            raise Exception(process.communicate()[1])

        # test package in container
        process = subprocess.Popen(['docker', 'exec',
                                    '-e', 'CIRCLE_PROJECT_REPONAME=' + package,
                                    '-e', 'CIRCLE_PROJECT_USERNAME=KarrLab',
                                    'build',
                                    'bash', '-c', '/root/test_package.sh',
                                    ])
        while process.poll() is None:
            time.sleep(0.5)
        if process.returncode and process.returncode != 0:
            valid = False
        else:
            valid = True

        # stop and remove container
        process = subprocess.Popen(['docker', 'rm', '-f', 'build'],
                                   stdout=subprocess.PIPE)
        while process.poll() is None:
            time.sleep(0.5)
        if process.returncode and process.returncode != 0:
            raise Exception(process.communicate()[1])

        return valid

    def _run_tests_circleci(self, test_path='tests', with_xunit=False, with_coverage=False, coverage_dirname='.',
                            exit_on_failure=True):
        """ Run unit tests located at `test_path` using the CircleCI local executor

        Optionally, generate a coverage report.
        Optionally, save the results to a file

        To configure coverage, place a .coveragerc configuration file in the root directory
        of the repository - the same directory that holds .coverage. Documentation of coverage
        configuration is in https://coverage.readthedocs.io/en/coverage-4.2/config.html

        Args:
            test_path (:obj:`str`, optional): path to tests that should be run            
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            coverage_dirname (:obj:`str`, optional): directory to save coverage data
            exit_on_failure (:obj:`bool`, optional): whether or not to exit on test failure

        Raises:
            :obj:`BuildHelperError`: If the package directory not set
        """
        package_dir = os.path.join(os.path.dirname(__file__), '..', '..', package)

        # remove __pycache__ files
        for path in glob.glob(os.path.join(package_dir, '**', '__pycache__'), recursive=True):
            shutil.rmtree(path)

        # update CircleCI to use build image with SSH key
        with open(os.path.join(package_dir, '.circleci', 'config.yml'), 'r') as file:
            config = yaml.load(file)

        if len(config['jobs']['build']['docker']) != 1:
            raise Exception('Only one docker build is supported at this time')

        image_name = config['jobs']['build']['docker'][0]['image']
        image_with_ssh_key_name = image_name + '.with_ssh_key'

        shutil.copyfile(os.path.join(package_dir, '.circleci', 'config.yml'), os.path.join(package_dir, '.circleci', 'config.yml.user'))
        config['jobs']['build']['docker'][0]['image'] = image_with_ssh_key_name
        with open(os.path.join(package_dir, '.circleci', 'config.yml'), 'w') as file:
            yaml.dump(config, file)

        # test package
        process = subprocess.Popen(['circleci', 'build',
                                    '-e', 'TEST_SERVER_TOKEN=' + TEST_SERVER_TOKEN,
                                    ], cwd=package_dir)
        while process.poll() is None:
            time.sleep(0.5)

        # undo changes to CircleCI config
        shutil.move(os.path.join(package_dir, '.circleci', 'config.yml.user'), os.path.join(package_dir, '.circleci', 'config.yml'))

        # return
        if process.returncode != 0 and process.communicate()[1] is not None:
            return False
        return True

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

        if self.test_server_token is None or \
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

        coverage_doc = coverage(data_file=os.path.join(coverage_dirname, '.coverage'))
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
                workman = coverage(data_file=os.path.join(coverage_dirname, '.coverage'))
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

        parser = ConfigParser()
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


class BuildHelperError(Exception):
    """ Represents :obj:`BuildHelper` errors """
    pass
