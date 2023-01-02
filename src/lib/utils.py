from src.lib.adapters import secrets_adapter
from src.constants import APP_SECRET_ARN

app_secrets = None

def get_app_secrets():
    global app_secrets
    if(app_secrets is None):
        app_secrets = secrets_adapter.get_secret(APP_SECRET_ARN)
    return app_secrets

def get_ssh_keys():
    return get_app_secrets()['ssh_keys']