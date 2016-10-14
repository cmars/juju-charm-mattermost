#!/usr/bin/env python3

import json
import psycopg2
from urllib.parse import urlparse

if __name__ == '__main__':
    with open('/srv/mattermost/config/config.json', 'r') as f:
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
                cur.execute('SELECT COUNT(1) FROM users')
                row, = cur.fetchone()
                print(row)
