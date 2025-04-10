import os
import uuid
from datetime import datetime

from markupsafe import Markup
from flask import Flask, render_template, request, flash, redirect, url_for, abort, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from s3_uploader import S3Uploader

def nl2br(value):
    return Markup(value.replace('\n', '<br>'))


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
# 註冊 nl2br 過濾器
app.jinja_env.filters['nl2br'] = nl2br
# setup a secret key, required by sessions
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# 設置上傳文件相關配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上傳文件大小為 16MB

# Amazon S3 配置
app.config['AWS_ACCESS_KEY_ID'] = os.environ.get('AWS_ACCESS_KEY_ID')
app.config['AWS_SECRET_ACCESS_KEY'] = os.environ.get('AWS_SECRET_ACCESS_KEY')
app.config['AWS_REGION'] = os.environ.get('AWS_REGION', 'ap-northeast-1')  # 默認東京區域
app.config['AWS_BUCKET_NAME'] = os.environ.get('AWS_BUCKET_NAME')

# 初始化 S3 上傳器
s3_uploader = S3Uploader(app)

# 確保上傳目錄存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# configure the database, relative to the app instance folder
database_url = os.environ.get("DATABASE_URL")
if database_url:
    # SQLAlchemy 1.4+ compatibility for postgres URLs
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
else:
    # 如果沒有環境變量，則使用SQLite
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"

# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

# 註冊檔案上傳藍圖
from file_uploader import upload_bp
app.register_blueprint(upload_bp)

# 設置 login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'
login_manager.login_message = '請先登入管理員帳號'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    from models import Admin
    return Admin.query.get(int(user_id))

@app.context_processor
def inject_now():
    """將當前日期時間添加到所有模板的上下文中"""
    from datetime import datetime
    return {'now': datetime.now()}

def init_db():
    """初始化資料庫並創建示例數據"""
    from models import Service, Admin, News, Profile, ContactInfo

    # 創建表格
    db.create_all()

    # 檢查是否已有管理員帳號，如果沒有則創建默認管理員
    if Admin.query.count() == 0:
        default_admin = Admin(
            username='admin', 
            email='fet0989147988@gmail.com'
        )
        default_admin.set_password('m1234857')  # 設置初始密碼
        db.session.add(default_admin)
        db.session.commit()
        print("初始管理員已添加到數據庫")

    # 檢查是否已有服務項目，如果沒有則創建默認服務
    if Service.query.count() == 0:
        default_services = [
            Service(title="提供AI終端應用與課程設計思維演講服務", description="為個人、團體或企業提供專業的AI應用培訓與思維演講", active=True),
            Service(title="修水電", description="專業水電維修與安裝服務", active=True),
            Service(title="借醬油", description="生活互助，隨時提供您所需的醬油", active=True),
            Service(title="臨終助唸", description="提供佛教臨終關懷與助唸服務", active=True)
        ]

        for service in default_services:
            db.session.add(service)

        db.session.commit()
        print("初始服務已添加到數據庫")

    # 檢查是否已有最新消息，如果沒有則創建默認消息
    if News.query.count() == 0:
        default_news = [
            News(
                title="AI臥龍崗近期活動預告", 
                content="近期將舉辦多場AI課程與實作工作坊，歡迎有興趣的朋友報名參加。詳情請透過聯絡表單向我們詢問。", 
                is_featured=True, 
                active=True
            ),
            News(
                title="新服務上線通知", 
                content="我們最近添加了新的服務項目，歡迎查看服務列表了解詳情，或直接聯繫我們預約服務。", 
                is_featured=False, 
                active=True
            ),
            News(
                title="感謝各位的支持", 
                content="感謝各位一直以來對AI臥龍崗的支持，我們將繼續提供優質的服務與資訊，期待與您的進一步合作。", 
                is_featured=False, 
                active=True
            )
        ]

        for news in default_news:
            db.session.add(news)

        db.session.commit()
        print("初始最新消息已添加到數據庫")

    #建立預設個人檔案
    if Profile.query.count() == 0:
        default_profile = Profile(content="講師「Jonathan H. 」個人小檔案：\n覺得英文稱謂很傲口也可以叫我「蕭蕭」。\n雙魚座B型、\n銀櫃KTV VIP會員、\nMcDonald's點點卡持有人、\n東海中文系博士生、\n東海中文系兼任講師、\n教育部素養導向高教學習創新計畫（XPlorer探索者計畫）AI專班共同課程講師、\n東海大學AI學習體驗設計專班、核心工作坊教師。")
        db.session.add(default_profile)
        db.session.commit()
        print("初始個人檔案已添加到數據庫")
        
    # 建立預設聯絡資訊
    if ContactInfo.query.count() == 0:
        default_contact = ContactInfo(
            email="ommanibamehumpractice@gmail.com",
            line_id="rainbowhunter",
            qr_code_path="images/line_qrcode.jpg",
            additional_info="歡迎透過Email或LINE與我聯繫"
        )
        db.session.add(default_contact)
        db.session.commit()
        print("初始聯絡資訊已添加到數據庫")


with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401

    # 初始化資料庫
    init_db()

@app.route('/')
def index():
    # 從數據庫獲取活躍服務和最新消息
    from models import Service, News, Profile, ContactInfo, Portfolio
    from flask import request
    
    # 獲取作品展示分頁參數
    portfolio_page = request.args.get('portfolio_page', 1, type=int)
    portfolio_per_page = 6  # 每頁顯示6個作品
    
    services = Service.query.filter_by(active=True).all()
    
    # 先按是否精選、再按發布日期降序排序
    news_posts = News.query.filter_by(active=True).order_by(
        News.is_featured.desc(),  # 精選的排在前面
        News.publish_date.desc()  # 然後按日期降序
    ).limit(3).all()
    
    # 查詢作品展示
    portfolio_query = Portfolio.query.filter_by(active=True).order_by(
        Portfolio.order.asc(),  # 先按自定義排序
        Portfolio.created_at.desc()  # 然後按建立日期降序
    )
    
    # 計算總作品數和總頁數
    portfolio_total = portfolio_query.count()
    portfolio_pages = (portfolio_total + portfolio_per_page - 1) // portfolio_per_page  # 向上取整
    
    # 獲取當前頁的作品
    portfolios = portfolio_query.offset((portfolio_page - 1) * portfolio_per_page).limit(portfolio_per_page).all()
    
    profile = Profile.query.first()
    contact_info = ContactInfo.get_or_create()
    
    return render_template(
        'index.html', 
        services=services, 
        news_posts=news_posts, 
        profile=profile, 
        contact_info=contact_info,
        portfolios=portfolios,
        portfolio_page=portfolio_page,
        portfolio_pages=portfolio_pages
    )

@app.route('/googleacb1ce472a34877b.html')
def google_verification():
    """提供Google站點驗證文件"""
    return app.send_static_file('google/googleacb1ce472a34877b.html')

@app.route('/contact', methods=['POST'])
def contact():
    """處理聯絡表單提交"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message_text = request.form.get('message')

        if not name or not email or not subject or not message_text:
            flash('請填寫所有必填欄位', 'error')
            return redirect(url_for('index'))

        try:
            from models import Message
            new_message = Message(
                name=name,
                email=email,
                subject=subject,
                message=message_text
            )
            db.session.add(new_message)
            db.session.commit()
            flash('感謝您的留言，我們會盡快回覆您！', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'發生錯誤，請稍後再試。錯誤訊息：{str(e)}', 'error')

        return redirect(url_for('index'))


# 管理員相關路由
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理員登入"""
    # 如果已經登入，直接跳轉至管理後台
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        from models import Admin
        user = Admin.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash('登入成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('admin_dashboard'))
        else:
            flash('登入失敗，請檢查用戶名和密碼。', 'error')

    return render_template('admin/login.html')


@app.route('/admin/logout')
@login_required
def admin_logout():
    """管理員登出"""
    logout_user()
    flash('您已成功登出。', 'info')
    return redirect(url_for('index'))


@app.route('/admin')
@login_required
def admin_dashboard():
    """管理後台首頁"""
    from models import Message, Service, News, Profile, Portfolio

    # 收集儀表板統計數據
    message_count = Message.query.count()
    replied_count = Message.query.filter_by(replied=True).count()
    service_count = Service.query.count()
    active_service_count = Service.query.filter_by(active=True).count()
    news_count = News.query.count()
    featured_news_count = News.query.filter_by(is_featured=True).count()
    portfolio_count = Portfolio.query.count()
    active_portfolio_count = Portfolio.query.filter_by(active=True).count()

    stats = {
        'message_count': message_count,
        'replied_count': replied_count,
        'service_count': service_count,
        'active_service_count': active_service_count,
        'news_count': news_count,
        'featured_news_count': featured_news_count,
        'portfolio_count': portfolio_count,
        'active_portfolio_count': active_portfolio_count
    }

    # 獲取最近留言
    recent_messages = Message.query.order_by(Message.created_at.desc()).limit(5).all()

    # 獲取最近消息，先顯示精選，再按日期降序
    recent_news = News.query.order_by(
        News.is_featured.desc(),
        News.publish_date.desc()
    ).limit(5).all()

    profile = Profile.query.first()

    return render_template('admin/dashboard.html', stats=stats, recent_messages=recent_messages, recent_news=recent_news, profile=profile)


@app.route('/admin/messages')
@login_required
def admin_messages():
    """留言管理頁面"""
    from models import Message
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_template('admin/messages.html', messages=messages)


@app.route('/admin/message/<int:message_id>', methods=['GET'])
@login_required
def admin_message_detail(message_id):
    """查看留言詳情"""
    from models import Message
    message = Message.query.get_or_404(message_id)
    return render_template('admin/message_detail.html', message=message)


@app.route('/admin/services')
@login_required
def admin_services():
    """服務項目管理頁面"""
    from models import Service
    services = Service.query.all()
    return render_template('admin/services.html', services=services)


@app.route('/admin/service/new', methods=['GET', 'POST'])
@login_required
def admin_service_new():
    """添加新服務項目"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        active = 'active' in request.form

        if not title:
            flash('服務名稱不能為空', 'error')
            return redirect(url_for('admin_service_new'))

        try:
            from models import Service
            new_service = Service(
                title=title,
                description=description,
                active=active
            )
            db.session.add(new_service)
            db.session.commit()
            flash('服務項目已添加成功', 'success')
            return redirect(url_for('admin_services'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失敗: {str(e)}', 'error')

    return render_template('admin/service_form.html', service=None, is_new=True)


@app.route('/admin/service/edit/<int:service_id>', methods=['GET', 'POST'])
@login_required
def admin_service_edit(service_id):
    """編輯服務項目"""
    from models import Service
    service = Service.query.get_or_404(service_id)

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        active = 'active' in request.form

        if not title:
            flash('服務名稱不能為空', 'error')
            return redirect(url_for('admin_service_edit', service_id=service_id))

        try:
            service.title = title
            service.description = description
            service.active = active
            db.session.commit()
            flash('服務項目已更新成功', 'success')
            return redirect(url_for('admin_services'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失敗: {str(e)}', 'error')

    return render_template('admin/service_form.html', service=service, is_new=False)


@app.route('/admin/service/delete/<int:service_id>', methods=['POST'])
@login_required
def admin_service_delete(service_id):
    """刪除服務項目"""
    from models import Service
    service = Service.query.get_or_404(service_id)

    try:
        db.session.delete(service)
        db.session.commit()
        flash('服務項目已刪除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'刪除失敗: {str(e)}', 'error')

    return redirect(url_for('admin_services'))


@app.route('/admin/profile', methods=['GET', 'POST'])
@login_required
def admin_profile():
    """管理員個人資料"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_user.check_password(current_password):
            flash('當前密碼不正確', 'error')
            return redirect(url_for('admin_profile'))

        if new_password != confirm_password:
            flash('新密碼和確認密碼不匹配', 'error')
            return redirect(url_for('admin_profile'))

        if len(new_password) < 6:
            flash('新密碼至少需要6個字符', 'error')
            return redirect(url_for('admin_profile'))

        current_user.set_password(new_password)
        db.session.commit()
        flash('密碼已成功更新', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/profile.html')


@app.route('/admin/news')
@login_required
def admin_news():
    """最新消息管理頁面"""
    from models import News
    # 先顯示精選內容，然後按發布日期降序排序
    news_posts = News.query.order_by(
        News.is_featured.desc(),
        News.publish_date.desc()
    ).all()
    return render_template('admin/news.html', news_posts=news_posts)


@app.route('/admin/news/new', methods=['GET', 'POST'])
@login_required
def admin_news_new():
    """添加新消息"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        is_featured = 'is_featured' in request.form
        active = 'active' in request.form

        if not title or not content:
            flash('標題和內容不能為空', 'error')
            return redirect(url_for('admin_news_new'))

        try:
            from models import News
            new_news = News(
                title=title,
                content=content,
                is_featured=is_featured,
                active=active
            )
            db.session.add(new_news)
            db.session.commit()
            flash('消息已添加成功', 'success')
            return redirect(url_for('admin_news'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失敗: {str(e)}', 'error')

    return render_template('admin/news_form.html', news=None, is_new=True)


@app.route('/admin/news/edit/<int:news_id>', methods=['GET', 'POST'])
@login_required
def admin_news_edit(news_id):
    """編輯消息"""
    from models import News
    news = News.query.get_or_404(news_id)

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        is_featured = 'is_featured' in request.form
        active = 'active' in request.form

        if not title or not content:
            flash('標題和內容不能為空', 'error')
            return redirect(url_for('admin_news_edit', news_id=news_id))

        try:
            news.title = title
            news.content = content
            news.is_featured = is_featured
            news.active = active
            db.session.commit()
            flash('消息已更新成功', 'success')
            return redirect(url_for('admin_news'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失敗: {str(e)}', 'error')

    return render_template('admin/news_form.html', news=news, is_new=False)


@app.route('/admin/news/delete/<int:news_id>', methods=['POST'])
@login_required
def admin_news_delete(news_id):
    """刪除消息"""
    from models import News
    news = News.query.get_or_404(news_id)

    try:
        db.session.delete(news)
        db.session.commit()
        flash('消息已刪除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'刪除失敗: {str(e)}', 'error')

    return redirect(url_for('admin_news'))

@app.route('/admin/profile/edit', methods=['GET', 'POST'])
@login_required
def admin_profile_edit():
    """編輯個人小檔案"""
    from models import Profile
    profile = Profile.query.first() or Profile() #get existing or create new

    if request.method == 'POST':
        content = request.form.get('content')

        if not content:
            flash('個人小檔案內容不能為空', 'error')
            return redirect(url_for('admin_profile_edit'))

        try:
            if not profile.id: #if new profile, add it to db
                db.session.add(profile)
            profile.content = content
            db.session.commit()
            flash('個人小檔案已更新成功', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失敗: {str(e)}', 'error')

    return render_template('admin/profile_edit.html', profile=profile)

@app.route('/admin/contact', methods=['GET', 'POST'])
@login_required
def admin_contact():
    """聯絡資訊管理頁面"""
    from models import ContactInfo
    contact_info = ContactInfo.get_or_create()
    
    if request.method == 'POST':
        email = request.form.get('email')
        line_id = request.form.get('line_id')
        additional_info = request.form.get('additional_info')
        
        if not email:
            flash('電子郵件不能為空', 'error')
            return redirect(url_for('admin_contact'))
        
        try:
            # 處理QR碼圖片上傳
            qr_code_file = request.files.get('qr_code')
            if qr_code_file and qr_code_file.filename:
                # 確保 static/images 目錄存在
                import os
                upload_dir = os.path.join('static', 'images')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                # 獲取文件擴展名並保存
                filename = f"line_qrcode_{int(datetime.now().timestamp())}"
                ext = os.path.splitext(qr_code_file.filename)[1]
                full_filename = f"{filename}{ext}"
                file_path = os.path.join(upload_dir, full_filename)
                qr_code_file.save(file_path)
                
                # 更新數據庫中的QR碼路徑
                contact_info.qr_code_path = os.path.join('images', full_filename)
            
            # 更新其他信息
            contact_info.email = email
            contact_info.line_id = line_id
            contact_info.additional_info = additional_info
            db.session.commit()
            flash('聯絡資訊已更新成功', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失敗: {str(e)}', 'error')
    
    return render_template('admin/contact_form.html', contact_info=contact_info)

@app.route('/news/<int:news_id>')
def news_detail(news_id):
    """顯示單篇文章的詳細內容"""
    from models import News, Profile, ContactInfo
    
    # 獲取指定ID的文章，確保它是啟用狀態
    news = News.query.filter_by(id=news_id, active=True).first_or_404()
    
    # 獲取個人資料以保持佈局一致性
    profile = Profile.query.first()
    contact_info = ContactInfo.get_or_create()
    
    # 獲取其他活躍的最新消息作為"相關文章"
    related_news = News.query.filter(News.id != news_id, News.active == True).order_by(
        News.is_featured.desc(),
        News.publish_date.desc()
    ).limit(3).all()
    
    return render_template('news_detail.html', news=news, profile=profile, 
                          related_news=related_news, contact_info=contact_info)
@app.route('/robots.txt')
def robots():
    """提供 robots.txt 文件"""
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap():
    """提供 sitemap.xml 文件"""
    return send_from_directory(app.static_folder, 'sitemap.xml')

@app.route('/portfolio/<int:portfolio_id>')
def portfolio_detail(portfolio_id):
    """顯示作品展示的詳細內容"""
    from models import Portfolio, Profile, ContactInfo
    
    # 獲取指定ID的作品，確保它是啟用狀態
    portfolio = Portfolio.query.filter_by(id=portfolio_id, active=True).first_or_404()
    
    # 獲取個人資料以保持佈局一致性
    profile = Profile.query.first()
    contact_info = ContactInfo.get_or_create()
    
    # 獲取其他活躍的作品作為"相關作品"
    related_portfolios = Portfolio.query.filter(
        Portfolio.id != portfolio_id, 
        Portfolio.active == True
    ).order_by(
        Portfolio.order.asc(),
        Portfolio.created_at.desc()
    ).limit(3).all()
    
    return render_template('portfolio_detail.html', 
                           portfolio=portfolio, 
                           profile=profile, 
                           related_portfolios=related_portfolios, 
                           contact_info=contact_info)

# 作品展示管理路由
@app.route('/admin/portfolios')
@login_required
def admin_portfolios():
    """作品展示管理頁面"""
    from models import Portfolio
    # 按排序順序和建立日期降序排列
    portfolios = Portfolio.query.order_by(
        Portfolio.order.asc(),
        Portfolio.created_at.desc()
    ).all()
    return render_template('admin/portfolios.html', portfolios=portfolios)

@app.route('/admin/portfolio/new', methods=['GET', 'POST'])
@login_required
def admin_portfolio_new():
    """添加新作品展示"""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        order = request.form.get('order', 0, type=int)
        active = 'active' in request.form
        external_image_url = request.form.get('external_image_url')
        
        if not title or not description:
            flash('標題和描述不能為空', 'error')
            return redirect(url_for('admin_portfolio_new'))
        
        try:
            from models import Portfolio
            import os
            from datetime import datetime
            
            new_portfolio = Portfolio(
                title=title,
                description=description,
                order=order,
                active=active
            )
            
            # 處理外部圖片URL
            if external_image_url and external_image_url.strip():
                new_portfolio.external_image_url = external_image_url.strip()
            
            # 處理圖片上傳 (優先使用上傳的圖片)
            image_file = request.files.get('image')
            if image_file and image_file.filename:
                # 確保上傳目錄存在
                upload_dir = os.path.join('static', 'images', 'portfolio')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                # 生成唯一文件名
                filename = f"portfolio_{int(datetime.now().timestamp())}"
                ext = os.path.splitext(image_file.filename)[1]
                full_filename = f"{filename}{ext}"
                file_path = os.path.join(upload_dir, full_filename)
                image_file.save(file_path)
                
                # 更新數據庫中的圖片路徑
                new_portfolio.image_path = os.path.join('images', 'portfolio', full_filename)
                # 如果上傳了圖片，清除外部URL（兩者只能存在一個）
                new_portfolio.external_image_url = None
            
            db.session.add(new_portfolio)
            db.session.commit()
            flash('作品已添加成功', 'success')
            return redirect(url_for('admin_portfolios'))
        except Exception as e:
            db.session.rollback()
            flash(f'添加失敗: {str(e)}', 'error')
    
    return render_template('admin/portfolio_form.html', portfolio=None, is_new=True)

@app.route('/admin/portfolio/edit/<int:portfolio_id>', methods=['GET', 'POST'])
@login_required
def admin_portfolio_edit(portfolio_id):
    """編輯作品展示"""
    from models import Portfolio
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        order = request.form.get('order', 0, type=int)
        active = 'active' in request.form
        remove_image = 'remove_image' in request.form
        external_image_url = request.form.get('external_image_url')
        remove_external_image = 'remove_external_image' in request.form
        
        if not title or not description:
            flash('標題和描述不能為空', 'error')
            return redirect(url_for('admin_portfolio_edit', portfolio_id=portfolio_id))
        
        try:
            import os
            from datetime import datetime
            
            # 更新基本信息
            portfolio.title = title
            portfolio.description = description
            portfolio.order = order
            portfolio.active = active
            
            # 處理本地圖片操作
            if remove_image and portfolio.image_path:
                # 如果用戶選擇刪除當前圖片
                try:
                    # 嘗試從文件系統中刪除圖片
                    os.remove(os.path.join('static', portfolio.image_path))
                except:
                    pass # 如果刪除失敗，繼續執行（可能是因為文件不存在）
                portfolio.image_path = None
                
            # 處理外部圖片URL操作
            if remove_external_image and portfolio.external_image_url:
                portfolio.external_image_url = None
                
            # 處理新的外部圖片URL
            if external_image_url and external_image_url.strip() and not remove_external_image:
                portfolio.external_image_url = external_image_url.strip()
                # 如果設置了外部URL且沒有上傳新圖片，清除本地圖片
                if not (request.files.get('image') and request.files.get('image').filename):
                    if portfolio.image_path:
                        try:
                            os.remove(os.path.join('static', portfolio.image_path))
                        except:
                            pass
                    portfolio.image_path = None
            
            # 處理新圖片上傳
            image_file = request.files.get('image')
            if image_file and image_file.filename:
                # 確保上傳目錄存在
                upload_dir = os.path.join('static', 'images', 'portfolio')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                # 生成唯一文件名
                filename = f"portfolio_{int(datetime.now().timestamp())}"
                ext = os.path.splitext(image_file.filename)[1]
                full_filename = f"{filename}{ext}"
                file_path = os.path.join(upload_dir, full_filename)
                image_file.save(file_path)
                
                # 如果原來有圖片，刪除舊圖片
                if portfolio.image_path:
                    try:
                        os.remove(os.path.join('static', portfolio.image_path))
                    except:
                        pass
                
                # 更新數據庫中的圖片路徑
                portfolio.image_path = os.path.join('images', 'portfolio', full_filename)
                # 如果上傳了新圖片，清除外部URL（兩者只能存在一個）
                portfolio.external_image_url = None
            
            portfolio.updated_at = datetime.utcnow()
            db.session.commit()
            flash('作品已更新成功', 'success')
            return redirect(url_for('admin_portfolios'))
        except Exception as e:
            db.session.rollback()
            flash(f'更新失敗: {str(e)}', 'error')
    
    return render_template('admin/portfolio_form.html', portfolio=portfolio, is_new=False)

@app.route('/admin/portfolio/delete/<int:portfolio_id>', methods=['POST'])
@login_required
def admin_portfolio_delete(portfolio_id):
    """刪除作品展示"""
    from models import Portfolio
    portfolio = Portfolio.query.get_or_404(portfolio_id)
    
    try:
        # 如果有圖片，嘗試從文件系統中刪除
        if portfolio.image_path:
            import os
            try:
                os.remove(os.path.join('static', portfolio.image_path))
            except:
                pass # 如果刪除失敗，繼續執行
        
        # 從數據庫中刪除記錄
        db.session.delete(portfolio)
        db.session.commit()
        flash('作品已刪除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'刪除失敗: {str(e)}', 'error')
    
    return redirect(url_for('admin_portfolios'))
