""" Tests karr_lab_build_utils.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-03
:Copyright: 2016, Karr Lab
:License: MIT
"""

from karr_lab_build_utils.core import BuildHelper
from test.test_support import EnvironmentVarGuard
import iocapture
import shutil
import subprocess
import os
import pysftp
import tempfile
import unittest


class TestKarrLabBuildUtils(unittest.TestCase):

    def setUp(self):
        self._env = EnvironmentVarGuard()
        if not os.getenv('CIRCLECI'):
            self._env.set('CIRCLE_PROJECT_REPONAME', 'Karr-Lab-build-utils')
            self._env.set('CIRCLE_BUILD_NUM', '0')
            self._env.set('CIRCLE_ARTIFACTS', tempfile.mkdtemp())
            self._env.set('CIRCLE_TEST_REPORTS', tempfile.mkdtemp())
            self._env.set('CODE_SERVER_PASSWORD', 'WJ8pcgTv6vqYkrEK')
            self._env.set('COVERALLS_REPO_TOKEN', 'XGUOnjoc3dOrifqc9xUPx1k2nVNiZsqSQ')

    def test_install_requirements(self):
        with self._env:
            buildHelper = BuildHelper()
            buildHelper.install_requirements()

            subprocess.check_call(['python', 'karr_lab_build_utils/bin/install_requirements.py'])

    def test_run_tests(self):
        with self._env:
            buildHelper = BuildHelper()

            """ test API """
            if os.path.isfile(os.path.join(buildHelper.proj_tests_nose_dir, buildHelper.proj_tests_nose_latest_filename)):
                os.remove(os.path.join(buildHelper.proj_tests_nose_dir, buildHelper.proj_tests_nose_latest_filename))
            if os.path.isfile(buildHelper.proj_cov_filename):
                os.remove(buildHelper.proj_cov_filename)

            buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                                  with_xml_report=True, with_coverage=True)

            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_tests_nose_dir,
                                                        buildHelper.proj_tests_nose_latest_filename)))
            self.assertTrue(os.path.isfile(buildHelper.proj_cov_filename))

            """ test CLI """
            if os.path.isfile(os.path.join(buildHelper.proj_tests_nose_dir, buildHelper.proj_tests_nose_latest_filename)):
                os.remove(os.path.join(buildHelper.proj_tests_nose_dir, buildHelper.proj_tests_nose_latest_filename))
            if os.path.isfile(buildHelper.proj_cov_filename):
                os.remove(buildHelper.proj_cov_filename)

            subprocess.check_call(['python', 'karr_lab_build_utils/bin/run_tests.py',
                                   '--test_path', 'tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                                   '--with_xml_report',
                                   '--with_coverage',
                                   ])

            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_tests_nose_dir,
                                                        buildHelper.proj_tests_nose_latest_filename)))
            self.assertTrue(os.path.isfile(buildHelper.proj_cov_filename))

    @unittest.skip('Write me')
    def test_make_and_archive_reports(self):
        with self._env:
            pass

    @unittest.skip('Write me')
    def test_download_nose_test_report_history_from_lab_server(self):
        with self._env:
            pass

    @unittest.skip('Write me')
    def test_make_test_history_report(self):
        with self._env:
            pass

    @unittest.skip('Write me')
    def test_archive_test_reports(self):
        with self._env:
            pass

    @unittest.skip('Write me')
    def test_upload_test_reports_to_lab_server(self):
        with self._env:
            pass

    def test_make_html_coverage_report(self):
        with self._env:
            buildHelper = BuildHelper()
            buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                                  with_xml_report=True, with_coverage=True)

            """ test API """
            if os.path.isdir(buildHelper.proj_cov_html_dir):
                shutil.rmtree(buildHelper.proj_cov_html_dir)

            buildHelper.make_html_coverage_report()

            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_cov_html_dir, 'index.html')))

            """ test CLI """
            if os.path.isdir(buildHelper.proj_cov_html_dir):
                shutil.rmtree(buildHelper.proj_cov_html_dir)

            subprocess.check_call(['python', 'karr_lab_build_utils/bin/make_html_coverage_report.py'])

            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_cov_html_dir, 'index.html')))

    @unittest.skip('Write me')
    def test_archive_coverage_report(self):
        with self._env:
            buildHelper = BuildHelper()
            buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                                  with_xml_report=True, with_coverage=True)

            abs_cov_filename = os.path.join(buildHelper.build_artifacts_dir, buildHelper.proj_cov_filename)

            """ test API """
            if os.path.isfile(abs_cov_filename):
                os.remove(abs_cov_filename)

            buildHelper.archive_coverage_report()

            self.assertTrue(os.path.isfile(abs_cov_filename))

            """ test CLI """
            if os.path.isfile(abs_cov_filename):
                os.remove(abs_cov_filename)

            subprocess.check_call(['python', 'karr_lab_build_utils/bin/archive_coverage_report.py'])
            
            self.assertTrue(os.path.isfile(abs_cov_filename))

    def test_copy_coverage_report_to_artifacts_directory(self):
        with self._env:
            buildHelper = BuildHelper()
            buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                                  with_xml_report=True, with_coverage=True)

            abs_cov_filename = os.path.join(buildHelper.build_artifacts_dir, buildHelper.proj_cov_filename)

            """ test API """
            buildHelper.copy_coverage_report_to_artifacts_directory()

            """ test CLI """
            subprocess.check_call(['python', 'karr_lab_build_utils/bin/copy_coverage_report_to_artifacts_directory.py'])

    def test_upload_coverage_report_to_coveralls(self):
        with self._env:
            buildHelper = BuildHelper()
            buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                                  with_xml_report=True, with_coverage=True)

            buildHelper.make_html_coverage_report()

            """ test API """
            buildHelper.upload_coverage_report_to_coveralls()

            """ test CLI """
            subprocess.check_call(['python', 'karr_lab_build_utils/bin/upload_coverage_report_to_coveralls.py'])

    def test_upload_html_coverage_report_to_lab_server(self):
        with self._env:
            buildHelper = BuildHelper()
            buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                                  with_xml_report=True, with_coverage=True)

            buildHelper.make_html_coverage_report()

            with iocapture.capture() as captured:
                cnopts = pysftp.CnOpts()
                cnopts.hostkeys = None
                sftp = pysftp.Connection(buildHelper.code_server_hostname,
                                         username=buildHelper.code_server_username,
                                         password=buildHelper.code_server_password,
                                         cnopts=cnopts
                                         )

            """ test API """
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_cov_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_cov_html_dir, 'index.html'))

            buildHelper.upload_html_coverage_report_to_lab_server()

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_cov_html_dir, 'index.html')))

            """ test CLI """
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_cov_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_cov_html_dir, 'index.html'))

            subprocess.check_call(['python', 'karr_lab_build_utils/bin/upload_html_coverage_report_to_lab_server.py'])

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_cov_html_dir, 'index.html')))

            """ cleanup """
            sftp.close()

    def test_make_documentation(self):
        with self._env:
            buildHelper = BuildHelper()

            """ test API """
            if os.path.isdir(buildHelper.proj_docs_build_html_dir):
                shutil.rmtree(buildHelper.proj_docs_build_html_dir)

            buildHelper.make_documentation()

            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_docs_build_html_dir, 'index.html')))

            """ test CLI """
            if os.path.isdir(buildHelper.proj_docs_build_html_dir):
                shutil.rmtree(buildHelper.proj_docs_build_html_dir)

            subprocess.check_call(['python', 'karr_lab_build_utils/bin/make_documentation.py'])

            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_docs_build_html_dir, 'index.html')))

    def test_archive_documentation(self):
        with self._env:
            """ setup """
            buildHelper = BuildHelper()
            buildHelper.make_documentation()

            with iocapture.capture() as captured:
                cnopts = pysftp.CnOpts()
                cnopts.hostkeys = None
                sftp = pysftp.Connection(buildHelper.code_server_hostname,
                                         username=buildHelper.code_server_username,
                                         password=buildHelper.code_server_password,
                                         cnopts=cnopts
                                         )

                sftp.makedirs(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name))

            """ test API """        
            buildHelper.archive_documentation()

            """ test CLI """
            subprocess.check_call(['python', 'karr_lab_build_utils/bin/archive_documentation.py'])

            """ cleanup """
            with iocapture.capture() as captured:
                sftp.close()

    def test_upload_documentation_to_lab_server(self):
        with self._env:
            """ setup """
            buildHelper = BuildHelper()
            buildHelper.make_documentation()

            with iocapture.capture() as captured:
                cnopts = pysftp.CnOpts()
                cnopts.hostkeys = None
                sftp = pysftp.Connection(buildHelper.code_server_hostname,
                                         username=buildHelper.code_server_username,
                                         password=buildHelper.code_server_password,
                                         cnopts=cnopts
                                         )

                sftp.makedirs(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name))

            """ test API """
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html'))

            buildHelper.upload_documentation_to_lab_server()

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')))

            """ test CLI """
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html'))

            subprocess.check_call(['python', 'karr_lab_build_utils/bin/upload_documentation_to_lab_server.py'])

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')))

            """ cleanup """
            with iocapture.capture() as captured:
                sftp.close()

    def test_dummy_test(self):
        with self._env:
            pass
