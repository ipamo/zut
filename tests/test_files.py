from __future__ import annotations
from unittest import TestCase, skipIf
from time import sleep
from zut import files
from tests import RESULTS_DIR, SMB_RESULTS_DIR

class Case(TestCase):
    def test_copy_local(self):
        self._do(
            func=files.copy,
            src=RESULTS_DIR.joinpath('test_copy_local-src.txt'),
            create_src=True,
            dst=RESULTS_DIR.joinpath('test_copy_local-dst.txt'),
        )


    @skipIf(not SMB_RESULTS_DIR, 'smb not configured')
    def test_copy_smb(self):
        # To SMB
        self._do(
            func=files.copy,
            src=RESULTS_DIR.joinpath('test_copy_smb-src.txt'),
            create_src=True,
            dst=SMB_RESULTS_DIR + '\\test_copy_smb-dst.txt',
        )

        # From SMB
        self._do(
            func=files.copy,
            src=SMB_RESULTS_DIR + '\\test_copy_smb-dst.txt',
            dst=RESULTS_DIR.joinpath('test_copy_smb-dst2.txt'),
        )

        # Within SMB
        self._do(
            func=files.copy,
            src=SMB_RESULTS_DIR + '\\test_copy_smb-dst.txt',
            dst=SMB_RESULTS_DIR + '\\test_copy_smb-dst2.txt',
        )

    
    def test_copy2_local(self):
        self._do(
            func=files.copy2,
            src=RESULTS_DIR.joinpath('test_copy2_local-src.txt'),
            create_src=True,
            dst=RESULTS_DIR.joinpath('test_copy2_local-dst.txt'),
            expect_same_mtime=True,
        )


    @skipIf(not SMB_RESULTS_DIR, 'smb not configured')
    def test_copy2_smb(self):
        # To SMB
        self._do(
            func=files.copy2,
            src=RESULTS_DIR.joinpath('test_copy2_smb-src.txt'),
            create_src=True,
            dst=SMB_RESULTS_DIR + '\\test_copy2_smb-dst.txt',
            expect_same_mtime=True,
        )

        # From SMB
        self._do(
            func=files.copy2,
            src=SMB_RESULTS_DIR + '\\test_copy2_smb-dst.txt',
            dst=RESULTS_DIR.joinpath('test_copy2_smb-dst2.txt'),
            expect_same_mtime=True,
        )

        # Within SMB
        self._do(
            func=files.copy2,
            src=SMB_RESULTS_DIR + '\\test_copy2_smb-dst.txt',
            dst=SMB_RESULTS_DIR + '\\test_copy2_smb-dst2.txt',
            expect_same_mtime=True,
        )

    
    def test_copyfile_local(self):
        self._do(
            func=files.copyfile,
            src=RESULTS_DIR.joinpath('test_copyfile_local-src.txt'),
            create_src=True,
            dst=RESULTS_DIR.joinpath('test_copyfile_local-dst.txt'),
        )


    @skipIf(not SMB_RESULTS_DIR, 'smb not configured')
    def test_copyfile_smb(self):
        # To SMB
        self._do(
            func=files.copyfile,
            src=RESULTS_DIR.joinpath('test_copyfile_smb-src.txt'),
            create_src=True,
            dst=SMB_RESULTS_DIR + '\\test_copyfile_smb-dst.txt',
        )

        # From SMB
        self._do(
            func=files.copyfile,
            src=SMB_RESULTS_DIR + '\\test_copyfile_smb-dst.txt',
            dst=RESULTS_DIR.joinpath('test_copyfile_smb-dst2.txt'),
        )

        # Within SMB
        self._do(
            func=files.copyfile,
            src=SMB_RESULTS_DIR + '\\test_copyfile_smb-dst.txt',
            dst=SMB_RESULTS_DIR + '\\test_copyfile_smb-dst2.txt',
        )


    def _do(self, src, dst, func, create_src=False, expect_same_mtime=False):
        text = 'Hello,\nWorld.\n'

        if create_src:
            if files.exists(src):
                files.remove(src)
            files.write_text(src, text, encoding='utf-8')

        stat_src = files.stat(src)

        if expect_same_mtime:
            sleep(0.100)
        
        if files.exists(dst):
            files.remove(dst)
            
        func(src, dst)

        stat_dst = files.stat(dst)


        self.assertTrue(files.exists(dst))
        self.assertEqual(text, files.read_text(dst))

        if expect_same_mtime:
            self.assertEqual(stat_dst.st_mtime, stat_src.st_mtime)
