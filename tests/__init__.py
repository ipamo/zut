from __future__ import annotations
import os
from pathlib import Path
from configparser import ConfigParser
from zut import configure_logging, register_locale, configure_smb_credentials, files

configure_logging(level=os.environ.get('LOG_LEVEL', 'WARNING'), manage_exit=False)
register_locale('fr_FR.UTF-8')

CONFIG = ConfigParser()
CONFIG.read(['data/tests.conf'])

SAMPLES_DIR = Path(__file__).parent.joinpath("samples")
RESULTS_DIR = Path('data', 'tests-results')
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

SMB_USER = CONFIG.get('zut-tests', 'smb_user', fallback=None)
SMB_PASSWORD = CONFIG.get('zut-tests', 'smb_password', fallback=None)
if SMB_USER or SMB_PASSWORD:
    configure_smb_credentials(user=SMB_USER, password=SMB_PASSWORD)

SMB_RESULTS_DIR = CONFIG.get('zut-tests', 'smb_results_dir', fallback=None)
if SMB_RESULTS_DIR:
    if not files.can_use_network_paths():
        SMB_RESULTS_DIR = None
    else:
        files.makedirs(SMB_RESULTS_DIR, exist_ok=True)
