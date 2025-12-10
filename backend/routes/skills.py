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