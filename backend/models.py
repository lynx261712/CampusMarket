# models.py
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# --- 1. 用户表 (核心: 积分与认证) ---
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)  # 学号或用户名
    password = db.Column(db.String(50), nullable=False)  # <--- 新增这一行
    contact = db.Column(db.String(100), nullable=False)  # 默认联系方式 (微信/手机)
    points = db.Column(db.Integer, default=10)  # 初始积分 10分

    # 关系: 一个人可以发布多个失物、技能、记录
    skills = db.relationship('Skill', backref='author', lazy=True)
    lost_items = db.relationship('LostItem', backref='author', lazy=True)


# --- 2. 失物招领表 (新业务) ---
class LostItem(db.Model):
    __tablename__ = 'lost_items'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)  # 物品名称
    desc = db.Column(db.Text)  # 详细描述/特征
    location = db.Column(db.String(100))  # 丢失/拾获地点

    # 类型: 0=我丢了东西(寻物), 1=我捡到了(招领)
    type = db.Column(db.Integer, default=0)

    # 状态: 0=进行中, 1=已认领/已归还
    status = db.Column(db.Integer, default=0)

    image = db.Column(db.String(500))  # 图片链接
    create_time = db.Column(db.DateTime, default=datetime.now)

    # 外键: 谁发布的
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


# --- 3. 技能/需求表 (原有业务升级) ---
class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    cost = db.Column(db.String(100), nullable=False)  # 代价 (如: 5积分/一杯奶茶)

    # 类型: 1=我能提供(赚积分), 2=我急需(花积分)
    type = db.Column(db.Integer, default=1)

    # 状态: 0=开放中, 1=已锁定(有人接单), 2=已完成
    status = db.Column(db.Integer, default=0)

    image = db.Column(db.String(500))
    create_time = db.Column(db.DateTime, default=datetime.now)

    # 外键: 关联到 User 表 (替换原来的 user_name 字符串)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


# --- 4. 交易/操作记录表 (用于后台和积分结算) ---
class Record(db.Model):
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key=True)

    # 谁发起的 (如: 认领人、接单人)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    # 关联的目标 (可以是失物，也可以是技能)
    target_id = db.Column(db.Integer)
    target_type = db.Column(db.String(20))  # 'lost' 或 'skill'

    # 积分变动值 (如: +5, -2)
    point_change = db.Column(db.Integer, default=0)

    create_time = db.Column(db.DateTime, default=datetime.now)