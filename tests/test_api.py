""" 
:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2018-03-12
:Copyright: 2018, Karr Lab
:License: MIT
"""

import karr_lab_build_utils
import unittest


class ApiTestCase(unittest.TestCase):
    def test(self):
        self.assertIsInstance(karr_lab_build_utils.BuildHelper, type)
