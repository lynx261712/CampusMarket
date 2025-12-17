import flet as ft
from api_client import APIClient


# 确保传递了 user_id 用于评价接口
def MyHelpView(user_id, on_back, show_msg, on_nav_to_chat):
    list_view = ft.ListView(expand=True, spacing=10, padding=10)

    # 1. 评价逻辑
    def do_review(e):
        action = e.control.data['action']
        item = e.control.data['item']

        # 乐观更新：点击即禁用，防止重复
        e.control.disabled = True
        e.control.update()

        try:
            # 必须传入 current_user_id 以便后端判断是谁在评价
            res = APIClient.review_order(item['id'], item['category'], action, user_id)
            if res.status_code == 200:
                show_msg(res.json().get('msg'), "green")
                load_data()  # 刷新列表状态
            else:
                show_msg(res.json().get('msg'))
                e.control.disabled = False  # 失败恢复
                e.control.update()
        except Exception as ex:
            show_msg(str(ex))

    # 2. 完成订单逻辑
    def do_finish(e):
        item = e.control.data
        try:
            res = APIClient.finish_order(item['id'], item['category'])
            if res.status_code == 200:
                show_msg("已确认完成，请进行评价", "green")
                load_data()
            else:
                show_msg(res.json().get('msg'))
        except Exception as ex:
            show_msg(str(ex))

    # 3. 聊天逻辑
    def go_chat(e):
        item = e.control.data
        t_id = item.get('target_id')
        t_name = item.get('target_name')
        if t_id:
            on_nav_to_chat(t_id, t_name)
        else:
            show_msg("无法获取对方信息")

    def load_data():
        list_view.controls.clear()
        try:
            res = APIClient.get_my_helps(user_id)
            if res.status_code == 200:
                data = res.json().get('data', [])
                for item in data:
                    status = item.get('status', 0)  # 1=进行中, 2=已完成
                    my_review = item.get('my_review', 0)  # 0=未评, 1/2=已评
                    is_poster = item.get('is_poster', False)  # 我是发布者吗？
                    target_name = item.get('target_name', '对方')

                    # --- 按钮状态逻辑 ---
                    btn_finish_disabled = True
                    btn_good_disabled = True
                    btn_bad_disabled = True

                    # 只有进行中(1) 才能点完成
                    if status == 1:
                        btn_finish_disabled = False

                    # 只有已完成(2) 且 我没评价过(0) 才能评价
                    elif status == 2:
                        if my_review == 0:
                            btn_good_disabled = False
                            btn_bad_disabled = False

                    # --- 按钮组件 ---

                    # 联系按钮：显示对方名字
                    btn_chat = ft.ElevatedButton(
                        f"联系 {target_name}",
                        icon=ft.Icons.CHAT,
                        color="blue", bgcolor="#e3f2fd",
                        data=item, on_click=go_chat
                    )

                    # 完成按钮
                    btn_finish = ft.ElevatedButton(
                        "完成互助",
                        disabled=btn_finish_disabled,
                        bgcolor="blue" if not btn_finish_disabled else "grey",
                        color="white",
                        height=30,
                        style=ft.ButtonStyle(padding=5),
                        data=item,
                        on_click=do_finish
                    )

                    # 评价按钮
                    # 如果已评价，根据结果高亮对应的图标，并禁用所有
                    good_color = "green" if my_review == 1 else ("grey" if btn_good_disabled else "green")
                    bad_color = "red" if my_review == 2 else ("grey" if btn_bad_disabled else "red")

                    btn_good = ft.IconButton(
                        ft.Icons.THUMB_UP,
                        icon_color=good_color,
                        disabled=btn_good_disabled or (my_review != 0),  # 如果已评，彻底禁用
                        tooltip="好评 (+2分)",
                        data={"action": "reward", "item": item},
                        on_click=do_review
                    )

                    btn_bad = ft.IconButton(
                        ft.Icons.THUMB_DOWN,
                        icon_color=bad_color,
                        disabled=btn_bad_disabled or (my_review != 0),
                        tooltip="差评 (-2分)",
                        data={"action": "complain", "item": item},
                        on_click=do_review
                    )

                    # 底部操作栏
                    action_row = ft.Row([
                        btn_chat,
                        ft.Container(expand=True),
                        btn_finish,
                        btn_good,
                        btn_bad
                    ], alignment=ft.MainAxisAlignment.START)

                    # 状态显示文本
                    status_text = "进行中" if status == 1 else "已完成"
                    status_color = "blue" if status == 1 else "green"

                    role_text = "我发布的" if is_poster else "我接收的"

                    list_view.controls.append(ft.Container(
                        bgcolor="white", padding=10, border_radius=10, border=ft.border.all(1, "#eee"),
                        content=ft.Column([
                            ft.Row([
                                ft.Image(src=item['image'], width=60, height=60, border_radius=5),
                                ft.Container(expand=True, content=ft.Column([
                                    ft.Row([
                                        ft.Text(item['title'], size=16, weight="bold"),
                                        ft.Container(
                                            content=ft.Text(role_text, size=10, color="white"),
                                            bgcolor="orange" if is_poster else "purple",
                                            padding=3, border_radius=4
                                        )
                                    ], spacing=5),
                                    ft.Text(f"互助对象: {target_name}", size=12, color="grey"),
                                    ft.Text(f"状态: {status_text}", size=12, color=status_color)
                                ]))
                            ]),
                            ft.Divider(height=10),
                            action_row
                        ])
                    ))
                if not data: list_view.controls.append(ft.Text("暂无互助记录", text_align="center", color="grey"))
        except Exception as e:
            print(e)
        if list_view.page: list_view.update()

    load_data()
    return ft.Column([
        ft.Container(padding=10, content=ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: on_back(None)),
                                                 ft.Text("我参与的互助", size=20, weight="bold")])),
        list_view
    ])