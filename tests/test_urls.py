from __future__ import annotations
from unittest import TestCase
from urllib.parse import urlparse, unquote
from zut import build_url, hide_url_password

class Case(TestCase):
    def test_build_url(self):
        self.assertEqual('http://us%40er:***@localhost/sub/path', build_url(scheme='http', hostname='localhost', username='us@er', password='password', path='sub/path', hide_password=True))
        self.assertEqual('//user:***@localhost', build_url(hostname='localhost', username='user', password='password', hide_password=True))
        self.assertEqual('myscheme:', build_url(scheme='myscheme'))
        self.assertEqual('myscheme:sub/path', build_url(scheme='myscheme', path='sub/path'))
        self.assertEqual('myscheme:/sub/path', build_url(scheme='myscheme', path='/sub/path'))

        # ipv6 and password quote
        expected_url = 'pg://postgres:myp%40ss%3Aword@[::1]:5432'
        r = urlparse(expected_url)
        self.assertEqual('pg', r.scheme)
        self.assertEqual('postgres', r.username)
        self.assertEqual('myp@ss:word', unquote(r.password))  # urlparse does not unquote by default...
        self.assertEqual('::1', r.hostname)
        self.assertEqual(5432, r.port)
        self.assertEqual(expected_url, build_url(scheme='pg', username='postgres', password='myp@ss:word', hostname='::1', port=5432))


    def test_hide_url_password(self):
        self.assertEqual('pg://postgres:***@localhost/dbname', hide_url_password('pg://postgres:password@localhost/dbname'))
