# Pythonモジュールとスクリプトを格納したディレクトリをzipファイル化
data "archive_file" "lambda_function_payload" {
  type        = "zip"
  source_dir  = "python"
  output_path = "lambda_function_payload.zip"
}

# IAMロールの作成
resource "aws_iam_role" "lambda_role" {
  name = "lambda_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

# IAMロールにS3へのフルアクセスポリシーをアタッチ
resource "aws_iam_role_policy_attachment" "s3_full_access" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# アップロード用S3バケットの作成
resource "aws_s3_bucket" "upload_bucket" {
  bucket = "${var.upload_bucket}"
}

# パブリックアクセスをすべて許可
resource "aws_s3_bucket_public_access_block" "upload_bucket-private" {
  bucket                  = aws_s3_bucket.upload_bucket.id
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Lambda関数の作成
resource "aws_lambda_function" "content_generator" {
  function_name    = "content_generator"
  filename         = "lambda_function_payload.zip"
  source_code_hash = filebase64sha256("lambda_function_payload.zip")
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.10"
  timeout          = 60

  environment {
    variables = {
      OPENAI_API_KEY = "${var.openai_api_key}"
      UPLOAD_BUKET = "${var.upload_bucket}"
    }
  }
}

# アップロード用S3バケットにファイルがアップロードされたときにLambda関数をトリガーする設定
resource "aws_s3_bucket_notification" "bucket_notification" {
  bucket = aws_s3_bucket.upload_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.content_generator.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.content_generator.arn
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.upload_bucket.arn
}