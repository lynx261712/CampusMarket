from flask import Blueprint, jsonify, request
from extensions import db      # 修改：去掉了 ..
from models import LostItem    # 修改：去掉了 ..

bp = Blueprint('lost_items', __name__)

@bp.route('/lost-items', methods=['GET'])
def get_lost_items():
    try:
        item_type = request.args.get('type', type=int)
        keyword = request.args.get('q')
        query = LostItem.query
        if item_type is not None: query = query.filter_by(type=item_type)
        if keyword:
            query = query.filter(LostItem.title.contains(keyword) | LostItem.desc.contains(keyword) | LostItem.location.contains(keyword))
        items = query.order_by(LostItem.create_time.desc()).all()
        data = []
        for item in items:
            author_name = item.author.username if item.author else "未知用户"
            author_avatar = f"https://ui-avatars.com/api/?name={author_name}&background=random"
            data.append({
                "id": item.id, "title": item.title, "desc": item.desc, "location": item.location,
                "type": item.type, "image": item.image, "time": item.create_time.strftime("%Y-%m-%d"),
                "user": author_name, "avatar": author_avatar
            })
        return jsonify({"code": 200, "data": data})
    except Exception as e: return jsonify({"code": 500, "msg": str(e)}), 500

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
        db.session.commit()
        return jsonify({"code": 200, "msg": "发布成功"})
    except Exception as e: return jsonify({"code": 500, "msg": str(e)}), 500