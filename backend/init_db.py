from app import create_app
from extensions import db
from models import User, LostItem, Skill

app = create_app()

def init_database():
    with app.app_context():
        # 1. 暴力重置
        db.drop_all()
        db.create_all()

        # 2. 创建测试用户
        u1 = User(username="admin", password="123", contact="VX: admin888", points=100)
        u2 = User(username="studentA", password="123", contact="VX: stu_a_123", points=10)
        u3 = User(username="studentB", password="123", contact="VX: stu_b_456", points=50)
        db.session.add_all([u1, u2, u3])
        db.session.commit()

        # 3. 创建测试数据
        l1 = LostItem(title="黑色联想充电器", desc="图书馆三楼", location="图书馆", type=1, user_id=u1.id, image="https://picsum.photos/200/200?1")
        l2 = LostItem(title="校园卡丢了", desc="卡号2021001", location="二食堂", type=0, user_id=u2.id, image="https://picsum.photos/200/200?2")
        s1 = Skill(title="Python 辅导", cost="10积分", type=1, user_id=u3.id, image="https://picsum.photos/200/200?3")
        s2 = Skill(title="求帮取快递", cost="2积分", type=2, user_id=u2.id, image="https://picsum.photos/200/200?4")

        db.session.add_all([l1, l2, s1, s2])
        db.session.commit()
        print(">>> 数据库初始化完成")

if __name__ == '__main__':
    init_database()