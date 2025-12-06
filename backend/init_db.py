# init_db.py
import os
from flask import Flask
from models import db, User, LostItem, Skill

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)


def init_database():
    with app.app_context():
        # 1. 暴力重置: 删除所有旧表，创建新表
        db.drop_all()
        db.create_all()

        # 2. 创建测试用户
        u1 = User(username="admin", password="123", contact="VX: admin888", points=100)
        u2 = User(username="studentA", password="123", contact="VX: stu_a_123", points=10)
        u3 = User(username="studentB", password="123", contact="VX: stu_b_456", points=50)
        db.session.add_all([u1, u2, u3])
        db.session.commit()  # 先提交，生成 User ID

        # 3. 创建失物招领数据
        l1 = LostItem(
            title="黑色联想充电器",
            desc="在图书馆三楼捡到的，放在前台了",
            location="图书馆三楼",
            type=1,  # 捡到了
            user_id=u1.id,  # 管理员发布的
            image="https://picsum.photos/200/200?1"
        )
        l2 = LostItem(
            title="我的校园卡丢了！！",
            desc="卡号 2021001，谁看到了麻烦联系我，急急急",
            location="二食堂附近",
            type=0,  # 丢东西了
            user_id=u2.id,
            image="https://picsum.photos/200/200?2"
        )

        # 4. 创建技能数据
        s1 = Skill(
            title="Python 辅导",
            cost="10积分",
            type=1,  # 提供服务
            user_id=u3.id,
            image="https://picsum.photos/200/200?3"
        )
        s2 = Skill(
            title="求帮取快递",
            cost="2积分",
            type=2,  # 需求
            user_id=u2.id,
            image="https://picsum.photos/200/200?4"
        )

        db.session.add_all([l1, l2, s1, s2])
        db.session.commit()

        print(">>> 数据库重构完成！包含 3个用户, 2个失物, 2个技能。")


if __name__ == '__main__':
    init_database()