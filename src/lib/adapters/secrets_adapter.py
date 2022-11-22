import boto3
import json
import base64

def get_secret(secret_name, region_name='us-east-1'):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    secret_response = client.get_secret_value(SecretId=secret_name)

    # Decrypts secret using the associated KMS CMK.
    # Depending on whether the secret is a string or binary, one of these fields will be populated.
    if 'SecretString' in secret_response:
        secret = secret_response['SecretString']
        return secret
    else:
        decoded_binary_secret = base64.b64decode(secret_response['SecretBinary'])
        return decoded_binary_secret


def get_app_secrets(secret_arn):
    secret_str = get_secret(secret_arn)
    secret_obj = json.loads(secret_str)
    return secret_obj
