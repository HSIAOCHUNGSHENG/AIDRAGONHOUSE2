import os
import uuid
import boto3
from botocore.exceptions import NoCredentialsError
from werkzeug.utils import secure_filename

class S3Uploader:
    def __init__(self, app=None):
        self.s3_client = None
        self.bucket_name = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化 S3 上傳器與 Flask 應用集成"""
        aws_access_key = app.config.get('AWS_ACCESS_KEY_ID')
        aws_secret_key = app.config.get('AWS_SECRET_ACCESS_KEY')
        aws_region = app.config.get('AWS_REGION', 'ap-northeast-1')  # 默認使用東京區域
        self.bucket_name = app.config.get('AWS_BUCKET_NAME')
        
        if aws_access_key and aws_secret_key and self.bucket_name:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name=aws_region
            )
        else:
            app.logger.warning("AWS S3 憑證未完全設置，無法初始化 S3 上傳功能！")
    
    def upload_file(self, file, folder='uploads'):
        """
        將文件上傳至 S3 存儲桶
        
        Args:
            file: 要上傳的文件對象（通常來自 request.files）
            folder: S3 存儲桶中的子目錄（默認為 'uploads'）
            
        Returns:
            str: 上傳後文件的公共 URL 或 None（如果上傳失敗）
        """
        if self.s3_client is None:
            return None
        
        if file.filename == '':
            return None
            
        # 確保文件名安全且唯一
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        s3_path = f"{folder}/{unique_filename}"
        
        try:
            # 上傳文件到 S3
            self.s3_client.upload_fileobj(
                file,
                self.bucket_name,
                s3_path,
                ExtraArgs={'ACL': 'public-read'}  # 使文件公開可訪問
            )
            
            # 構建 S3 文件的公共 URL
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_path}"
            return url
        except NoCredentialsError:
            print("憑證錯誤：無法訪問 S3")
            return None
        except Exception as e:
            print(f"上傳錯誤：{str(e)}")
            return None

    def upload_existing_file(self, file_path, folder='uploads'):
        """
        將已存在的本地文件上傳至 S3 存儲桶
        
        Args:
            file_path: 本地文件的完整路徑
            folder: S3 存儲桶中的子目錄（默認為 'uploads'）
            
        Returns:
            str: 上傳後文件的公共 URL 或 None（如果上傳失敗）
        """
        if self.s3_client is None:
            return None
        
        if not os.path.exists(file_path):
            return None
        
        # 獲取文件名並確保安全且唯一
        filename = os.path.basename(file_path)
        filename = secure_filename(filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        s3_path = f"{folder}/{unique_filename}"
        
        try:
            # 上傳文件到 S3
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_path,
                ExtraArgs={'ACL': 'public-read'}  # 使文件公開可訪問
            )
            
            # 構建 S3 文件的公共 URL
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_path}"
            return url
        except NoCredentialsError:
            print("憑證錯誤：無法訪問 S3")
            return None
        except Exception as e:
            print(f"上傳錯誤：{str(e)}")
            return None