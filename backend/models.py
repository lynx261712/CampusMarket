from datetime import datetime
from extensions import db


# --- 1. 用户表 ---
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(100), nullable=False)
    points = db.Column(db.Integer, default=10)
    # 【新增】存储自定义头像 URL
    avatar = db.Column(db.String(500), nullable=True)
    # 关系
    skills = db.relationship('Skill', backref='author', lazy=True, foreign_keys='Skill.user_id')
    lost_items = db.relationship('LostItem', backref='author', lazy=True, foreign_keys='LostItem.user_id')


# --- 2. 消息表 (新增) ---
class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.now)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_msgs')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_msgs')


# --- 3. 失物招领表 (升级) ---
class LostItem(db.Model):
    __tablename__ = 'lost_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.Text)
    location = db.Column(db.String(100))
    type = db.Column(db.Integer, default=0)
    image = db.Column(db.String(500))
    create_time = db.Column(db.DateTime, default=datetime.now)

    # 关联发布者
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 【新增字段】
    status = db.Column(db.Integer, default=0)  # 0=开放, 1=进行中, 2=已完成
    helper_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 接单人
    review_status = db.Column(db.Integer, default=0)  # 0=未评价, 1=已打赏, 2=已投诉


# --- 4. 技能表 (升级) ---
class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Integer, default=1)
    image = db.Column(db.String(500))
    create_time = db.Column(db.DateTime, default=datetime.now)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # 【新增字段】
    status = db.Column(db.Integer, default=0)
    helper_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    review_status = db.Column(db.Integer, default=0)