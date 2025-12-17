import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app, url_for

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 默认的空白图片URL (当用户没上传时使用)
# 这里使用一个在线的灰色占位图，你也可以在 static 下放一个 default.png 然后指向它
DEFAULT_IMAGE_URL = "https://via.placeholder.com/200x200/cccccc/999999?text=No+Image"


def allowed_file(filename):
    """检查文件扩展名是否合法"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    """
    保存上传的文件并返回可访问的 URL
    如果没文件或不合法，返回默认 URL
    """
    if file and allowed_file(file.filename):
        # 生成一个安全且唯一的文件名 (使用 UUID 防止重名)
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"

        # 保存路径
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(upload_path)

        # 生成外部可访问的 URL
        # 例如: http://localhost:5000/static/uploads/xxx.jpg
        # _external=True 会生成带域名的完整 URL
        return url_for('static', filename=f'uploads/{unique_filename}', _external=True)

    return DEFAULT_IMAGE_URL