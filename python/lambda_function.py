import os
import re
import openai
import urllib.parse
import boto3
import markdown
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from io import BytesIO

# OpenAIのAPIキーを設定
openai.api_key = os.getenv("OPENAI_API_KEY")
upload_buket = os.getenv("UPLOAD_BUKET")
# ローカルデバック用変数 Tureの場合、ローカルのファイルを読み込む
LOCAL_DEBUG = os.getenv("LOCAL_DEBUG", "False") == "True"

s3 = boto3.client('s3')

# ローカルのファイルを読み込む関数
def read_file(file_path):
    if file_path.endswith('.pdf'):
        with open(file_path, 'rb') as file:
            pdf = PdfReader(file)
            return " ".join(page.extract_text() for page in pdf.pages)
    elif file_path.endswith('.html'):
        with open(file_path, 'r', encoding="utf-8") as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')
            return str(soup.body)
    elif file_path.endswith('.md'):
        with open(file_path, 'r', encoding="utf-8") as file:
            md_text = file.read()
            return markdown.markdown(md_text)
    elif file_path.endswith('.txt'):
        with open(file_path, 'r', encoding="utf-8") as file:
            text = file.read()
            return text
    else:
        return None

# Lambda関数のメインコード
def lambda_handler(event, context):
    if LOCAL_DEBUG:
        # ファイルパスを取得
        key = event['file_path']
        # ファイルの拡張子を確認
        file_extension = os.path.splitext(key)[1]
        # html, markdown, pdf, txt以外の拡張子の場合は処理をスキップ
        if file_extension not in ['.html', '.pdf', '.md', '.txt']:
            return {
                'statusCode': 204,
                'NoContent': f"Unsupported file type {file_extension}"
            }

        # ファイルを読み込む
        file_object = open(key, 'rb')
        file_content = read_file(key)
    else:
        # アップロードされたファイルの情報を取得
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')

        # ファイルをダウンロード
        file_object = s3.get_object(Bucket=bucket, Key=key)
        # ファイルの拡張子を確認
        file_extension = os.path.splitext(key)[1]
        # html, markdown, pdf, txt以外の拡張子の場合は処理をスキップ
        if file_extension not in ['.html', '.pdf', '.md', '.txt']:
            return {
                'statusCode': 204,
                'body': f"Unsupported file type: {file_extension}"
            }
            
        if key.endswith('.pdf'):
            # PDFファイルの場合、テキストに変換
            pdf = PdfReader(BytesIO(file_object["Body"].read()))
            file_content = " ".join(page.extract_text() for page in pdf.pages)
        elif key.endswith('.html'):
            content = file_object["Body"].read().decode('utf-8')
            soup = BeautifulSoup(content, 'html.parser')
            file_content = str(soup.body)
        else:
            # テキストファイルの場合
            file_content = file_object["Body"].read().decode('utf-8')

    # プロンプト文: 出力は'[#tag1, #tag2]'の形式で返却してください。また、タグの値は英数字のみ(日本語は英語に直すこと）。以下の文章のタグをいくつか生成してください。: (ChatGPTの命令文については、考慮の余地あり。)
    prompt = "Output should be returned in the format '[#tag1, #tag2]'. However, only alphanumeric characters should be used (Japanese tags should be translated into English). Please generate several tags for the following sentence. :\n" + file_content[:5000]
    # CahtGPTでプロンプト文を実行
    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, temperature=0.2, max_tokens=200)
    tags = re.findall(r"#(\w+)", response.choices[0].text)

    # タグをS3のメタデータとして保存(最大10個まで設定可能。ここでは上位5個)
    tag_set = [{"Key": f"key{idx+1}", "Value": tag} for idx, tag in enumerate(tags[:5])]
    # タグの更新
    if LOCAL_DEBUG: # ローカル実行の場合
        print (f"set tags: {tag_set}")
    else:
        s3.put_object_tagging(Bucket=bucket, Key=key, Tagging={'TagSet': tag_set})

    return {
        'statusCode': 200,
        'upload file': f"{key}"
    }

# ローカルでデバッグするためのコード
if __name__ == "__main__":
    # ローカルのファイルで実行する場合は、LOCAL_DEBUG="True"に設定する
    event = {
        'file_path': 'sample.md',  # テストするローカルのファイルパスを指定します
    }
    context = {}
    print(lambda_handler(event, context))
