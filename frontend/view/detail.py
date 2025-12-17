import flet as ft
from api_client import APIClient


# 【修改】增加了参数 on_nav_to_chat
def DetailView(item, category, on_back, show_msg, current_user, on_nav_to_chat):
    detail_img = ft.Image(src=item['image'], width=float("inf"), height=200, fit=ft.ImageFit.COVER)

    # 1. 聊天/联系逻辑
    def go_chat(e):
        if not current_user['id']: return show_msg("请先登录")

        target_id = item.get('user_id')
        # 获取对方名字，如果没有则显示未知
        target_name = item.get('user', '未知用户')

        if str(target_id) == str(current_user['id']):
            return show_msg("不能和自己聊天")

        # 【核心修改】直接跳转到聊天页面
        on_nav_to_chat(target_id, target_name)

    # 2. 接单逻辑
    def do_accept(e):
        if not current_user['id']: return show_msg("请先登录")
        # 注意：这里需要把 ID 转成字符串比较，或者确保类型一致，防止 int 和 str 比较失败
        if str(current_user['id']) == str(item.get('user_id')): return show_msg("不能接自己的单")

        try:
            res = APIClient.accept_order(item['id'], category, current_user['id'])
            if res.status_code == 200:
                show_msg("接单成功！请在'我的帮助'中查看", "green")
                on_back(None)  # 返回列表
            else:
                show_msg(res.json().get('msg', "接单失败"))
        except Exception as ex:
            show_msg(str(ex))

    # 按钮组
    action_row = ft.Row([
        ft.ElevatedButton("💬 联系", on_click=go_chat, expand=1),
        ft.ElevatedButton("🙋‍♂️ 接收", on_click=do_accept, expand=1, bgcolor="orange", color="white")
    ])

    content_val = f"代价: {item.get('cost')}" if category == "skill" else f"描述: {item.get('desc')}"

    # 构建元数据行 (发布人/地点)
    meta_info = []
    if category == "skill":
        meta_info = [ft.Icon(ft.Icons.PERSON, size=16), ft.Text(item.get('user', '未知'))]
    else:
        meta_info = [ft.Icon(ft.Icons.LOCATION_ON, size=16), ft.Text(item.get('location', '未知'))]

    return ft.Column([
        ft.Stack([
            detail_img,
            ft.IconButton(ft.Icons.ARROW_BACK, icon_color="white", on_click=lambda e: on_back(None), left=5, top=5)
        ]),
        ft.Container(padding=20, content=ft.Column([
            ft.Text(item['title'], size=22, weight="bold"),
            ft.Divider(),
            ft.Text(content_val, size=16),
            ft.Row(meta_info),
            ft.Container(height=20),
            action_row
        ]))
    ])