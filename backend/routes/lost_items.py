from flask import Blueprint, jsonify, request
from sqlalchemy.sql.expression import func
from extensions import db
from models import LostItem, User
from utils import save_uploaded_file

bp = Blueprint('lost_items', __name__)


@bp.route('/lost-items', methods=['GET'])
def get_lost_items():
    try:
        item_type = request.args.get('type', type=int)
        keyword = request.args.get('keyword')
        location = request.args.get('location')

        query = LostItem.query.filter_by(status=0)
        if item_type is not None:
            query = query.filter_by(type=item_type)
        if keyword:
            query = query.filter(LostItem.title.contains(keyword) | LostItem.desc.contains(keyword))
        if location:
            query = query.filter(LostItem.location.contains(location))

        items = query.order_by(LostItem.create_time.desc()).all()
        data = []
        for item in items:
            author_name = item.author.username if item.author else "未知用户"
            data.append({
                "id": item.id, "title": item.title, "desc": item.desc,
                "location": item.location, "type": item.type, "image": item.image,
                "time": item.create_time.strftime("%Y-%m-%d"),
                "user": author_name, "user_id": item.user_id
            })
        return jsonify({"code": 200, "data": data})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


@bp.route('/lost-items', methods=['POST'])
def create_lost_item():
    try:
        title = request.form.get('title')
        desc = request.form.get('desc')
        location = request.form.get('location')
        # 增加 default=0 保护
        type_val = request.form.get('type', 0, type=int)
        user_id = request.form.get('user_id', type=int)

        image_file = request.files.get('image')
        image_url = save_uploaded_file(image_file)

        new_item = LostItem(
            title=title, desc=desc, location=location,
            type=type_val, image=image_url, user_id=user_id
        )
        db.session.add(new_item)

        # 积分奖励逻辑
        user = User.query.get(user_id)
        if user and new_item.type == 1:  # 捡到东西
            user.points += 5

        db.session.commit()
        return jsonify({"code": 200, "msg": "发布成功"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# ... (保留 tags 接口不变) ...
@bp.route('/lost-items/tags', methods=['GET'])
def get_search_tags():
    # ... (保持原样)
    pass