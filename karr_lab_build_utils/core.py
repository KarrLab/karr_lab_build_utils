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
from ftputil import FTPHost
from glob import glob
from junit2htmlreport.parser import Junit as JunitParser
from nose2unitth.core import Converter as Nose2UnitthConverter
from sphinx import build_main as sphinx_build
from sphinx.apidoc import main as sphinx_apidoc
from unitth.core import UnitTH
import abduct
import git
import karr_lab_build_utils
import nose
import os
import pip
import pytest
import re
import shutil
import subprocess
import sys
import tempfile
import subprocess


class BuildHelper(object):
    """ Utility class to help build projects:

    * Run tests
    * Generate HTML test history reports
    * Generate HTML coverage reports
    * Generate HTML API documentation
    * Archive reports to lab server, Coveralls, and Code Climate

    Attributes:
        test_runner (:obj:`str`): name of test runner {pytest, nose}

        code_server_hostname (:obj:`str`): hostname of server where reports should be uploaded
        code_server_username (:obj:`str`): username for server where reports should be uploaded
        code_server_password (:obj:`str`): password for server where reports should be uploaded
        code_server_base_dir (:obj:`str`): base directory on server where reports should be uploaded

        project_name (:obj:`str`): name of project, e.g. GitHub repository name
        build_num (:obj:`int`): CircleCI build number        

        proj_tests_dir (:obj:`str`): local directory with test code
        proj_tests_xml_latest_filename (:obj:`str`): file name to store latest XML test report
        proj_tests_xml_dir (:obj:`str`): local directory where the test reports generated should be saved
        proj_tests_unitth_dir (:obj:`str`): local directory where UnitTH input should be saved
        proj_tests_html_dir (:obj:`str`): local directory where HTML test history report should be saved
        proj_cov_filename (:obj:`str`): file name where coverage report should be saved
        proj_cov_html_dir (:obj:`str`): local directory where HTML coverage report should be saved
        proj_docs_dir (:obj:`str`): local directory with Sphinx configuration
        proj_docs_static_dir (:obj:`str`): local directory of static documentation files
        proj_docs_source_dir (:obj:`str`): local directory of source documentation files created by sphinx-apidoc
        proj_docs_build_html_dir (:obj:`str`): local directory where generated HTML documentation should be saved

        serv_tests_xml_dir (:obj:`str`): server directory where the test reports generated should be saved
        serv_tests_unitth_dir (:obj:`str`): server directory where UnitTH input should be saved
        serv_tests_html_dir (:obj:`str`): server directory where HTML test history report should be saved
        serv_cov_html_dir (:obj:`str`): server directory where HTML coverage report should be saved
        
        artifacts_docs_build_html_dir (:obj:`str`): artifactrs subdirectory where generated HTML documentation should be saved

        coveralls_token (:obj:`str`): Coveralls token
        code_climate_token (:obj:`str`): Code Climate token

        build_artifacts_dir (:obj:`str`): directory which CircleCI will record with each build
        build_test_dir (:obj:`str`): directory where CircleCI will look for test results

        DEFAULT_TEST_RUNNER (:obj:`str`): default test runner {pytest, nose}
        DEFAULT_CODE_SERVER_HOSTNAME (:obj:`str`): default hostname of server where reports should be uploaded
        DEFAULT_CODE_SERVER_USERNAME (:obj:`str`): default username for server where reports should be uploaded
        DEFAULT_CODE_SERVER_BASE_DIR (:obj:`str`): default base directory on server where reports should be uploaded
        DEFAULT_PROJ_TESTS_DIR (:obj:`str`): default local directory with test code
        DEFAULT_PROJ_TESTS_XML_LATEST_FILENAME (:obj:`str`): default file name to store latest XML test report
        DEFAULT_PROJ_TESTS_XML_DIR (:obj:`str`): default local directory where the test reports generated should be saved
        DEFAULT_PROJ_TESTS_UNITTH_DIR (:obj:`str`): default local directory where UnitTH input should be saved
        DEFAULT_PROJ_TESTS_HTML_DIR (:obj:`str`): default local directory where HTML test history report should be saved
        DEFAULT_PROJ_COV_FILENAME (:obj:`str`): default coverage file name
        DEFAULT_PROJ_COV_HTML_DIR (:obj:`str`): default local directory where HTML coverage report should be saved
        DEFAULT_PROJ_DOCS_DIR (:obj:`str`): default local directory with Sphinx configuration
        DEFAULT_PROJ_DOCS_STATIC_DIR (:obj:`str`): default local directory of static documentation files
        DEFAULT_PROJ_DOCS_SOURCE_DIR (:obj:`str`): default local directory of source documentation files created by sphinx-apidoc
        DEFAULT_PROJ_DOCS_BUILD_HTML_DIR (:obj:`str`): default local directory where generated HTML documentation should be saved
        DEFAULT_SERV_TESTS_XML_DIR (:obj:`str`): default server directory where the test reports generated should be saved
        DEFAULT_SERV_TESTS_UNITTH_DIR (:obj:`str`): default server directory where UnitTH input should be saved
        DEFAULT_SERV_TESTS_HTML_DIR (:obj:`str`): default server directory where HTML test history report should be saved
        DEFAULT_SERV_COV_HTML_DIR (:obj:`str`): default server directory where HTML coverage report should be saved        
        DEFAULT_ARTIFACTS_DOCS_BUILD_HTML_DIR (:obj:`str`): default artifacts subdirectory where generated HTML documentation should be saved
    """

    DEFAULT_TEST_RUNNER = 'pytest'
    DEFAULT_CODE_SERVER_HOSTNAME = 'code.karrlab.org'
    DEFAULT_CODE_SERVER_USERNAME = 'karrlab_code'
    DEFAULT_CODE_SERVER_BASE_DIR = '/code.karrlab.org'
    DEFAULT_PROJ_TESTS_DIR = 'tests'
    DEFAULT_PROJ_TESTS_XML_LATEST_FILENAME = 'latest'
    DEFAULT_PROJ_TESTS_XML_DIR = 'tests/reports/xml'
    DEFAULT_PROJ_TESTS_UNITTH_DIR = 'tests/reports/unitth'
    DEFAULT_PROJ_TESTS_HTML_DIR = 'tests/reports/html'
    DEFAULT_PROJ_COV_FILENAME = '.coverage'
    DEFAULT_PROJ_COV_HTML_DIR = 'tests/reports/coverage'
    DEFAULT_PROJ_DOCS_DIR = 'docs'
    DEFAULT_PROJ_DOCS_STATIC_DIR = 'docs/_static'
    DEFAULT_PROJ_DOCS_SOURCE_DIR = 'docs/source'
    DEFAULT_PROJ_DOCS_BUILD_HTML_DIR = 'docs/_build/html'
    DEFAULT_SERV_TESTS_XML_DIR = 'tests/xml'
    DEFAULT_SERV_TESTS_UNITTH_DIR = 'tests/unitth'
    DEFAULT_SERV_TESTS_HTML_DIR = 'tests/html'
    DEFAULT_SERV_COV_HTML_DIR = 'tests/coverage'
    DEFAULT_ARTIFACTS_DOCS_BUILD_HTML_DIR = 'docs'

    def __init__(self):
        """ Construct build helper """

        # get settings from environment variables
        self.test_runner = os.getenv('TEST_RUNNER', self.DEFAULT_TEST_RUNNER)
        if self.test_runner not in ['pytest', 'nose']:
            raise Exception('Unsupported test runner {}'.format(self.test_runner))

        self.code_server_hostname = os.getenv('CODE_SERVER_HOSTNAME', self.DEFAULT_CODE_SERVER_HOSTNAME)
        self.code_server_username = os.getenv('CODE_SERVER_USERNAME', self.DEFAULT_CODE_SERVER_USERNAME)
        self.code_server_password = os.getenv('CODE_SERVER_PASSWORD')
        self.code_server_base_dir = os.getenv('CODE_SERVER_BASE_DIR', self.DEFAULT_CODE_SERVER_BASE_DIR)

        self.project_name = os.getenv('CIRCLE_PROJECT_REPONAME', '')
        if not self.project_name:
            try:
                repo = git.Repo('.')
                self.project_name, _ = os.path.splitext(os.path.basename(repo.remote().url))
            except git.exc.InvalidGitRepositoryError as err:
                pass
        self.build_num = int(float(os.getenv('CIRCLE_BUILD_NUM', 0)))

        self.proj_tests_dir = self.DEFAULT_PROJ_TESTS_DIR
        self.proj_tests_xml_latest_filename = self.DEFAULT_PROJ_TESTS_XML_LATEST_FILENAME
        self.proj_tests_xml_dir = self.DEFAULT_PROJ_TESTS_XML_DIR
        self.proj_tests_unitth_dir = self.DEFAULT_PROJ_TESTS_UNITTH_DIR
        self.proj_tests_html_dir = self.DEFAULT_PROJ_TESTS_HTML_DIR
        self.proj_cov_filename = self.DEFAULT_PROJ_COV_FILENAME
        self.proj_cov_html_dir = self.DEFAULT_PROJ_COV_HTML_DIR
        self.proj_docs_dir = self.DEFAULT_PROJ_DOCS_DIR
        self.proj_docs_static_dir = self.DEFAULT_PROJ_DOCS_STATIC_DIR
        self.proj_docs_source_dir = self.DEFAULT_PROJ_DOCS_SOURCE_DIR
        self.proj_docs_build_html_dir = self.DEFAULT_PROJ_DOCS_BUILD_HTML_DIR

        self.serv_tests_xml_dir = self.DEFAULT_SERV_TESTS_XML_DIR
        self.serv_tests_unitth_dir = self.DEFAULT_SERV_TESTS_UNITTH_DIR
        self.serv_tests_html_dir = self.DEFAULT_SERV_TESTS_HTML_DIR
        self.serv_cov_html_dir = self.DEFAULT_SERV_COV_HTML_DIR
        self.artifacts_docs_build_html_dir = self.DEFAULT_ARTIFACTS_DOCS_BUILD_HTML_DIR

        self.coveralls_token = os.getenv('COVERALLS_REPO_TOKEN')
        self.code_climate_token = os.getenv('CODECLIMATE_REPO_TOKEN')

        self.build_artifacts_dir = os.getenv('CIRCLE_ARTIFACTS')
        self.build_test_dir = os.getenv('CIRCLE_TEST_REPORTS')

    ########################
    # Installing dependencies
    ########################
    def install_requirements(self):
        """ Install requirements """

        # requirements for package
        self.install_requirements_pypi('requirements.txt')

        # requirements for testing and documentation
        subprocess.check_call(['sudo', 'apt-get', 'install', 'libffi-dev'])

        self.install_requirements_pypi(os.path.join(self.proj_tests_dir, 'requirements.txt'))
        self.install_requirements_pypi(os.path.join(self.proj_docs_dir, 'requirements.txt'))

    def install_requirements_pypi(self, req_file):
        if not os.path.isfile(req_file):
            return

        with abduct.captured(abduct.err()) as stderr:
            result = pip.main(['install', '-r', req_file])
            long_err_msg = stderr.getvalue()

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
    def run_tests(self, test_path='tests', with_xunit=False, with_coverage=False):
        """ Run unit tests located at `test_path`.
        Optionally, generate a coverage report.
        Optionally, save the results to `xml_file`.

        To configure coverage, place a .coveragerc configuration file in the root directory
        of the repository - the same directory that holds .coverage. Documentation of coverage
        configuration is in https://coverage.readthedocs.io/en/coverage-4.2/config.html

        Args:
            test_path (:obj:`str`, optional): path to tests that should be run
            with_coverage (:obj:`bool`, optional): whether or not coverage should be assessed
            xml_file (:obj:`str`, optional): path to save test results

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

        if with_xunit and self.build_test_dir:
            abs_xml_artifact_filename = os.path.join(self.build_test_dir, '{0}.{1}.xml'.format('xml', py_v))
            shutil.copyfile(abs_xml_latest_filename, abs_xml_artifact_filename)

        if result != 0:
            sys.exit(1)

    def make_and_archive_reports(self):
        """ Make and archive reports:

        * Generate HTML test history reports
        * Generate HTML coverage reports
        * Generate HTML API documentation
        * Archive coverage report to Coveralls and Code Climate
        * Archive HTML coverage report to lab sever
        """

        """ test reports """
        # create directory with test result history
        self.download_xml_test_report_history_from_lab_server()

        for file in glob(os.path.join(self.proj_tests_xml_dir, '{0}.{1}.xml'.format(self.proj_tests_xml_latest_filename, '*'))):
            shutil.copyfile(file, file.replace(self.proj_tests_xml_latest_filename, str(self.build_num)))

        # make report of test history
        self.make_test_history_report()

        # copy test history to lab server
        self.archive_test_reports()

        """ coverage """
        # Merge coverage reports
        # Generate HTML report
        # Copy coverage report to artifacts directory
        # Upload coverage report to Coveralls and Code Climate
        # Upload HTML coverage report to lab server
        self.combine_coverage_reports()
        self.make_html_coverage_report()
        self.archive_coverage_report()

        """ documentation """
        self.make_documentation()
        self.archive_documentation()

    ########################
    # Test reports
    ########################

    def download_xml_test_report_history_from_lab_server(self):
        """ Download XML test report history from lab server """

        if not os.path.isdir(self.proj_tests_xml_dir):
            os.makedirs(self.proj_tests_xml_dir)
        for report_filename in glob(os.path.join(self.proj_tests_xml_dir, "[0-9]*.*.xml")):
            os.remove(report_filename)

        with self.get_connection_to_lab_server() as ftp:
            self.download_dir_from_lab_server(ftp, self.serv_tests_xml_dir, self.proj_tests_xml_dir)

    def make_test_history_report(self):
        """ Make an HTML test history report from a directory of nose-style XML test reports """

        if not os.path.isdir(self.proj_tests_unitth_dir):
            os.makedirs(self.proj_tests_unitth_dir)

        # remove old UnitTH input
        for path in os.listdir(self.proj_tests_unitth_dir):
            full_path = os.path.join(self.proj_tests_unitth_dir, path)
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)

        # Make XML and HTML test reports that are readable UnitTH
        for build_file_path in glob(os.path.join(self.proj_tests_xml_dir, "[0-9]*.*.xml")):
            build_base_name = os.path.basename(build_file_path)
            build_num_py_v = os.path.splitext(build_base_name)[0]

            # Split nose-style XML report into UnitTH-style reports for each package
            if not os.path.isdir(os.path.join(self.proj_tests_unitth_dir, build_num_py_v)):
                os.makedirs(os.path.join(self.proj_tests_unitth_dir, build_num_py_v))

            Nose2UnitthConverter.run(build_file_path, os.path.join(self.proj_tests_unitth_dir, build_num_py_v))

            # Make HTML report from nose-style test XML report
            with open(os.path.join(os.path.join(self.proj_tests_unitth_dir, build_num_py_v, 'index.html')), 'wb') as html_file:
                html_file.write(JunitParser(build_file_path).html().encode('utf-8'))

        # Make HTML test history report
        if not os.path.isdir(self.proj_tests_html_dir):
            os.makedirs(self.proj_tests_html_dir)

        UnitTH.run(os.path.join(self.proj_tests_unitth_dir, '*'),
                   xml_report_filter='',
                   html_report_path='.',
                   generate_exec_time_graphs=True,
                   html_report_dir=self.proj_tests_html_dir)

    def archive_test_reports(self):
        """ Archive test report:

        * Upload XML and HTML test reports to lab server
        """

        self.upload_test_reports_to_lab_server()

    def upload_test_reports_to_lab_server(self):
        """ Upload XML and HTML test reports to lab server """

        with self.get_connection_to_lab_server() as ftp:
            if not ftp.path.isdir(self.serv_tests_xml_dir):
                ftp.makedirs(self.serv_tests_xml_dir)

            for name in glob(os.path.join(self.proj_tests_xml_dir, '{0:d}.{1:s}.xml'.format(self.build_num, '*'))):
                ftp.upload(name, self.serv_tests_xml_dir + name[len(self.proj_tests_xml_dir):])

            for name in glob(os.path.join(self.proj_tests_unitth_dir, '{0:d}.{1:s}'.format(self.build_num, '*'))):
                self.upload_dir_to_lab_server(ftp, name, self.serv_tests_unitth_dir +
                                              name[len(self.proj_tests_unitth_dir):])

            self.upload_dir_to_lab_server(ftp, self.proj_tests_html_dir, self.serv_tests_html_dir)

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

    def make_html_coverage_report(self):
        """ Make HTML coverage report from `proj_cov_filename` 
        """
        if not os.path.isdir(self.proj_cov_html_dir):
            os.makedirs(self.proj_cov_html_dir)
        map(os.remove, glob(os.path.join(self.proj_cov_html_dir, '*')))
        coverage_doc = coverage(data_file='.coverage', config_file=True)
        coverage_doc.load()
        coverage_doc.html_report(directory=self.proj_cov_html_dir)

    def archive_coverage_report(self):
        """ Archive coverage report:

        * Copy report to artifacts directory
        * Upload report to Coveralls and Code Climate
        * Upload HTML report to lab server
        """

        # copy to artifacts directory
        self.copy_coverage_report_to_artifacts_directory()

        # upload to Coveralls
        self.upload_coverage_report_to_coveralls()

        # upload to Code Climate
        self.upload_coverage_report_to_code_climate()

        # upload to lab server
        self.upload_html_coverage_report_to_lab_server()

    def copy_coverage_report_to_artifacts_directory(self):
        """ Copy coverage report to CircleCI artifacts directory """
        if self.build_artifacts_dir:
            for name in glob('.coverage.*'):
                shutil.copyfile(name, os.path.join(self.build_artifacts_dir, name))

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

    def upload_html_coverage_report_to_lab_server(self):
        """ Upload HTML coverage report to lab server """

        with self.get_connection_to_lab_server() as ftp:
            self.upload_dir_to_lab_server(ftp, self.proj_cov_html_dir, self.serv_cov_html_dir)

    ########################
    # Documentation
    ########################

    def make_documentation(self):
        """ Make HTML documentation using Sphinx for one or more packages. Save documentation to `proj_docs_build_html_dir` 

        Raises:
            :obj:`BuildHelperError`: If project name or code server password not set
        """

        # create `proj_docs_static_dir`, if necessary
        if not os.path.isdir(self.proj_docs_static_dir):
            os.mkdir(self.proj_docs_static_dir)

        # compile API documentation
        parser = ConfigParser()
        parser.read('setup.cfg')
        packages = parser.get('sphinx-apidocs', 'packages').strip().split('\n')
        for package in packages:
            sphinx_apidoc(argv=['sphinx-apidoc', '-f', '-o', self.proj_docs_source_dir, package])

        # build HTML documentation
        result = sphinx_build(['sphinx-build', self.proj_docs_dir, self.proj_docs_build_html_dir])
        if result != 0:
            sys.exit(result)

    def archive_documentation(self):
        """ Save documentation to artifacts directory """

        shutil.copytree(self.proj_docs_build_html_dir, os.path.join(self.build_artifacts_dir, self.artifacts_docs_build_html_dir))

    def get_version(self):
        return '{0:s} (Python {1[0]:d}.{1[1]:d}.{1[2]:d})'.format(karr_lab_build_utils.__version__, sys.version_info)

    def get_connection_to_lab_server(self):
        """ Connect to lab server

        Raises:
            :obj:`BuildHelperError`: If project name or code server password not set
        """

        if not self.project_name:
            raise BuildHelperError('Project name not set')

        if not self.code_server_password:
            raise BuildHelperError('Code server password must be set')

        ftp = FTPHost(self.code_server_hostname, self.code_server_username, self.code_server_password)
        if not ftp.path.isdir(ftp.path.join(self.code_server_base_dir, self.project_name)):
            ftp.makedirs(ftp.path.join(self.code_server_base_dir, self.project_name))
        ftp.chdir(ftp.path.join(self.code_server_base_dir, self.project_name))

        return ftp

    def upload_dir_to_lab_server(self, ftp, local_root_dir, remote_root_dir):
        """ Upload directory to lab server

        Args:
            ftp (:obj:`ftputil.FTPHost`): FTP connection
            local_root_dir (:obj:`str`): local directory to upload
            remote_root_dir (:obj:`str`): remote path to copy local directory to
        """
        for local_dir, _, local_files in os.walk(local_root_dir, onerror=self.walk_error):
            if local_dir == local_root_dir:
                rel_dir = '.'
            else:
                rel_dir = local_dir[len(local_root_dir) + 1:]

            if not ftp.path.isdir(ftp.path.join(remote_root_dir, rel_dir)):
                ftp.makedirs(ftp.path.join(remote_root_dir, rel_dir))
            for local_file in local_files:
                ftp.upload(os.path.join(local_root_dir, rel_dir, local_file),
                           ftp.path.join(remote_root_dir, rel_dir, local_file))

    def download_dir_from_lab_server(self, ftp, remote_root_dir, local_root_dir):
        """ Download directory from lab server

        Args:
            ftp (:obj:`ftputil.FTPHost`): FTP connection
            remote_root_dir (:obj:`str`): remote directory to download
            local_root_dir (:obj:`str`): local path to copy remote directory to
        """
        if not ftp.path.isdir(remote_root_dir):
            ftp.makedirs(remote_root_dir)

        for remote_dir, _, remote_files in ftp.walk(remote_root_dir, onerror=self.walk_error):
            if remote_dir == remote_root_dir:
                rel_dir = '.'
            else:
                rel_dir = remote_dir[len(remote_root_dir) + 1:]
            if not os.path.isdir(os.path.join(local_root_dir, rel_dir)):
                os.makedirs(os.path.join(local_root_dir, rel_dir))
            for remote_file in remote_files:
                ftp.download(ftp.path.join(remote_root_dir, rel_dir, str(remote_file)),
                             os.path.join(local_root_dir, rel_dir, remote_file))

    def walk_error(self, err):
        """ Throw error during os or ftp walk

        Args:
            err: Error in os or ftp walk

        Raises:
            :obj:`BuildHelperError`
        """
        raise BuildHelperError(err)

    @staticmethod
    def get_python_version():
        return '{0[0]:d}.{0[1]:d}.{0[2]:d}'.format(sys.version_info)


class BuildHelperError(Exception):
    """ Represents :obj:`BuildHelper` errors """
    pass
