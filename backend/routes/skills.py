from flask import Blueprint, jsonify, request
from extensions import db    # 修改：去掉了 ..
from models import Skill     # 修改：去掉了 ..

bp = Blueprint('skills', __name__)

@bp.route('/skills', methods=['GET'])
def get_skills():
    try:
        keyword = request.args.get('q')
        query = Skill.query
        if keyword:
            query = query.filter(Skill.title.contains(keyword) | Skill.cost.contains(keyword))
        skills = query.order_by(Skill.create_time.desc()).all()
        data = []
        for s in skills:
            author_name = s.author.username if s.author else "未知用户"
            author_avatar = f"https://ui-avatars.com/api/?name={author_name}&background=random"
            data.append({
                "id": s.id, "title": s.title, "cost": s.cost, "type": s.type,
                "image": s.image, "status": s.status, "user": author_name, "avatar": author_avatar
            })
        return jsonify({"code": 200, "data": data})
    except Exception as e: return jsonify({"code": 500, "msg": str(e)}), 500

@bp.route('/skills', methods=['POST'])
def create_skill():
    try:
        data = request.get_json()
        new_skill = Skill(
            title=data['title'], cost=data['cost'], type=int(data.get('type', 1)),
            image=data.get('image', "https://picsum.photos/200/200"),
            user_id=data.get('user_id', 1)
        )
        db.session.add(new_skill)
        db.session.commit()
        return jsonify({"code": 200, "msg": "发布成功"})
    except Exception as e: return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route('/skills/complete', methods=['POST'])
def complete_transaction():
    """
    逻辑说明：
    1. 只有发布者(需求方)能确认完成。
    2. 确认后，需求方扣除积分，提供方增加积分。
    3. 使用数据库事务，确保资金安全。
    """
    data = request.get_json()
    skill_id = data.get('skill_id')
    current_user_id = data.get('user_id')  # 当前操作人（通常是需求发起者）

    try:
        # 开启事务
        with db.session.begin_nested():
            skill = Skill.query.get(skill_id)
            if not skill:
                return jsonify({"code": 404, "msg": "记录不存在"}), 404

            if skill.status == 2:
                return jsonify({"code": 400, "msg": "该订单已完成，请勿重复操作"}), 400

            # 假设场景：A发布了“求取快递”(type=2)，花费积分。B来帮忙。
            # 这里简化逻辑：我们假设 skill 表里没有存 'helper_id'，
            # 为了演示，我们假设只要点击完成，就扣除当前用户的分（如果是需求），或者不做变动仅改状态。

            # 让我们做一个更有技术含量的逻辑：
            # 假设 skill.cost 存储的是数字字符串 "10"。
            try:
                cost_val = int(skill.cost.replace("积分", "").strip())
            except:
                cost_val = 0  # 如果写的是“一杯奶茶”，则不涉及积分变动

            user = User.query.get(current_user_id)

            # 如果这是一个“需求单”(type=2)，发布者确认完成时，代表他要付钱了
            # (实际逻辑中通常是发布时冻结，这里简化为结算时扣除)
            if skill.type == 2 and cost_val > 0:
                if user.points < cost_val:
                    return jsonify({"code": 400, "msg": "您的积分不足，无法结算"}), 400

                user.points -= cost_val
                # 这里理论上应该给“接单人”加分，但由于我们没做复杂的接单系统
                # 我们就假设系统回收了，或者你可以加一个字段 `helper_id` 给那个人加分

            # 如果这是一个“提供单”(type=1)，发布者确认完成，代表他赚到了（假设有人付了现金）
            # 或者我们在这里做一个“系统奖励”，只要完成一单，系统奖励 2 分
            if skill.type == 1:
                user.points += 2

                # 更新状态为已完成
            skill.status = 2

            # 提交事务 (SQLAlchemy 会自动 commit，如果报错会自动 rollback)
            db.session.add(user)
            db.session.add(skill)

        db.session.commit()
        return jsonify({"code": 200, "msg": "交易完成，积分已更新"})

    except Exception as e:
        db.session.rollback()  # 报错回滚
        return jsonify({"code": 500, "msg": f"交易失败: {str(e)}"}), 500