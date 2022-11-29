import os
from src.lib.adapters import secrets_adapter

SERVICE_NAME = os.environ.get('SERVICE_NAME')
STAGE = os.environ.get('STAGE')
SIMULATIONS_TABLE = f'{SERVICE_NAME}-{STAGE}-Simulations'
SIMULATIONS_RESULTS_TABLE = f'{SERVICE_NAME}-{STAGE}-SimulationsResults'
APP_SECRET_ARN = 'arn:aws:secretsmanager:us-east-1:396489703414:secret:rebound-ctrl-secret-6pFng0'

HOSTS = [
    'cassini.rc.unesp.br',
    'nelson1.rc.unesp.br',
    'ganimedes.rc.unesp.br',
    'hubble.rc.unesp.br',
]

SSH_KEYS = secrets_adapter.get_app_secrets(APP_SECRET_ARN)['ssh_keys']