from flask import Blueprint, jsonify, request
from sqlalchemy import or_, and_
from extensions import db
from models import Message, User
from utils import save_uploaded_file  # 【重要】记得导入这个

bp = Blueprint('messages', __name__)


# --- 发送消息 (支持文本和图片) ---
@bp.route('/messages', methods=['POST'])
def send_message():
    try:
        # 改为从 form 和 files 中获取数据，以支持文件上传
        sender_id = request.form.get('sender_id')
        receiver_id = request.form.get('receiver_id')
        content = request.form.get('content')
        image_file = request.files.get('image')

        if not sender_id or not receiver_id:
            return jsonify({"code": 400, "msg": "参数缺失"}), 400

        # 处理图片
        if image_file:
            # 保存图片并获取 URL
            url = save_uploaded_file(image_file)
            # 使用特殊前缀标记这是图片
            final_content = f"image:{url}"
        else:
            if not content:
                return jsonify({"code": 400, "msg": "内容不能为空"}), 400
            final_content = content

        new_msg = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=final_content
        )
        db.session.add(new_msg)
        db.session.commit()
        return jsonify({"code": 200, "msg": "发送成功"})
    except Exception as e:
        print(e)
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

            # 【新增】判断内容类型 (文本 vs 图片)
            msg_type = "image" if m.content.startswith("image:") else "text"
            # 如果是图片，去掉前缀只保留 URL
            clean_content = m.content.replace("image:", "") if msg_type == "image" else m.content

            data.append({
                "id": m.id,
                "type": msg_type,  # 告诉前端这是图片还是字
                "content": clean_content,
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
        # Message.query.filter_by(sender_id=sender_id, receiver_id=receiver_id, is_read=False).update(dict(is_read=True))
        # db.session.commit()
        return jsonify({"code": 200, "msg": "已读"})
    except Exception as e:
        return jsonify({"code": 500, "msg": str(e)}), 500