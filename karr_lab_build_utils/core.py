""" Karr Lab build utilities

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2016-08-02
:Copyright: 2016, Karr Lab
:License: MIT
"""

from codeclimate_test_reporter.components.runner import Runner as CodeClimateRunner
from configparser import ConfigParser
from coverage import coverage
from coveralls import Coveralls
from glob import glob
from jinja2 import Template
from pkg_resources import resource_filename
from sphinx import build_main as sphinx_build
from sphinx.apidoc import main as sphinx_apidoc
import abduct
import karr_lab_build_utils
import nose
import os
import pip
import pytest
import requests
import re
import shutil
import subprocess
import sys
import tempfile


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
        proj_docs_build_html_dir (:obj:`str`): local directory where generated HTML documentation should be saved

        test_server_token (:obj:`str`): test history report server token
        coveralls_token (:obj:`str`): Coveralls token
        code_climate_token (:obj:`str`): Code Climate token

        github_api_token (obj:`str`): GitHub API token
        circle_api_token (:obj:`str`): CircleCI API token

        DEFAULT_TEST_RUNNER (:obj:`str`): default test runner {pytest, nose}
        DEFAULT_PROJ_TESTS_DIR (:obj:`str`): default local directory with test code
        DEFAULT_PROJ_TESTS_XML_DIR (:obj:`str`): default local directory where the test reports generated should be saved
        DEFAULT_PROJ_TESTS_XML_LATEST_FILENAME (:obj:`str`): default file name to store latest XML test report        
        DEFAULT_PROJ_DOCS_DIR (:obj:`str`): default local directory with Sphinx configuration
        DEFAULT_PROJ_DOCS_STATIC_DIR (:obj:`str`): default local directory of static documentation files
        DEFAULT_PROJ_DOCS_SOURCE_DIR (:obj:`str`): default local directory of source documentation files created by sphinx-apidoc
        DEFAULT_PROJ_DOCS_BUILD_HTML_DIR (:obj:`str`): default local directory where generated HTML documentation should be saved

        GITHUB_API_ENDPOINT (:obj:`str`): GitHub API endpoint
        CIRCLE_API_ENDPOINT (:obj:`str`): CircleCI API endpoint

        COVERALLS_ENABLED (:obj:`bool`): if :obj:`True`, upload coverage reports to coveralls
        CODE_CLIMATE_ENABLED (:obj:`bool`): if :obj:`True`, upload coverage reports to code climate
    """

    DEFAULT_TEST_RUNNER = 'pytest'
    DEFAULT_PROJ_TESTS_DIR = 'tests'
    DEFAULT_PROJ_TESTS_XML_DIR = 'tests/reports'
    DEFAULT_PROJ_TESTS_XML_LATEST_FILENAME = 'latest'
    DEFAULT_PROJ_DOCS_DIR = 'docs'
    DEFAULT_PROJ_DOCS_STATIC_DIR = 'docs/_static'
    DEFAULT_PROJ_DOCS_SOURCE_DIR = 'docs/source'
    DEFAULT_PROJ_DOCS_BUILD_HTML_DIR = 'docs/_build/html'

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
        self.proj_docs_build_html_dir = self.DEFAULT_PROJ_DOCS_BUILD_HTML_DIR

        self.test_server_token = os.getenv('TEST_SERVER_TOKEN')
        self.coveralls_token = os.getenv('COVERALLS_REPO_TOKEN')
        self.code_climate_token = os.getenv('CODECLIMATE_REPO_TOKEN')

        self.github_username = os.getenv('GITHUB_USERNAME')
        self.github_password = os.getenv('GITHUB_PASSWORD')
        self.circle_api_token = os.getenv('CIRCLE_API_TOKEN')

    ########################
    # Register repo on CircleCI
    ########################
    def create_circleci_build(self):
        """ Create CircleCI build for a repository 

        Raises:
            :obj:`ValueError`: if a CircleCI build wasn't created and didn't already exist
        """
        url = '{}/project/{}/{}/{}/follow?circle-token={}'.format(
            self.CIRCLE_API_ENDPOINT, self.repo_type, self.repo_owner, self.repo_name, self.circle_api_token)
        response = requests.post(url)
        response.raise_for_status()
        if not response.json()['following']:
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

    ########################
    # Installing dependencies
    ########################
    def install_requirements(self):
        """ Install requirements """

        # requirements for package
        self._install_requirements_helper('requirements.txt')

        # requirements for testing and documentation
        subprocess.check_call(['sudo', 'apt-get', 'install', 'libffi-dev'])

        self._install_requirements_helper(os.path.join(self.proj_tests_dir, 'requirements.txt'))
        self._install_requirements_helper(os.path.join(self.proj_docs_dir, 'requirements.txt'))

    def _install_requirements_helper(self, req_file, update=True):
        if not os.path.isfile(req_file):
            return

        with abduct.captured(abduct.err()) as stderr:
            if update:
                cmd = ['install', '-U', '-r', req_file]
            else:
                cmd = ['install', '-r', req_file]
            result = pip.main(cmd)
            long_err_msg = stderr.getvalue()

        if result:
            sep = 'During handling of the above exception, another exception occurred:\n\n'
            i_sep = long_err_msg.find(sep)
            short_err_msg = long_err_msg[i_sep + len(sep):]

            sys.stderr.write(short_err_msg)
            sys.stderr.flush()
            sys.exit(1)

        if not update:
            self._update_requirements_github(req_file)

    def _update_requirements_github(self, req_file):
        with open(req_file, 'r') as req_file_id:
            for req in filter(lambda req: 'git+https://github.com/KarrLab/' in req, req_file_id.readlines()):
                result = pip.main(['install', '-U', req])

                if result:
                    sep = 'During handling of the above exception, another exception occurred:\n\n'
                    i_sep = long_err_msg.find(sep)
                    short_err_msg = long_err_msg[i_sep + len(sep):]

                    sys.stderr.write(short_err_msg)
                    sys.stderr.flush()
                    sys.exit(1)

    ########################
    # Running tests
    ########################
    def run_tests(self, test_path='tests', with_xunit=False, with_coverage=False, exit_on_failure=True):
        """ Run unit tests located at `test_path`.
        Optionally, generate a coverage report.
        Optionally, save the results to a file

        To configure coverage, place a .coveragerc configuration file in the root directory
        of the repository - the same directory that holds .coverage. Documentation of coverage
        configuration is in https://coverage.readthedocs.io/en/coverage-4.2/config.html

        Args:
            test_path (:obj:`str`, optional): path to tests that should be run
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            with_xunit (:obj:`bool`, optional): whether or not to save test results
            exit_on_failure (:obj:`bool`, optional): whether or not to exit on test failure

        Raises:
            :obj:`BuildHelperError`: If package directory not set
        """

        py_v = self.get_python_version()
        abs_xml_latest_filename = os.path.join(
            self.proj_tests_xml_dir, '{0}.{1}.xml'.format(self.proj_tests_xml_latest_filename, py_v))

        if with_coverage:
            cov = coverage(data_file='.coverage', data_suffix=py_v, config_file=True)
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

            if nose.run(argv=argv):
                result = 0
            else:
                result = 1
        else:
            raise Exception('Unsupported test runner {}'.format(self.test_runner))

        if with_coverage:
            cov.stop()
            cov.save()

        if exit_on_failure and result != 0:
            sys.exit(1)

    def make_and_archive_reports(self):
        """ Make and archive reports:

        * Upload test report to history server
        * Upload coverage report to Coveralls and Code Climate
        """

        """ test reports """
        # Upload test report to history server
        self.archive_test_report()

        """ coverage """
        # Merge coverage reports
        # Generate HTML report
        # Upload coverage report to Coveralls and Code Climate
        self.combine_coverage_reports()
        self.archive_coverage_report()

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
        for abs_xml_latest_filename in glob(abs_xml_latest_filename_pattern):
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

            r_json = r.json()

            if not r_json['success']:
                raise BuildHelperError('Error uploading report to test history server: {}'.format(r_json['message']))

    ########################
    # Coverage reports
    ########################
    def combine_coverage_reports(self):
        data_paths = []
        for name in glob('.coverage.*'):
            data_path = tempfile.mktemp()
            shutil.copyfile(name, data_path)
            data_paths.append(data_path)

        coverage_doc = coverage()
        coverage_doc.combine(data_paths=data_paths)
        coverage_doc.save()

    def archive_coverage_report(self):
        """ Archive coverage report:

        * Upload report to Coveralls and Code Climate
        """

        # upload to Coveralls
        if self.COVERALLS_ENABLED:
            self.upload_coverage_report_to_coveralls()

        # upload to Code Climate
        if self.CODE_CLIMATE_ENABLED:
            self.upload_coverage_report_to_code_climate() # disabled becase

    def upload_coverage_report_to_coveralls(self):
        """ Upload coverage report to Coveralls """
        if self.coveralls_token:
            Coveralls(True, repo_token=self.coveralls_token,
                      service_name='circle-ci', service_job_id=self.build_num).wear()

    def upload_coverage_report_to_code_climate(self):
        """ Upload coverage report to Code Climate 

        Raises:
            :obj:`BuildHelperError`: If error uploading code coverage to Code Climate
        """
        if self.code_climate_token:
            result = CodeClimateRunner(['--token', self.code_climate_token, '--file', '.coverage']).run()
            if result != 0:
                raise BuildHelperError('Error uploading coverage report to Code Climate')

    ########################
    # Documentation
    ########################

    def generate_documentation_configuration(self):
        """ Generate Sphinx build configuration for a package

        Raises:
            :obj:`ValueError`: if no package or more than one package is specified
        """

        parser = ConfigParser()
        parser.read('setup.cfg')
        packages = parser.get('sphinx-apidocs', 'packages').strip().split('\n')
        if len(packages) != 1:
            raise ValueError('Sphinx configuration auto-generation only supports 1 package')

        if not os.path.isdir(self.proj_docs_dir):
            os.mkdir(self.proj_docs_dir)

        for package in packages:
            with open(resource_filename('karr_lab_build_utils', 'templates/docs.conf.py'), 'r') as file:
                template = Template(file.read())
            template.stream(package=package).dump(os.path.join(self.proj_docs_dir, 'conf.py'))

            with open(resource_filename('karr_lab_build_utils', 'templates/docs.index.rst'), 'r') as file:
                template = Template(file.read())
            title = "Welcome to {}'s documentation!".format(package)
            template.stream(title=title, title_underline='=' * len(title)).dump(os.path.join(self.proj_docs_dir, 'index.rst'))

    def make_documentation(self):
        """ Make HTML documentation using Sphinx for one or more packages. Save documentation to `proj_docs_build_html_dir` 

        Raises:
            :obj:`BuildHelperError`: If project name not set
        """

        # create `proj_docs_static_dir`, if necessary
        if not os.path.isdir(self.proj_docs_static_dir):
            os.mkdir(self.proj_docs_static_dir)

        # build HTML documentation
        result = sphinx_build(['sphinx-build', self.proj_docs_dir, self.proj_docs_build_html_dir])
        if result != 0:
            sys.exit(result)

    def get_version(self):
        return '{0:s} (Python {1[0]:d}.{1[1]:d}.{1[2]:d})'.format(karr_lab_build_utils.__version__, sys.version_info)

    @staticmethod
    def get_python_version():
        return '{0[0]:d}.{0[1]:d}.{0[2]:d}'.format(sys.version_info)


class BuildHelperError(Exception):
    """ Represents :obj:`BuildHelper` errors """
    pass
