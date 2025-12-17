import os
from flask import Flask
from flask_cors import CORS
from extensions import db
# 对应你的 backend/routes 文件夹
from routes import auth, skills, lost_items, messages

def create_app():
    # 1. 明确指定 static 文件夹为当前目录下的 'static'
    app = Flask(__name__, static_folder='static')
    app.json.ensure_ascii = False
    CORS(app)

    basedir = os.path.abspath(os.path.dirname(__file__))

    # 2. 【关键】MySQL 配置
    # 格式: mysql+pymysql://用户名:密码@地址:端口/数据库名
    # 请确保你已经安装了驱动: pip install pymysql
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost/campus_market?charset=utf8mb4'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your_secret_key_here'

    # 3. 上传文件路径 (指向 backend/static/uploads)
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'static', 'uploads')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    db.init_app(app)

    # 注册蓝图
    app.register_blueprint(auth.bp, url_prefix='/api')
    app.register_blueprint(skills.bp, url_prefix='/api')
    app.register_blueprint(lost_items.bp, url_prefix='/api')
    app.register_blueprint(messages.bp, url_prefix='/api')

    @app.route('/')
    def index():
        return "Campus Market API is running!"

    return app

if __name__ == '__main__':
    app = create_app()
    # 允许局域网访问
    print("🚀 后端服务启动: http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)