# AWS S3の自動タグ付けアプリケーション

ここでは、AWS LambdaとChatGPTを使用して、S3にアップロードされたファイルに自動でタグを付与するシステムを構築します。

ChatGPIで、ファイルの内容を解析し、適切なタグを生成してます。
解析できるファイルの種類は、 html, markdown, pdf, txt です。
それ以外の拡張子のファイルは対応していません。

## Terraform実行に必要な事前作業

## 前提作業
- terraformのCLIがインストール済みであること
- AWSのIAMとそのアクセスキーを作成していること
- OpenAPIのAPIの取得していること

terraformのvalues.yamlにAPI KEYなどの必要な情報を追記します。

```
variable "access_key" {
  default     = "IAMで作成したアクセスキー"
}

variable "secret_key" {
  default     = "IAMで作成したシークレットキー"
}

variable "openai_api_key" {
  default     = "OPENAIのAPI KEY"
}

variable "upload_bucket" {
  default     = "アップロード用S3バケット名"
}
```

## 導入手順

```
# 初期化
terraform init
# 構築内容確認
terraform plan
# 構築
terraform apply
```

* 削除する場合
```
# 削除
terraform destroy
```

## python ディレクトリの作成方法

AWS Lamdbaで実行するPythonのライブラリの追加が必要な場合は、以下を参考に追加してください。

* pythonフォルダにpipでpythonのモジュールをダウンロードして配置

作成例)
```
pip install openai --no-user -t python/
pip install markdown --no-user -t python/
pip install PyPDF2 --no-user -t python/
pip install beautifulsoup4 --no-user -t python/
pip install urllib3==1.26.7 --no-user -t python/
```

## ローカルでコードのデバックをする際

LOCAL_DEBUGを有効にすることで、ローカルでもコードを実行できます。
```
export OPENAI_API_KEY="<ChatGPTで使用するOpenAPIのApiKey>"
export UPLOAD_BUKET="<S3の保存先のバケット名>"
export LOCAL_DEBUG="True"
```

* 実行方法
```
python3 python/lambda_function.py
```

# S3アップロード スクリプト

* s3_upload_file.py を利用してローカルのファイルをS3にアップロードできます

オプション説明:
* bucket-name: uploadするS3バケット名
* local-file-path: uploadするローカルのファイル
* s3-object-key: S3バケットに配置する際のパス

実行例)
```
# python3 s3_upload_file.py --bucket-name=${UPLOAD_BUKET} --local-file-path='sample.md' --s3-object-key='test/sample.md'
sample.md を [yourbuckt]/test/sample.md にアップロードしました。
```

※ aws cliで同様の処理が可能
```
# aws s3 cp sample.md s3://${UPLOAD_BUKET}/test/sample.md
upload: .\sample.md to s3://${UPLOAD_BUKET}/test/sample.md
```

# タグの確認方法

aws cliでS3のオブジェクトに、タグが付与されているか確認する事ができます。
```
aws s3api get-object-tagging --bucket ${UPLOAD_BUKET} --key test/sample.md
```