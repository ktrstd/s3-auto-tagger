import boto3
import argparse

def upload_to_s3(bucket_name, local_file_path, s3_object_key):
    s3 = boto3.client('s3')
    
    try:
        # ファイルをS3にアップロード
        s3.upload_file(local_file_path, bucket_name, s3_object_key)
        print(f'{local_file_path} を {bucket_name}/{s3_object_key} にアップロードしました。')
    except FileNotFoundError:
        print(f'{local_file_path} が見つかりません。')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='ローカルファイルをS3にアップロードするスクリプト')
    parser.add_argument('--bucket-name', required=True, help='S3バケット名')
    parser.add_argument('--local-file-path', required=True, help='ローカルファイルのパス')
    parser.add_argument('--s3-object-key', required=True, help='S3オブジェクトキー')

    args = parser.parse_args()

    bucket_name = args.bucket_name
    local_file_path = args.local_file_path
    s3_object_key = args.s3_object_key

    upload_to_s3(bucket_name, local_file_path, s3_object_key)
