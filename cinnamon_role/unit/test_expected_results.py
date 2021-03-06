# Copyright (c) 2016 Ryan Rossiter
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
from tempest import exceptions

from cinnamon_role import expected_results
from cinnamon_role.unit import base


class TestExpectedResultsProvider(base.BaseTestCase):
    @mock.patch('cinnamon_role.expected_results.open')
    @mock.patch('yaml.safe_load')
    def test_read_expected_results_yaml(self, mock_load, mock_open):
        mock_file = mock.MagicMock(spec=file)
        mock_results = mock.Mock()
        mock_open.return_value = mock_file
        mock_load.return_value = mock_results
        path = 'foo/bar.yaml'

        er = expected_results.read_expected_results_yaml(path)

        mock_open.assert_called_once_with(path, 'r')
        read_file = mock_file.__enter__.return_value
        mock_load.assert_called_once_with(read_file)
        self.assertEqual(mock_results, er)

    @mock.patch('cinnamon_role.expected_results.open')
    def test_read_expected_results_yaml_no_file(self, mock_open):
        mock_open.side_effect = IOError

        self.assertRaises(exceptions.InvalidConfiguration,
                          expected_results.read_expected_results_yaml,
                          'foo')

    @mock.patch.object(expected_results, 'read_expected_results_yaml')
    def test_get_result(self, mock_read):
        results = {'test.foo.test_foobar': {'pass': ['user1'],
                                            'fail': ['user2']}}
        mock_read.return_value = results

        erp = expected_results.ExpectedResultsProvider('foo.yaml')
        success_result = erp.get_result('test.foo.test_foobar', 'user1')
        fail_result = erp.get_result('test.foo.test_foobar', 'user2')

        self.assertTrue(success_result.is_expected_pass())
        self.assertTrue(fail_result.is_expected_fail())

    @mock.patch.object(expected_results, 'read_expected_results_yaml')
    def test_get_result_no_test_listed(self, mock_read):
        # No tests means there is no tests that came back from expected
        # results. Because it isn't found, it is unlisted
        results = {}
        mock_read.return_value = results

        erp = expected_results.ExpectedResultsProvider('foo.yaml')
        success_result = erp.get_result('test.foo.test_foobar', 'user1')

        self.assertTrue(success_result.is_unlisted())

    @mock.patch.object(expected_results, 'read_expected_results_yaml')
    def test_get_result_no_user_listed(self, mock_read):
        # Test an unlisted user. If the user is not present, it is an
        # unlisted test
        results = {'test.foo.test_foobar': {'pass': ['user1']}}
        mock_read.return_value = results

        erp = expected_results.ExpectedResultsProvider('foo.yaml')
        success_result = erp.get_result('test.foo.test_foobar', 'not_user')

        self.assertTrue(success_result.is_unlisted())


class TestExpectedResults(base.BaseTestCase):
    def setUp(self):
        super(TestExpectedResults, self).setUp()
        self.rs = expected_results.ResultState

    def test_expected_fail(self):
        state = self.rs(self.rs.FAIL)
        er = expected_results.ExpectedResult(state)
        self.assertFalse(er.is_expected_pass())
        self.assertTrue(er.is_expected_fail())
        self.assertFalse(er.is_unlisted())

    def test_expected_pass(self):
        state = self.rs(self.rs.PASS)
        er = expected_results.ExpectedResult(state)
        self.assertTrue(er.is_expected_pass())
        self.assertFalse(er.is_expected_fail())
        self.assertFalse(er.is_unlisted())

    def test_unlisted(self):
        state = self.rs(self.rs.UNLISTED)
        er = expected_results.ExpectedResult(state)
        self.assertFalse(er.is_expected_pass())
        self.assertFalse(er.is_expected_fail())
        self.assertTrue(er.is_unlisted())
