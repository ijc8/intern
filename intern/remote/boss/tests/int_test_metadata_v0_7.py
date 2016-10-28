﻿# Copyright 2016 The Johns Hopkins University Applied Physics Laboratory
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import six
from intern.remote.boss import BossRemote
from intern.resource.boss.resource import *
from intern.service.boss.httperrorlist import HTTPErrorList

import random
import requests
from requests import Session, HTTPError
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import unittest

API_VER = 'v0.7'

class MetadataServiceTest_v0_7(unittest.TestCase):
    """Integration tests of the Boss metadata API.

    Because setup and teardown involves many REST calls, tests are only
    divided into tests of the different types of data model resources.  All
    operations are performed within a single test of each resource.
    """

    @classmethod
    def setUpClass(cls):
        """Do an initial DB clean up in case something went wrong the last time.

        If a test failed really badly, the DB might be in a bad state despite
        attempts to clean up during tearDown().
        """
        cls.initialize()
        cls.cleanup_db()
        cls.rmt.project_create(cls.coll)
        coord_actual = cls.rmt.project_create(cls.coord)
        cls.rmt.project_create(cls.exp)
        chan_actual = cls.rmt.project_create(cls.chan)

    @classmethod
    def tearDownClass(cls):
        """Remove all data model objects created in the DB.
        """
        cls.cleanup_db()

    @classmethod
    def initialize(cls):
        """Initialization for each test.

        Called by both setUp() and setUpClass().
        """
        cls.rmt = BossRemote('test.cfg', API_VER)

        # Turn off SSL cert verification.  This is necessary for interacting with
        # developer instances of the Boss.
        cls.rmt.project_service.session_send_opts = { 'verify': False }
        cls.rmt.metadata_service.session_send_opts = { 'verify': False }
        cls.rmt.volume_service.session_send_opts = { 'verify': False }
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        coll_name = 'coll2309_{}'.format(random.randint(0, 9999))
        cls.coll = CollectionResource(coll_name, 'bar')

        cf_name = 'MetaFrame{}'.format(random.randint(0, 9999))
        cls.coord = CoordinateFrameResource(
            cf_name, 'Test coordinate frame.', 0, 10, -5, 5, 3, 6,
            1, 1, 1, 'nanometers', 1, 'nanoseconds')

        cls.exp = ExperimentResource(
            'myMetaExp2309', cls.coll.name, cls.coord.name, 'my experiment',
            1, 'iso', 0)

        cls.chan = ChannelResource(
            'myTestMetaChan', cls.coll.name, cls.exp.name, 'image', 'test channel',
            0, 'uint8', 0)

    @classmethod
    def cleanup_db(cls):
        """Clean up the data model objects used by this test case.

        This method is used by both tearDownClass() and setUpClass().
        """
        try:
            cls.rmt.project_delete(cls.chan)
        except HTTPError:
            pass
        try:
            cls.rmt.project_delete(cls.exp)
        except HTTPError:
            pass
        try:
            cls.rmt.project_delete(cls.coord)
        except HTTPError:
            pass
        try:
            cls.rmt.project_delete(cls.coll)
        except HTTPError:
            pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_collection(self):
        actual_list = self.rmt.metadata_list(self.coll)
        self.assertEqual([], actual_list)

        keys_vals = {'red': 'green', 'two': 'four', 'inside': 'out'}
        self.rmt.metadata_create(self.coll, keys_vals)

        actual = self.rmt.metadata_get(self.coll, list(keys_vals.keys()))
        six.assertCountEqual(self,keys_vals, actual)

        with self.assertRaises(HTTPErrorList):
            # Should fail when trying create keys that already exist.
            self.rmt.metadata_create(self.coll, keys_vals)

        update = {'two': 'six', 'inside': 'upside-down'}
        self.rmt.metadata_update(self.coll, update)

        actual_upd = self.rmt.metadata_get(self.coll, list(update.keys()))
        six.assertCountEqual(self, update, actual_upd)

        actual_list_upd = self.rmt.metadata_list(self.coll)
        six.assertCountEqual(self, list(keys_vals.keys()), actual_list_upd)

        with self.assertRaises(HTTPErrorList):
            # Try updating a non-existent key.
            self.rmt.metadata_update(self.coll, {'foo': 'bar'})

        self.rmt.metadata_delete(self.coll, list(keys_vals.keys()))

        with self.assertRaises(HTTPErrorList):
            # Try getting keys that don't exist.
            self.rmt.metadata_get(self.coll, ['foo', 'bar'])

        actual_list_end = self.rmt.metadata_list(self.coll)
        self.assertEqual([], actual_list_end)

    def test_experiment(self):
        actual_list = self.rmt.metadata_list(self.exp)
        self.assertEqual([], actual_list)

        keys_vals = {'red': 'green', 'two': 'four', 'inside': 'out'}
        self.rmt.metadata_create(self.exp, keys_vals)
        actual = self.rmt.metadata_get(self.exp, list(keys_vals.keys()))
        six.assertCountEqual(self, keys_vals, actual)

        with self.assertRaises(HTTPErrorList):
            # Should fail when trying create keys that already exist.
            self.rmt.metadata_create(self.exp, keys_vals)

        update = { 'two': 'six', 'inside': 'upside-down' }
        self.rmt.metadata_update(self.exp, update)

        actual_upd = self.rmt.metadata_get(self.exp, list(update.keys()))
        six.assertCountEqual(self, update, actual_upd)

        actual_list_upd = self.rmt.metadata_list(self.exp)
        six.assertCountEqual(self, list(keys_vals.keys()), actual_list_upd)

        with self.assertRaises(HTTPErrorList):
            # Try updating a non-existent key.
            self.rmt.metadata_update(self.exp, {'foo': 'bar'})

        self.rmt.metadata_delete(self.exp, list(keys_vals.keys()))

        with self.assertRaises(HTTPErrorList):
            # Try getting keys that don't exist.
            self.rmt.metadata_get(self.exp, ['foo', 'bar'])

        actual_list_end = self.rmt.metadata_list(self.exp)
        self.assertEqual([], actual_list_end)

    def test_channel(self):
        actual_list = self.rmt.metadata_list(self.chan)
        self.assertEqual([], actual_list)

        keys_vals = { 'red': 'green', 'two': 'four', 'inside': 'out'}
        self.rmt.metadata_create(self.chan, keys_vals)
        actual = self.rmt.metadata_get(self.chan, list(keys_vals.keys()))
        six.assertCountEqual(self, keys_vals, actual)

        with self.assertRaises(HTTPErrorList):
            # Should fail when trying create keys that already exist.
            self.rmt.metadata_create(self.chan, keys_vals)

        update = { 'two': 'six', 'inside': 'upside-down' }
        self.rmt.metadata_update(self.chan, update)

        actual_upd = self.rmt.metadata_get(self.chan, list(update.keys()))
        six.assertCountEqual(self,update, actual_upd)

        actual_list_upd = self.rmt.metadata_list(self.chan)
        six.assertCountEqual(self,keys_vals, actual_list_upd)

        with self.assertRaises(HTTPErrorList):
            # Try updating a non-existent key.
            self.rmt.metadata_update(self.chan, {'foo': 'bar'})

        self.rmt.metadata_delete(self.chan, list(keys_vals.keys()))

        with self.assertRaises(HTTPErrorList):
            # Try getting keys that don't exist.
            self.rmt.metadata_get(self.chan, ['foo', 'bar'])

        actual_list_end = self.rmt.metadata_list(self.chan)
        self.assertEqual([], actual_list_end)


if __name__ == '__main__':
    unittest.main()