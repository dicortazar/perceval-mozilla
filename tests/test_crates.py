#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2017 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, 51 Franklin Street, Fifth Floor, Boston, MA 02110-1335, USA.
#
# Authors:
#     Valerio Cosentino <valcos@bitergia.com>
#

import datetime
import httpretty
import json
import unittest

from perceval.backend import BackendCommandArgumentParser
from perceval.backends.mozilla.crates import (Crates,
                                              CratesClient,
                                              CratesCommand,
                                              CRATES_CATEGORY,
                                              SUMMARY_CATEGORY)

from perceval.utils import DEFAULT_DATETIME


CRATES_API_URL = "https://crates.io/api/v1/"


def read_file(filename, mode='r'):
    with open(filename, mode) as f:
        content = f.read()
    return content


def setup_http_server(empty=False):
    """Setup a mock HTTP server"""

    summary = read_file('data/crates/crates_summary')
    httpretty.register_uri(httpretty.GET,
                           CRATES_API_URL + "summary",
                           body=summary,
                           status=200)

    if empty:
        page_empty = read_file('data/crates/crates_page_empty')
        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates?sort=alphabetical&page=1',
                               body=page_empty,
                               status=200)
    else:
        page_1 = read_file('data/crates/crates_page_1')
        page_2 = read_file('data/crates/crates_page_2')

        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates?sort=alphabetical&page=2',
                               body=page_2,
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates?sort=alphabetical&page=1',
                               body=page_1,
                               status=200)

        crate_1 = read_file('data/crates/crate_example_1')
        crate_2 = read_file('data/crates/crate_example_2')
        crate_3 = read_file('data/crates/crate_example_3')
        crate_4 = read_file('data/crates/crate_example_4')

        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates/a',
                               body=crate_1,
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates/aabb2',
                               body=crate_2,
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates/aac',
                               body=crate_3,
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates/abc',
                               body=crate_4,
                               status=200)

        crate_user_1 = read_file('data/crates/crate_owner_user_1')
        crate_user_2 = read_file('data/crates/crate_owner_user_2')
        crate_user_3 = read_file('data/crates/crate_owner_user_3')
        crate_user_4 = read_file('data/crates/crate_owner_user_4')

        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates/a/owner_user',
                               body=crate_user_1,
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates/aabb2/owner_user',
                               body=crate_user_2,
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates/aac/owner_user',
                               body=crate_user_3,
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates/abc/owner_user',
                               body=crate_user_4,
                               status=200)

        crate_team_1 = read_file('data/crates/crate_owner_team_1')
        crate_team_2 = read_file('data/crates/crate_owner_team_2')
        crate_team_3 = read_file('data/crates/crate_owner_team_3')
        crate_team_4 = read_file('data/crates/crate_owner_team_4')

        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates/a/owner_team',
                               body=crate_team_1,
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates/aabb2/owner_team',
                               body=crate_team_2,
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates/aac/owner_team',
                               body=crate_team_3,
                               status=200)
        httpretty.register_uri(httpretty.GET,
                               CRATES_API_URL + 'crates/abc/owner_team',
                               body=crate_team_4,
                               status=200)


class TestCratesBackend(unittest.TestCase):
    """Crates.io backend tests"""

    def test_initialization(self):
        """Test whether attributes are initializated"""

        crates = Crates(tag='test')

        self.assertEqual(crates.origin, 'https://crates.io/')
        self.assertEqual(crates.tag, 'test')

        # When tag is empty or None it will be set to
        # the value in origin
        crates = Crates()
        self.assertEqual(crates.origin, 'https://crates.io/')
        self.assertEqual(crates.tag, 'https://crates.io/')

        crates = Crates(tag='')
        self.assertEqual(crates.origin, 'https://crates.io/')
        self.assertEqual(crates.tag, 'https://crates.io/')

    def test_has_caching(self):
        """Test if it returns True when has_caching is called"""

        self.assertEqual(Crates.has_caching(), False)

    def test_has_resuming(self):
        """Test if it returns True when has_resuming is called"""

        self.assertEqual(Crates.has_resuming(), False)

    @httpretty.activate
    def test_fetch_crates(self):
        """Test whether a list of crates is returned"""

        setup_http_server()

        backend = Crates()
        items = [items for items in backend.fetch()]

        self.assertEqual(len(items), 4)

        item = items[0]
        self.assertEqual(item['category'], CRATES_CATEGORY)
        self.assertEqual(len(item['data']['owner_team_data']['teams']), 0)
        self.assertEqual(len(item['data']['owner_user_data']['users']), 1)

        item = items[1]
        self.assertEqual(item['category'], CRATES_CATEGORY)
        self.assertEqual(len(item['data']['owner_team_data']['teams']), 1)
        self.assertEqual(len(item['data']['owner_user_data']['users']), 2)

        item = items[2]
        self.assertEqual(item['category'], CRATES_CATEGORY)
        self.assertEqual(len(item['data']['owner_team_data']['teams']), 1)
        self.assertEqual(len(item['data']['owner_user_data']['users']), 2)

        item = items[3]
        self.assertEqual(item['category'], CRATES_CATEGORY)
        self.assertEqual(len(item['data']['owner_team_data']['teams']), 1)
        self.assertEqual(len(item['data']['owner_user_data']['users']), 3)

    @httpretty.activate
    def test_fetch_summary(self):
        """Test whether a summary is returned"""

        setup_http_server()

        backend = Crates()
        items = [items for items in backend.fetch(category=SUMMARY_CATEGORY)]

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['category'], SUMMARY_CATEGORY)
        self.assertEqual(items[0]['data']['num_crates'], 10000)
        self.assertEqual(items[0]['data']['num_downloads'], 2000000000)

    @httpretty.activate
    def test_fetch_from_date(self):
        """Test when return from date"""

        setup_http_server()

        backend = Crates()
        from_date = datetime.datetime(2016, 1, 1)
        items = [items for items in backend.fetch(from_date=from_date)]

        self.assertEqual(len(items), 3)
        self.assertEqual(len(items[0]['data']['owner_team_data']['teams']), 1)
        self.assertEqual(len(items[0]['data']['owner_user_data']['users']), 2)
        self.assertEqual(len(items[1]['data']['owner_team_data']['teams']), 1)
        self.assertEqual(len(items[1]['data']['owner_user_data']['users']), 2)
        self.assertEqual(len(items[2]['data']['owner_team_data']['teams']), 1)
        self.assertEqual(len(items[2]['data']['owner_user_data']['users']), 3)

    @httpretty.activate
    def test_fetch_summary_from_date(self):
        """Test when return from date"""

        setup_http_server()

        backend = Crates()
        from_date = datetime.datetime(2016, 1, 1)
        items = [items for items in backend.fetch(category=SUMMARY_CATEGORY,
                                                  from_date=from_date)]

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['category'], SUMMARY_CATEGORY)
        self.assertEqual(items[0]['data']['num_crates'], 10000)
        self.assertEqual(items[0]['data']['num_downloads'], 2000000000)

    @httpretty.activate
    def test_fetch_empty(self):
        """Test when return empty"""

        setup_http_server(empty=True)

        backend = Crates()
        items = [items for items in backend.fetch()]

        self.assertEqual(len(items), 0)


class TestCratesClient(unittest.TestCase):
    """Crates API client tests"""

    @httpretty.activate
    def test_summary(self):
        """Test summary API call"""

        setup_http_server()

        client = CratesClient()
        summary = json.loads(client.summary())

        self.assertEqual(summary['num_crates'], 10000)
        self.assertEqual(summary['num_downloads'], 2000000000)

    @httpretty.activate
    def test_crates(self):
        """Test crates API call"""

        setup_http_server()

        client = CratesClient()
        crates = [crates for crates in client.crates()]
        self.assertEqual(len(crates), 2)

        # Check requests
        expected = {
            'sort': ['alphabetical'],
            'page': ['2']
        }

        self.assertDictEqual(httpretty.last_request().querystring, expected)

    @httpretty.activate
    def test_crate(self):
        """ Test crate API call """

        setup_http_server()

        client = CratesClient()
        crate = client.crate('a')

        self.assertNotEqual(crate, None)


class TestCratesCommand(unittest.TestCase):
    """CratesCommand unit tests"""

    def test_backend_class(self):
        """Test if the backend class is Launchpad"""

        self.assertIs(CratesCommand.BACKEND, Crates)

    def test_setup_cmd_parser(self):
        """Test if it parser object is correctly initialized"""

        parser = CratesCommand.setup_cmd_parser()
        self.assertIsInstance(parser, BackendCommandArgumentParser)

        args = ['--tag', 'test',
                '--from-date', '1970-01-01',
                '--category', 'summary',
                '--sleep-time', '600']

        parsed_args = parser.parse(*args)
        self.assertEqual(parsed_args.tag, 'test')
        self.assertEqual(parsed_args.from_date, DEFAULT_DATETIME)
        self.assertEqual(parsed_args.category, SUMMARY_CATEGORY)
        self.assertEqual(parsed_args.sleep_time, '600')


if __name__ == "__main__":
    unittest.main(warnings='ignore')
