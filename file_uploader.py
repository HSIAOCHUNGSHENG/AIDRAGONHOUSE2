import os
import uuid
from flask import Blueprint, request, jsonify, url_for, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename

upload_bp = Blueprint('uploads', __name__)

# 檢查文件副檔名是否允許上傳
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 文件上傳處理路由
@upload_bp.route('/admin/upload', methods=['POST'])
@login_required
def upload_file():
    """處理文件上傳 - 用於 TinyMCE 編輯器圖像上傳"""
    if 'file' not in request.files:
        return jsonify({'location': ''})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'location': ''})
    
    if file and allowed_file(file.filename):
        # 為上傳的文件生成唯一名稱，避免名稱衝突
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # 確保上傳目錄存在
        upload_folder = os.path.join(current_app.static_folder, 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # 保存文件
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # 返回可訪問的URL路徑給TinyMCE
        file_url = url_for('static', filename=f'uploads/{unique_filename}')
        return jsonify({'location': file_url})
    
    return jsonify({'location': ''})