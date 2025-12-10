from flask import Blueprint, jsonify, request
from extensions import db       # 修改：去掉了 ..
from models import User, Skill, LostItem  # 修改：去掉了 ..

bp = Blueprint('auth', __name__)

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"code": 400, "msg": "用户名已存在"}), 400
    new_user = User(username=data['username'], password=data['password'], contact=data['contact'])
    db.session.add(new_user); db.session.commit()
    return jsonify({"code": 200, "msg": "注册成功"})

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if user: return jsonify({"code": 200, "data": {"user_id": user.id, "username": user.username}})
    return jsonify({"code": 401, "msg": "账号或密码错误"}), 401

@bp.route('/user/<int:user_id>', methods=['GET'])
def get_user_info(user_id):
    user = User.query.get(user_id)
    if not user: return jsonify({"code": 404, "msg": "用户不存在"}), 404
    skills_count = Skill.query.filter_by(user_id=user.id).count()
    lost_count = LostItem.query.filter_by(user_id=user.id).count()
    return jsonify({
        "code": 200,
        "data": {
            "id": user.id, "username": user.username, "contact": user.contact, "points": user.points,
            "avatar": f"https://ui-avatars.com/api/?name={user.username}&background=random",
            "stats": {"posts": skills_count + lost_count, "skills": skills_count, "lost": lost_count}
        }
    })

@bp.route('/user/update', methods=['POST'])
def update_user():
    data = request.get_json()
    user = User.query.get(data['user_id'])
    if data.get('username'): user.username = data['username']
    if data.get('contact'): user.contact = data['contact']
    db.session.commit()
    return jsonify({"code": 200, "msg": "修改成功"})

@bp.route('/user/posts/<int:user_id>', methods=['GET'])
def get_user_posts(user_id):
    skills = Skill.query.filter_by(user_id=user_id).all()
    losts = LostItem.query.filter_by(user_id=user_id).all()
    data = []
    for s in skills:
        data.append({"id": s.id, "category": "skill", "title": s.title, "tag": "提供" if s.type==1 else "求助", "color": "blue" if s.type==1 else "orange", "image": s.image, "info": s.cost, "create_time": s.create_time.strftime("%m-%d")})
    for l in losts:
        data.append({"id": l.id, "category": "lost", "title": l.title, "tag": "捡到" if l.type==1 else "丢失", "color": "green" if l.type==1 else "red", "image": l.image, "info": l.location, "create_time": l.create_time.strftime("%m-%d")})
    data.sort(key=lambda x: x['create_time'], reverse=True)
    return jsonify({"code": 200, "data": data})

@bp.route('/delete', methods=['POST'])
def delete_post():
    data = request.get_json()
    item = Skill.query.get(data['id']) if data['category'] == 'skill' else LostItem.query.get(data['id'])
    if item: db.session.delete(item); db.session.commit()
    return jsonify({"code": 200, "msg": "删除成功"})

@bp.route('/interact', methods=['POST'])
def interact():
    try:
        data = request.get_json()
        item = Skill.query.get(data.get('item_id')) if data.get('category') == 'skill' else LostItem.query.get(data.get('item_id'))
        if not item: return jsonify({"code": 404, "msg": "未找到"}), 404
        contact = item.author.contact if item.author else "未留联系方式"
        return jsonify({"code": 200, "data": {"contact": contact}})
    except Exception as e: return jsonify({"code": 500, "msg": str(e)}), 500