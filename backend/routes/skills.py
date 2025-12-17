from flask import Blueprint, jsonify, request
from sqlalchemy import or_, and_
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


# --- 【核心修改】确认完成接口（含积分结算） ---
@bp.route('/order/finish', methods=['POST'])
def finish_order():
    try:
        data = request.get_json()
        item_id = data.get('id')
        category = data.get('category')

        # 1. 查找订单
        if category == 'skill':
            item = Skill.query.get(item_id)
        else:
            item = LostItem.query.get(item_id)

        if not item: return jsonify({"code": 404, "msg": "未找到订单"}), 404

        # 防止重复结算 (只有状态为1进行中时才结算)
        if item.status != 1:
            return jsonify({"code": 400, "msg": "订单状态不正确"}), 400

        # 2. 积分结算逻辑
        reward_points = 5
        target_user = None

        # 准备用户对象
        publisher = User.query.get(item.user_id)
        helper = User.query.get(item.helper_id)

        if category == 'skill':
            if item.type == 1:
                # 技能-我能提供: 发布者出力 -> 奖励发布者
                target_user = publisher
            else:
                # 技能-需要帮助: 接收者出力 -> 奖励接收者
                target_user = helper

        elif category == 'lost':
            if item.type == 1:
                # 招领-捡到了: 发布者捡到 -> 奖励发布者
                target_user = publisher
            else:
                # 失物-丢失了: 接收者帮忙找回 -> 奖励接收者
                target_user = helper

        # 3. 执行加分
        if target_user:
            target_user.points += reward_points

        # 4. 更新状态
        item.status = 2
        db.session.commit()

        msg = f"订单已完成，{target_user.username if target_user else '用户'} 积分+5"
        return jsonify({"code": 200, "msg": msg})
    except Exception as e:
        print(e)
        return jsonify({"code": 500, "msg": str(e)}), 500


# --- 评价接口 ---
@bp.route('/order/review', methods=['POST'])
def review_order():
    try:
        data = request.get_json()
        item_id = data.get('id')
        category = data.get('category')
        action = data.get('action')  # 'reward' (好评) or 'complain' (差评)
        current_uid = data.get('current_user_id')  # 前端必须传当前操作人ID

        model = Skill if category == 'skill' else LostItem
        item = model.query.get(item_id)

        if not item: return jsonify({"code": 404, "msg": "未找到"}), 404

        # 确定评价方向
        target_user = None
        is_poster = (str(current_uid) == str(item.user_id))

        # 1. 如果我是发布者 -> 我评价接单者 (helper)
        if is_poster:
            if item.poster_review != 0: return jsonify({"code": 400, "msg": "您已评价过"}), 400

            item.poster_review = 1 if action == 'reward' else 2
            if item.helper_id:
                target_user = User.query.get(item.helper_id)

        # 2. 如果我是接单者 -> 我评价发布者 (user/author)
        elif str(current_uid) == str(item.helper_id):
            if item.helper_review != 0: return jsonify({"code": 400, "msg": "您已评价过"}), 400

            item.helper_review = 1 if action == 'reward' else 2
            target_user = User.query.get(item.user_id)

        else:
            return jsonify({"code": 403, "msg": "无权操作"}), 403

        # 3. 结算评价积分 (+/- 2分) 给对方
        if target_user:
            change = 2 if action == 'reward' else -2
            target_user.points += change
            db.session.commit()
            return jsonify({"code": 200, "msg": f"评价成功，对方积分 {'+2' if change > 0 else '-2'}"})

        db.session.commit()
        return jsonify({"code": 200, "msg": "评价成功"})
    except Exception as e:
        print(e)
        return jsonify({"code": 500, "msg": str(e)}), 500


# --- 获取"我参与的互助" ---
@bp.route('/user/helps/<int:user_id>', methods=['GET'])
def get_my_helps(user_id):
    try:
        skill_filter = or_(
            Skill.helper_id == user_id,
            and_(Skill.user_id == user_id, Skill.status != 0)
        )
        lost_filter = or_(
            LostItem.helper_id == user_id,
            and_(LostItem.user_id == user_id, LostItem.status != 0)
        )

        my_skills = Skill.query.filter(skill_filter).all()
        my_losts = LostItem.query.filter(lost_filter).all()

        data = []

        def pack_item(obj, cat):
            is_poster = (str(obj.user_id) == str(user_id))

            if is_poster:
                target_id = obj.helper_id
                helper_user = User.query.get(target_id) if target_id else None
                target_name = helper_user.username if helper_user else "未知接单人"
                my_review = obj.poster_review
            else:
                target_id = obj.user_id
                target_name = obj.author.username if obj.author else "未知发布者"
                my_review = obj.helper_review

            if obj.create_time:
                time_str = obj.create_time.strftime("%Y-%m-%d %H:%M")
            else:
                time_str = "未知时间"

            return {
                "id": obj.id,
                "category": cat,
                "title": obj.title,
                "image": obj.image,
                "status": obj.status,
                "create_time": time_str,
                "is_poster": is_poster,
                "target_id": target_id,
                "target_name": target_name,
                "my_review": my_review
            }

        for s in my_skills: data.append(pack_item(s, "skill"))
        for l in my_losts: data.append(pack_item(l, "lost"))

        data.sort(key=lambda x: x['create_time'], reverse=True)
        return jsonify({"code": 200, "data": data})
    except Exception as e:
        print(f"Get helps error: {e}")
        return jsonify({"code": 500, "msg": str(e)}), 500


# --- 获取热门标签 (智能导航版) ---
@bp.route('/tags', methods=['GET'])
def get_hot_tags():
    try:
        # 1. 获取最新的技能标题
        skill_titles = db.session.query(Skill.title) \
            .filter_by(status=0) \
            .order_by(Skill.create_time.desc()) \
            .limit(6).all()

        # 2. 获取最新的失物标题
        lost_titles = db.session.query(LostItem.title) \
            .filter_by(status=0) \
            .order_by(LostItem.create_time.desc()) \
            .limit(4).all()

        tags = []
        seen_titles = set()

        # 封装数据：带上 category 标记
        for t in skill_titles:
            if t[0] and t[0] not in seen_titles:
                tags.append({"text": t[0], "cat": "skill"})  # 标记为 skill
                seen_titles.add(t[0])

        for t in lost_titles:
            if t[0] and t[0] not in seen_titles:
                tags.append({"text": t[0], "cat": "lost"})  # 标记为 lost
                seen_titles.add(t[0])

        # 如果没数据，给点默认的
        if not tags:
            tags = [
                {"text": "Python", "cat": "skill"},
                {"text": "雨伞", "cat": "lost"}
            ]

        # 返回前 8 个
        return jsonify({"code": 200, "data": tags[:8]})
    except Exception as e:
        print(e)
        return jsonify({"code": 500, "msg": str(e)}), 500