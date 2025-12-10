from datetime import datetime
from extensions import db  # 修改：去掉了前面的 .

# --- 1. 用户表 ---
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(100), nullable=False)
    points = db.Column(db.Integer, default=10)

    skills = db.relationship('Skill', backref='author', lazy=True)
    lost_items = db.relationship('LostItem', backref='author', lazy=True)

# --- 2. 失物招领表 ---
class LostItem(db.Model):
    __tablename__ = 'lost_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.Text)
    location = db.Column(db.String(100))
    type = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer, default=0)
    image = db.Column(db.String(500))
    create_time = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# --- 3. 技能/需求表 ---
class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Integer, default=1)
    status = db.Column(db.Integer, default=0)
    image = db.Column(db.String(500))
    create_time = db.Column(db.DateTime, default=datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)