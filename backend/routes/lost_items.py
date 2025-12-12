from flask import Blueprint, jsonify, request
from sqlalchemy.sql.expression import func
from extensions import db
from models import LostItem, User

bp = Blueprint('lost_items', __name__)


# --- 获取失物列表 (过滤掉已接单 status!=0) ---
@bp.route('/lost-items', methods=['GET'])
def get_lost_items():
    try:
        item_type = request.args.get('type', type=int)
        keyword = request.args.get('keyword')
        location = request.args.get('location')

        # 只看开放中的
        query = LostItem.query.filter_by(status=0)

        if item_type is not None: query = query.filter_by(type=item_type)
        if keyword:
            query = query.filter(LostItem.title.contains(keyword) | LostItem.desc.contains(keyword))
        if location:
            query = query.filter(LostItem.location.contains(location))

        items = query.order_by(LostItem.create_time.desc()).all()

        data = []
        for item in items:
            author_name = item.author.username if item.author else "未知用户"
            author_avatar = f"https://ui-avatars.com/api/?name={author_name}&background=random"
            data.append({
                "id": item.id, "title": item.title, "desc": item.desc, "location": item.location,
                "type": item.type, "image": item.image, "time": item.create_time.strftime("%Y-%m-%d"),
                "user": author_name, "avatar": author_avatar,
                "user_id": item.user_id  # 返回发布者ID
            })
        return jsonify({"code": 200, "data": data})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# --- 获取标签 ---
@bp.route('/lost-items/tags', methods=['GET'])
def get_search_tags():
    try:
        locs = db.session.query(LostItem.location).distinct().order_by(func.random()).limit(5).all()
        titles = db.session.query(LostItem.title).distinct().order_by(func.random()).limit(5).all()
        return jsonify({
            "code": 200,
            "data": {
                "locations": [l[0] for l in locs if l[0]],
                "keywords": [t[0] for t in titles if t[0]]
            }
        })
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# --- 发布 ---
@bp.route('/lost-items', methods=['POST'])
def create_lost_item():
    try:
        data = request.get_json()
        new_item = LostItem(
            title=data.get('title'), desc=data.get('desc'), location=data.get('location'),
            type=int(data.get('type', 0)),
            image=data.get('image', "https://picsum.photos/200/200"),
            user_id=data.get('user_id', 1)
        )
        db.session.add(new_item)

        # 简单积分奖励: 发布失物+5
        user = User.query.get(data.get('user_id', 1))
        if user and new_item.type == 1:  # 捡到东西
            user.points += 5

        db.session.commit()
        return jsonify({"code": 200, "msg": "发布成功"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500