from __future__ import annotations
from unittest import TestCase, skipIf
from zut import slugify, slugify_django, slugify_snake, skip_utf8_bom
from . import SAMPLES_DIR

try:
    from django.utils.text import slugify as slugify_django_actual
except ImportError:
    slugify_django_actual = None

SLUGIFY_DJANGO_SAMPLES = {
    "Hello world":                  "hello-world",
    "  \"Privilège\" : élevé!-:) ": "privilege-eleve",
    "--__ _-ADMIN_-_SYS_#_":        "admin_-_sys",  # not "admin-sys"
    "Pas d'problème":               "pas-dprobleme",  # not "pas-d-probleme"
    "L ' horloge":                  "l-horloge",
    "Main (detail)":                "main-detail",
    "__-__":                        "",
    "---":                          "",
    "-":                            "",
    "#":                            "",
    "":                             "",
    None:                           "none",  # not None
}

SLUGIFY_SAMPLES = {
    **SLUGIFY_DJANGO_SAMPLES,
    "--__ _-ADMIN_-_SYS_#_":        "admin-sys",
    None:                           None,
}

class Case(TestCase):
    def test_slugify(self):
        for text, expected in SLUGIFY_SAMPLES.items():
            actual = slugify(text)
            self.assertEqual(actual, expected, "slugify(%s)" % text)


    def test_slugify_django(self):
        for text, expected in SLUGIFY_DJANGO_SAMPLES.items():
            actual = slugify_django(text)
            self.assertEqual(actual, expected, "slugify_django(%s)" % text)


    @skipIf(not slugify_django_actual, "django not available")
    def test_slugify_django_actual(self):
        for text, expected in SLUGIFY_DJANGO_SAMPLES.items():
            actual = slugify_django_actual(text)
            self.assertEqual(actual, expected or expected, "slugify_django_actual(%s)" % text)
            

    def test_slugify_snake(self):
        self.assertEqual(slugify_snake("CamelCase"), "camel_case")
        self.assertEqual(slugify_snake("CamèlCa-se"), "camel_ca_se")
        self.assertEqual(slugify_snake("ColumnId"), "column_id")
        self.assertEqual(slugify_snake("ColumnID"), "column_id")
        self.assertEqual(slugify_snake('camel2_camel2_case'), "camel2_camel2_case")
        self.assertEqual(slugify_snake('getHTTPResponseCode'), "get_http_response_code")
        self.assertEqual(slugify_snake('HTTPResponseCodeXYZ'), "http_response_code_xyz")


    def test_slugify_with_params(self):
        self.assertEqual(slugify('VirtualMachine'), 'virtualmachine')
        self.assertEqual(slugify('_ Vir_tual- Mach ine_', keep='_'), 'vir_tual-mach-ine')
        self.assertEqual(slugify('_ Vir_tual-* Mach ine_*', separator=None, keep='*'), 'virtual*machine')
        self.assertEqual(slugify('_ Vir_tual-* Mach ine_*', separator=None, keep='*', strip_keep=False), 'virtual*machine*')
        self.assertEqual(slugify('_ Vir_tual-* Mach ine_*', separator=None, keep=None), 'virtualmachine')


    def test_empty_file(self):
        with open(SAMPLES_DIR.joinpath('empty_file.txt'), encoding='utf-8') as fp:
            self.assertEqual(fp.read(), "")
        

    def test_skip_bom(self):
        # Without skip_bom
        with open(SAMPLES_DIR.joinpath('utf8_bom.csv'), encoding='utf-8') as fp:
            self.assertEqual(fp.read()[0], '\ufeff')

        # With skip_bom
        with open(SAMPLES_DIR.joinpath('utf8_bom.csv'), encoding='utf-8') as fp:
            skip_utf8_bom(fp)
            self.assertEqual(fp.read()[0], 'i')

        # Without skip_bom (binary)
        with open(SAMPLES_DIR.joinpath('utf8_bom.csv'), 'rb') as fp:
            self.assertEqual(fp.read()[0:3], '\ufeff'.encode('utf-8'))

        # With skip_bom (binary)
        with open(SAMPLES_DIR.joinpath('utf8_bom.csv'), 'rb') as fp:
            skip_utf8_bom(fp)
            self.assertEqual(fp.read()[0:1], 'i'.encode('utf-8'))
        
        # Empty file
        with open(SAMPLES_DIR.joinpath('empty_file.txt'), encoding='utf-8') as fp:
            skip_utf8_bom(fp)
            self.assertEqual(fp.read(), "")
