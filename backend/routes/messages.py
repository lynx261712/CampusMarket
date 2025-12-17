from flask import Blueprint, jsonify, request
from sqlalchemy import or_, and_
from extensions import db
from models import Message, User

bp = Blueprint('messages', __name__)


# --- 发送消息 ---
@bp.route('/messages', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        sender_id = data.get('sender_id')
        receiver_id = data.get('receiver_id')
        content = data.get('content')

        if not content:
            return jsonify({"code": 400, "msg": "内容不能为空"}), 400

        new_msg = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content
        )
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({"code": 200, "msg": "发送成功"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# --- 获取消息记录 (获取我和某人的聊天历史) ---
@bp.route('/messages', methods=['GET'])
def get_messages():
    try:
        user_id = request.args.get('user_id')
        partner_id = request.args.get('partner_id')  # 对方ID

        if not user_id or not partner_id:
            return jsonify({"code": 400, "msg": "参数缺失"}), 400

        # 查询逻辑：(发送者是我 且 接收者是他) OR (发送者是他 且 接收者是我)
        # 按时间正序排列
        msgs = Message.query.filter(
            or_(
                and_(Message.sender_id == user_id, Message.receiver_id == partner_id),
                and_(Message.sender_id == partner_id, Message.receiver_id == user_id)
            )
        ).order_by(Message.create_time.asc()).all()

        data = []
        for m in msgs:
            # 判断这条消息是不是我发的
            is_me = (str(m.sender_id) == str(user_id))
            data.append({
                "id": m.id,
                "content": m.content,
                "is_me": is_me,
                "time": m.create_time.strftime("%H:%M")
            })

        return jsonify({"code": 200, "data": data})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500


# --- (可选) 标记已读 ---
@bp.route('/messages/read', methods=['POST'])
def mark_read():
    try:
        data = request.get_json()
        sender_id = data.get('sender_id')  # 对方
        receiver_id = data.get('receiver_id')  # 我

        # 把所有对方发给我的未读消息标记为已读
        Message.query.filter_by(sender_id=sender_id, receiver_id=receiver_id, is_read=False).update(dict(is_read=True))
        db.session.commit()
        return jsonify({"code": 200, "msg": "已读"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500