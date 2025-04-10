from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os

class Admin(UserMixin, db.Model):
    """管理員模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Admin {self.username}>'

class Message(db.Model):
    """用戶留言模型"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 新增回覆相關欄位
    replied = db.Column(db.Boolean, default=False)
    reply_text = db.Column(db.Text, nullable=True)
    replied_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Message {self.id} from {self.name}>'

class Service(db.Model):
    """服務項目模型"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Service {self.title}>'

class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_or_create():
        profile = Profile.query.first()
        if not profile:
            profile = Profile(content="講師「Jonathan H. 」個人小檔案：\n覺得英文稱謂很傲口也可以叫我「蕭蕭」。\n雙魚座B型、\n銀櫃KTV VIP會員、\nMcDonald's點點卡持有人、\n東海中文系博士生、\n東海中文系兼任講師、\n教育部素養導向高教學習創新計畫（XPlorer探索者計畫）AI專班共同課程講師、\n東海大學AI學習體驗設計專班、核心工作坊教師。")
            db.session.add(profile)
            db.session.commit()
        return profile

class News(db.Model):
    """最新消息與貼文模型"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    publish_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_featured = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<News {self.title}>'

class Portfolio(db.Model):
    """作品展示模型"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    order = db.Column(db.Integer, default=0)  # 用於自定義排序
    active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Portfolio {self.title}>'

class ContactInfo(db.Model):
    """聯絡資訊模型"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    line_id = db.Column(db.String(64), nullable=True)
    qr_code_path = db.Column(db.String(255), nullable=True)
    additional_info = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_or_create():
        """獲取或創建聯絡資訊記錄"""
        contact_info = ContactInfo.query.first()
        if not contact_info:
            contact_info = ContactInfo(
                email="ommanibamehumpractice@gmail.com",
                line_id="rainbowhunter",
                qr_code_path="images/line_qrcode.jpg",
                additional_info="歡迎透過Email或LINE與我聯繫"
            )
            db.session.add(contact_info)
            db.session.commit()
        return contact_info