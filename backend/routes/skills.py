from flask import Blueprint, jsonify, request
from extensions import db
from models import Skill, LostItem, User
from utils import save_uploaded_file

bp = Blueprint('skills', __name__)


# --- 获取技能列表 ---
@bp.route('/skills', methods=['GET'])
def get_skills():
    try:
        keyword = request.args.get('q')
        query = Skill.query.filter_by(status=0)  # 只显示未接单
        if keyword:
            query = query.filter(Skill.title.contains(keyword) | Skill.cost.contains(keyword))
        skills = query.order_by(Skill.create_time.desc()).all()

        data = []
        for s in skills:
            author_name = s.author.username if s.author else "未知用户"
            data.append({
                "id": s.id, "title": s.title, "cost": s.cost, "type": s.type,
                "image": s.image, "status": s.status,
                "user": author_name, "user_id": s.user_id
            })
        return jsonify({"code": 200, "data": data})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# --- 发布技能 ---
@bp.route('/skills', methods=['POST'])
def create_skill():
    try:
        # 1. 文本数据
        title = request.form.get('title')
        cost = request.form.get('cost')
        type_val = request.form.get('type', 1, type=int)  # 默认1
        user_id = request.form.get('user_id', type=int)

        if not title or not user_id:
            return jsonify({"code": 400, "msg": "标题或用户ID不能为空"}), 400

        # 2. 文件数据
        image_file = request.files.get('image')
        image_url = save_uploaded_file(image_file)

        new_skill = Skill(
            title=title,
            cost=cost,
            type=type_val,
            image=image_url,
            user_id=user_id
        )
        db.session.add(new_skill)
        db.session.commit()
        return jsonify({"code": 200, "msg": "发布成功"})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"code": 500, "msg": str(e)}), 500


# ==========================================
#  以下是之前缺失的核心交互接口
# ==========================================

# --- 接单接口 ---
@bp.route('/order/accept', methods=['POST'])
def accept_order():
    try:
        data = request.get_json()
        item_id = data.get('id')
        category = data.get('category')  # 'skill' 或 'lost'
        user_id = data.get('user_id')

        # 根据类型选择模型
        model = Skill if category == 'skill' else LostItem
        item = model.query.get(item_id)

        if not item:
            return jsonify({"code": 404, "msg": "订单不存在"}), 404

        # 校验状态
        if item.status != 0:
            return jsonify({"code": 400, "msg": "手慢了，该单已被抢或已完成"}), 400

        # 校验不能接自己的单
        if str(item.user_id) == str(user_id):
            return jsonify({"code": 400, "msg": "不能接自己的单"}), 400

        # 更新状态为进行中 (1)
        item.status = 1
        item.helper_id = user_id
        db.session.commit()

        return jsonify({"code": 200, "msg": "接单成功"})
    except Exception as e:
        print(e)
        return jsonify({"code": 500, "msg": str(e)}), 500


# --- 确认完成接口 ---
@bp.route('/order/finish', methods=['POST'])
def finish_order():
    try:
        data = request.get_json()
        item_id = data.get('id')
        category = data.get('category')

        model = Skill if category == 'skill' else LostItem
        item = model.query.get(item_id)

        if not item:
            return jsonify({"code": 404, "msg": "未找到订单"}), 404

        # 更新状态为已完成 (2)
        item.status = 2

        # 可选：这里可以处理积分转移逻辑
        # helper = User.query.get(item.helper_id)
        # helper.points += ...

        db.session.commit()
        return jsonify({"code": 200, "msg": "订单已完成"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# --- 评价接口 ---
@bp.route('/order/review', methods=['POST'])
def review_order():
    try:
        data = request.get_json()
        item_id = data.get('id')
        category = data.get('category')
        action = data.get('action')  # 'reward' (好评) or 'complain' (差评)

        model = Skill if category == 'skill' else LostItem
        item = model.query.get(item_id)

        if not item: return jsonify({"code": 404, "msg": "未找到"}), 404

        # 1=好评, 2=差评
        item.review_status = 1 if action == 'reward' else 2

        # 简单的积分奖惩逻辑
        if item.helper_id:
            helper = User.query.get(item.helper_id)
            if helper:
                if action == 'reward':
                    helper.points += 2
                elif action == 'complain':
                    helper.points -= 5

        db.session.commit()
        return jsonify({"code": 200, "msg": "评价成功"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# --- 获取"我参与的互助" ---
@bp.route('/user/helps/<int:user_id>', methods=['GET'])
def get_my_helps(user_id):
    try:
        # 查询我是 helper 的所有记录
        my_skills = Skill.query.filter_by(helper_id=user_id).all()
        my_losts = LostItem.query.filter_by(helper_id=user_id).all()

        data = []
        # 整合两类数据
        for s in my_skills:
            data.append({
                "id": s.id, "category": "skill", "title": s.title,
                "image": s.image, "status": s.status, "review": s.review_status,
                "create_time": s.create_time
            })
        for l in my_losts:
            data.append({
                "id": l.id, "category": "lost", "title": l.title,
                "image": l.image, "status": l.status, "review": l.review_status,
                "create_time": l.create_time
            })

        # 按时间倒序
        data.sort(key=lambda x: x['create_time'], reverse=True)
        return jsonify({"code": 200, "data": data})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500