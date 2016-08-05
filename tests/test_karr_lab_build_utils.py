""" Tests karr_lab_build_utils.

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2017-08-03
:Copyright: 2016, Karr Lab
:License: MIT
"""

from glob import glob
from karr_lab_build_utils.core import BuildHelper
import iocapture
import shutil
import subprocess
import os
import pysftp
import sys
import tempfile
import unittest

if sys.version_info >= (3, 0, 0):
    from test.support import EnvironmentVarGuard
else:
    from test.test_support import EnvironmentVarGuard

class TestKarrLabBuildUtils(unittest.TestCase):
    TEST_API = True
    TEST_CLI = False
    PROJECT_NAME = 'Karr-Lab-build-utils'
    COVERALLS_REPO_TOKEN = ''

    @classmethod
    def setUpClass(cls):
        env = EnvironmentVarGuard()
        env.set('CIRCLE_PROJECT_REPONAME', TestKarrLabBuildUtils.PROJECT_NAME)
        env.set('CIRCLE_BUILD_NUM', '0')
        env.set('CIRCLE_ARTIFACTS', tempfile.mkdtemp())
        env.set('CIRCLE_TEST_REPORTS', tempfile.mkdtemp())
        env.set('COVERALLS_REPO_TOKEN', TestKarrLabBuildUtils.COVERALLS_REPO_TOKEN)
        if not os.getenv('CIRCLECI'):
            with open('tests/fixtures/CODE_SERVER_PASSWORD', 'r') as file:
                env.set('CODE_SERVER_PASSWORD', file.read())

        with env:
            buildHelper = BuildHelper()

        cls._buildHelper = buildHelper

    @classmethod
    def tearDownClass(cls):
        buildHelper = cls._buildHelper
        sftp = buildHelper.connect_to_lab_server()

        with iocapture.capture() as captured:
            with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                if sftp.isfile(os.path.join(buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num)):
                    sftp.remove(os.path.join(buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num))

                dir_name = os.path.join(buildHelper.serv_tests_unitth_dir, '%d' % buildHelper.build_num)
                if sftp.isdir(dir_name):
                    sftp.walktree(dir_name, sftp.remove, sftp.rmdir, sftp.remove)
                    sftp.rmdir(dir_name)

        cls._buildHelper.disconnect_from_lab_server()

    def setUp(self):
        env = EnvironmentVarGuard()
        env.set('CIRCLE_PROJECT_REPONAME', self._buildHelper.project_name)
        env.set('CIRCLE_BUILD_NUM', '%d' % self._buildHelper.build_num)
        env.set('CIRCLE_ARTIFACTS', self._buildHelper.build_artifacts_dir)
        env.set('CIRCLE_TEST_REPORTS', self._buildHelper.build_test_dir)
        env.set('COVERALLS_REPO_TOKEN', self._buildHelper.coveralls_token)
        env.set('CODE_SERVER_PASSWORD', self._buildHelper.code_server_password)

        self._env = env

    def test_setup_machine(self):
        buildHelper = self._buildHelper

        if self.TEST_API:
            buildHelper.setup_machine()

        if self.TEST_CLI:
            self.call_cli('setup_machine')

    def test_install_requirements(self):
        buildHelper = self._buildHelper

        if self.TEST_API:
            buildHelper.install_requirements()

        if self.TEST_CLI:
            self.call_cli('install_requirements')

    def test_run_tests(self):
        buildHelper = self._buildHelper

        if self.TEST_API:
            if os.path.isfile(os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename)):
                os.remove(os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename))
            if os.path.isfile(buildHelper.proj_cov_filename):
                os.remove(buildHelper.proj_cov_filename)

            buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                                  with_xml_report=True, with_coverage=True)

            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_tests_nose_dir,
                                                        '%s.xml' % buildHelper.proj_tests_nose_latest_filename)))
            self.assertTrue(os.path.isfile(buildHelper.proj_cov_filename))

        if self.TEST_CLI:
            if os.path.isfile(os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename)):
                os.remove(os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename))
            if os.path.isfile(buildHelper.proj_cov_filename):
                os.remove(buildHelper.proj_cov_filename)

            self.call_cli('run_tests', [
                '--test_path', 'tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                '--with_xml_report',
                '--with_coverage',
            ])

            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_tests_nose_dir,
                                                        '%s.xml' % buildHelper.proj_tests_nose_latest_filename)))
            self.assertTrue(os.path.isfile(buildHelper.proj_cov_filename))

    def test_make_and_archive_reports(self):
        buildHelper = self._buildHelper
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xml_report=True, with_coverage=True)

        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename),
            os.path.join(buildHelper.proj_tests_nose_dir, '10000000000000001.xml')
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename),
            os.path.join(buildHelper.proj_tests_nose_dir, '10000000000000002.xml')
        )

        if self.TEST_API:
            buildHelper.make_and_archive_reports()

        if self.TEST_CLI:
            self.call_cli('make_and_archive_reports')

    @unittest.skip('Redundant with test_make_and_archive_reports')
    def test_download_nose_test_report_history_from_lab_server(self):
        buildHelper = self._buildHelper

        if self.TEST_API:
            buildHelper.download_nose_test_report_history_from_lab_server()

        if self.TEST_CLI:
            self.call_cli('download_nose_test_report_history_from_lab_server')

    @unittest.skip('Redundant with test_make_and_archive_reports')
    def test_make_test_history_report(self):
        buildHelper = self._buildHelper
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xml_report=True, with_coverage=True)

        for report_filename in glob(os.path.join(buildHelper.proj_tests_nose_dir, "[0-9]*.xml")):
            os.remove(report_filename)
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename),
            os.path.join(buildHelper.proj_tests_nose_dir, '10000000000000001.xml')
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename),
            os.path.join(buildHelper.proj_tests_nose_dir, '10000000000000002.xml')
        )

        if self.TEST_API:
            if os.path.isdir(buildHelper.proj_tests_unitth_dir):
                shutil.rmtree(buildHelper.proj_tests_unitth_dir)
            if os.path.isdir(buildHelper.proj_tests_html_dir):
                shutil.rmtree(buildHelper.proj_tests_html_dir)

            buildHelper.make_test_history_report()

            self.assertTrue(os.path.isfile(os.path.join(
                buildHelper.proj_tests_unitth_dir, '10000000000000001', 'index.html')))
            self.assertTrue(os.path.isfile(os.path.join(
                buildHelper.proj_tests_unitth_dir, '10000000000000002', 'index.html')))
            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_tests_html_dir, 'index.html')))

        if self.TEST_CLI:
            if os.path.isdir(buildHelper.proj_tests_unitth_dir):
                shutil.rmtree(buildHelper.proj_tests_unitth_dir)
            if os.path.isdir(buildHelper.proj_tests_html_dir):
                shutil.rmtree(buildHelper.proj_tests_html_dir)

            self.call_cli('make_test_history_report')

            self.assertTrue(os.path.isfile(os.path.join(
                buildHelper.proj_tests_unitth_dir, '10000000000000001', 'index.html')))
            self.assertTrue(os.path.isfile(os.path.join(
                buildHelper.proj_tests_unitth_dir, '10000000000000002', 'index.html')))
            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_tests_html_dir, 'index.html')))

    @unittest.skip('Redundant with test_make_and_archive_reports')
    def test_archive_test_reports(self):
        buildHelper = self._buildHelper
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xml_report=True, with_coverage=True)

        for report_filename in glob(os.path.join(buildHelper.proj_tests_nose_dir, "[0-9]*.xml")):
            os.remove(report_filename)
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename),
            os.path.join(buildHelper.proj_tests_nose_dir, "%d.xml" % buildHelper.build_num)
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename),
            os.path.join(buildHelper.proj_tests_nose_dir, '10000000000000001.xml')
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename),
            os.path.join(buildHelper.proj_tests_nose_dir, '10000000000000002.xml')
        )
        buildHelper.make_test_history_report()

        sftp = buildHelper.connect_to_lab_server()

        if self.TEST_API:
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num)):
                        sftp.remove(os.path.join(buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num))

                    if sftp.isfile(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html'))
                    if sftp.isfile(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html'))

                    if sftp.isfile(os.path.join(buildHelper.serv_tests_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_tests_html_dir, 'index.html'))

            buildHelper.archive_test_reports()

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(
                        buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num)))
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_tests_unitth_dir, '%d' %
                                                             buildHelper.build_num, 'index.html')))
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_tests_html_dir, 'index.html')))

        if self.TEST_CLI:
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num)):
                        sftp.remove(os.path.join(buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num))

                    if sftp.isfile(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html'))
                    if sftp.isfile(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html'))

                    if sftp.isfile(os.path.join(buildHelper.serv_tests_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_tests_html_dir, 'index.html'))

            self.call_cli('archive_test_reports')

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(
                        buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num)))
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_tests_unitth_dir, '%d' %
                                                             buildHelper.build_num, 'index.html')))
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_tests_html_dir, 'index.html')))

    @unittest.skip('Redundant with test_archive_test_reports')
    def test_upload_test_reports_to_lab_server(self):
        buildHelper = self._buildHelper
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xml_report=True, with_coverage=True)

        for report_filename in glob(os.path.join(buildHelper.proj_tests_nose_dir, "[0-9]*.xml")):
            os.remove(report_filename)
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename),
            os.path.join(buildHelper.proj_tests_nose_dir, "%d.xml" % buildHelper.build_num)
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename),
            os.path.join(buildHelper.proj_tests_nose_dir, '10000000000000001.xml')
        )
        shutil.copyfile(
            os.path.join(buildHelper.proj_tests_nose_dir, '%s.xml' % buildHelper.proj_tests_nose_latest_filename),
            os.path.join(buildHelper.proj_tests_nose_dir, '10000000000000002.xml')
        )
        buildHelper.make_test_history_report()

        sftp = buildHelper.connect_to_lab_server()

        if self.TEST_API:
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num)):
                        sftp.remove(os.path.join(buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num))

                    if sftp.isfile(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html'))
                    if sftp.isfile(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html'))

                    if sftp.isfile(os.path.join(buildHelper.serv_tests_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_tests_html_dir, 'index.html'))

            buildHelper.upload_test_reports_to_lab_server()

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(
                        buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num)))
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_tests_unitth_dir, '%d' %
                                                             buildHelper.build_num, 'index.html')))
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_tests_html_dir, 'index.html')))

        if self.TEST_CLI:
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num)):
                        sftp.remove(os.path.join(buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num))

                    if sftp.isfile(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html'))
                    if sftp.isfile(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_tests_unitth_dir, '10000000000000001', 'index.html'))

                    if sftp.isfile(os.path.join(buildHelper.serv_tests_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_tests_html_dir, 'index.html'))

            self.call_cli('upload_test_reports_to_lab_server')

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(
                        buildHelper.serv_tests_nose_dir, '%d.xml' % buildHelper.build_num)))
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_tests_unitth_dir, '%d' %
                                                             buildHelper.build_num, 'index.html')))
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_tests_html_dir, 'index.html')))

    def test_make_html_coverage_report(self):
        buildHelper = self._buildHelper
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xml_report=True, with_coverage=True)

        if self.TEST_API:
            if os.path.isdir(buildHelper.proj_cov_html_dir):
                shutil.rmtree(buildHelper.proj_cov_html_dir)

            buildHelper.make_html_coverage_report()

            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_cov_html_dir, 'index.html')))

        if self.TEST_CLI:
            if os.path.isdir(buildHelper.proj_cov_html_dir):
                shutil.rmtree(buildHelper.proj_cov_html_dir)

            self.call_cli('make_html_coverage_report')

            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_cov_html_dir, 'index.html')))

    @unittest.skip('Redundant with test_make_and_archive_reports')
    def test_archive_coverage_report(self):
        buildHelper = self._buildHelper
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xml_report=True, with_coverage=True)

        buildHelper.make_html_coverage_report()
        sftp = buildHelper.connect_to_lab_server()

        abs_cov_filename = os.path.join(buildHelper.build_artifacts_dir, buildHelper.proj_cov_filename)

        if self.TEST_API:
            if os.path.isfile(abs_cov_filename):
                os.remove(abs_cov_filename)

            buildHelper.archive_coverage_report()

            self.assertTrue(os.path.isfile(abs_cov_filename))

        if self.TEST_CLI:
            if os.path.isfile(abs_cov_filename):
                os.remove(abs_cov_filename)

            self.call_cli('archive_coverage_report')

            self.assertTrue(os.path.isfile(abs_cov_filename))

    @unittest.skip("Redundant with test_archive_coverage_report")
    def test_copy_coverage_report_to_artifacts_directory(self):
        buildHelper = self._buildHelper
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xml_report=True, with_coverage=True)

        abs_cov_filename = os.path.join(buildHelper.build_artifacts_dir, buildHelper.proj_cov_filename)

        if self.TEST_API:
            if os.path.isfile(abs_cov_filename):
                os.remove(abs_cov_filename)

            buildHelper.copy_coverage_report_to_artifacts_directory()

            self.assertTrue(os.path.isfile(abs_cov_filename))

        if self.TEST_CLI:
            if os.path.isfile(abs_cov_filename):
                os.remove(abs_cov_filename)

            self.call_cli('copy_coverage_report_to_artifacts_directory')

            self.assertTrue(os.path.isfile(abs_cov_filename))

    def test_upload_coverage_report_to_coveralls(self):
        buildHelper = self._buildHelper
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xml_report=True, with_coverage=True)

        buildHelper.make_html_coverage_report()

        if self.TEST_API:
            buildHelper.upload_coverage_report_to_coveralls()

        if self.TEST_CLI:
            self.call_cli('upload_coverage_report_to_coveralls')

    @unittest.skip("Redundant with test_archive_coverage_report")
    def test_upload_html_coverage_report_to_lab_server(self):
        buildHelper = self._buildHelper
        buildHelper.run_tests(test_path='tests/test_karr_lab_build_utils.py:TestKarrLabBuildUtils.test_dummy_test',
                              with_xml_report=True, with_coverage=True)

        buildHelper.make_html_coverage_report()
        sftp = buildHelper.connect_to_lab_server()

        if self.TEST_API:
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_cov_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_cov_html_dir, 'index.html'))

            buildHelper.upload_html_coverage_report_to_lab_server()

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_cov_html_dir, 'index.html')))

        if self.TEST_CLI:
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_cov_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_cov_html_dir, 'index.html'))

            self.call_cli('upload_html_coverage_report_to_lab_server')

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_cov_html_dir, 'index.html')))

    @unittest.skip('Redundant with test_make_and_archive_reports')
    def test_make_documentation(self):
        buildHelper = self._buildHelper

        if self.TEST_API:
            if os.path.isdir(buildHelper.proj_docs_build_html_dir):
                shutil.rmtree(buildHelper.proj_docs_build_html_dir)

            buildHelper.make_documentation()

            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_docs_build_html_dir, 'index.html')))

        if self.TEST_CLI:
            if os.path.isdir(buildHelper.proj_docs_build_html_dir):
                shutil.rmtree(buildHelper.proj_docs_build_html_dir)

            self.call_cli('make_documentation')

            self.assertTrue(os.path.isfile(os.path.join(buildHelper.proj_docs_build_html_dir, 'index.html')))

    @unittest.skip('Redundant with test_make_and_archive_reports')
    def test_archive_documentation(self):
        """ setup """
        buildHelper = self._buildHelper
        buildHelper.make_documentation()

        sftp = buildHelper.connect_to_lab_server()

        if self.TEST_API:
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html'))

            buildHelper.archive_documentation()

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')))

        if self.TEST_CLI:
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html'))

            self.call_cli('archive_documentation')

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')))

    @unittest.skip("Redundant with test_archive_documentation")
    def test_upload_documentation_to_lab_server(self):
        """ setup """
        buildHelper = self._buildHelper
        buildHelper.make_documentation()

        sftp = buildHelper.connect_to_lab_server()

        if self.TEST_API:
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html'))

            buildHelper.upload_documentation_to_lab_server()

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')))

        if self.TEST_CLI:
            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    if sftp.isfile(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')):
                        sftp.remove(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html'))

            self.call_cli('upload_documentation_to_lab_server')

            with iocapture.capture() as captured:
                with sftp.cd(os.path.join(buildHelper.code_server_base_dir, buildHelper.project_name)):
                    self.assertTrue(sftp.isfile(os.path.join(buildHelper.serv_docs_build_html_dir, 'index.html')))

    def test_dummy_test(self):
        pass

    def call_cli(self, command, arguments=[]):
        with self._env:
            if self._buildHelper.machine_python_2:
                subprocess.check_call(['python2', 'karr_lab_build_utils/bin/%s.py' % command] + arguments)
            if self._buildHelper.machine_python_3:
                subprocess.check_call(['python3', 'karr_lab_build_utils/bin/%s.py' % command] + arguments)
