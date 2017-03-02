#!/usr/bin/env python3
#
# Copyright 2016 Casey Marshall
# Copyright 2017 Ghent University
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
#
import json
import psycopg2
from urllib.parse import urlparse

if __name__ == '__main__':
    with open('/opt/mattermost/config/config.json', 'r') as f:
        conf = json.load(f)
        urlstr = conf.get('SqlSettings', {}).get('DataSource')
        if not urlstr:
            raise Exception('database not configured')
        url = urlparse(urlstr)
        if not url.scheme.startswith('postgres'):
            raise Exception('unsupported database: %s', url.scheme)
        connstr = 'dbname=%s user=%s password=%s host=%s port=%s' % (
            url.path.lstrip('/'), url.username, url.password,
            url.hostname, url.port)
        with psycopg2.connect(connstr) as c:
            with c.cursor() as cur:
                cur.execute('SELECT COUNT(1) FROM sessions')
                row, = cur.fetchone()
                print(row)
