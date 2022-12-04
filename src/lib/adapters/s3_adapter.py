import io
import boto3
import json
from io import StringIO, BytesIO

s3_client = None

def get_client():
    global s3_client
    if(s3_client is None):
        s3_client = boto3.client('s3')
    return s3_client


def file_exists(bucket, path):
    try:
        get_client().head_object(Bucket=bucket, Key=path)
        return True
    except:
        return False


def save_to_s3(bucket, path, data):
    get_client().put_object(Key=path, Body=data, Bucket=bucket)


def read_json(bucket, path):
    obj = get_client().get_object(Bucket=bucket, Key=path)
    return json.loads(obj['Body'].read())


def save_df_to_s3(bucket, path, df, format='csv'):
    if format == 'csv':
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        data = buffer.getvalue()
        save_to_s3(bucket, path, data)
    elif format == 'xlsx':
        buffer = BytesIO()
        df.to_excel(buffer, index=False)
        data = buffer.getvalue()
        save_to_s3(bucket, path, data)
    else:
        raise Exception('Invalid format.')


def list_files(bucket, prefix):
    result = get_client().list_objects_v2(Bucket=bucket, Prefix=prefix)
    if 'Contents' not in result:
        return []
    return result['Contents']


def download_file(bucket, path):
    response = get_client().get_object(Bucket=bucket, Key=path)
    obj = response['Body'].read()
    return obj


def upload_file(bucket, path, file, content_type=None):
    file.seek(0)
    get_client().upload_fileobj(file, bucket, path, ExtraArgs={ 'ContentType': content_type })


def upload_excel(bucket, path, file):
    file.seek(0)
    get_client().upload_fileobj(
        file,
        bucket,
        path,
        ExtraArgs={
            'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        },
    )

def delete_file(bucket, path):
    get_client().delete_object(Bucket=bucket, Key=path)