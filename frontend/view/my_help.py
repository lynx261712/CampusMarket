import flet as ft
from api_client import APIClient


def MyHelpView(user_id, on_back, show_msg):
    list_view = ft.ListView(expand=True, spacing=10, padding=10)

    # 1. 评价逻辑 (好评/差评)
    def do_review(e):
        action = e.control.data['action']  # 'reward' or 'complain'
        item = e.control.data['item']

        try:
            # Helper 评价 Publisher (target_user_id 自动由后端判断或前端不传，后端默认处理)
            # 注意：这里的 action 会传递给后端，后端会根据 action 加减分
            res = APIClient.review_order(item['id'], item['category'], action)
            if res.status_code == 200:
                show_msg(res.json().get('msg'), "green")
                load_data()  # 刷新状态
            else:
                show_msg(res.json().get('msg'))
        except Exception as ex:
            show_msg(str(ex))

    # 2. 完成互助逻辑
    def do_finish(e):
        item = e.control.data
        try:
            # 这里的 finish_order 会触发后端的基础积分结算 (+3 或 +5)
            res = APIClient.finish_order(item['id'], item['category'])
            if res.status_code == 200:
                show_msg("已确认完成，基础积分已发放", "green")
                # 刷新列表，此时状态变为 status=2，前端逻辑会让评价按钮变亮
                load_data()
            else:
                show_msg(res.json().get('msg'))
        except Exception as ex:
            show_msg(str(ex))

    def load_data():
        list_view.controls.clear()
        try:
            res = APIClient.get_my_helps(user_id)
            if res.status_code == 200:
                data = res.json().get('data', [])
                for item in data:
                    status = item.get('status', 0)
                    review_status = item.get('review', 0)  # 0=未评, 1=好, 2=差

                    # --- 按钮状态逻辑 ---
                    # 默认全部禁用
                    btn_finish_disabled = True
                    btn_good_disabled = True
                    btn_bad_disabled = True

                    if status == 1:
                        # 进行中: 可以点击完成，不能评价
                        btn_finish_disabled = False
                        btn_good_disabled = True
                        btn_bad_disabled = True
                    elif status == 2:
                        # 已完成: 不能再点完成
                        btn_finish_disabled = True
                        # 如果还没评价(review=0)，可以评价
                        if review_status == 0:
                            btn_good_disabled = False
                            btn_bad_disabled = False
                        else:
                            # 已经评价过，全部禁用
                            btn_good_disabled = True
                            btn_bad_disabled = True

                    # --- 构建按钮组 ---
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

                    # 好评按钮 (+2分)
                    btn_good = ft.IconButton(
                        ft.Icons.THUMB_UP,
                        icon_color="green" if not btn_good_disabled else "grey",
                        disabled=btn_good_disabled,
                        tooltip="好评 (对方+2分)",
                        data={"action": "reward", "item": item},
                        on_click=do_review
                    )

                    # 差评按钮 (-2分)
                    btn_bad = ft.IconButton(
                        ft.Icons.THUMB_DOWN,
                        icon_color="red" if not btn_bad_disabled else "grey",
                        disabled=btn_bad_disabled,
                        tooltip="差评 (对方-2分)",
                        data={"action": "complain", "item": item},
                        on_click=do_review
                    )

                    # 组装操作栏
                    action_row = ft.Row([btn_finish, btn_good, btn_bad], alignment=ft.MainAxisAlignment.END)

                    if review_status != 0:
                        review_text = "已好评" if review_status == 1 else "已差评"
                        action_row.controls.append(ft.Text(review_text, size=12, color="grey"))

                    # 卡片 UI
                    list_view.controls.append(ft.Container(
                        bgcolor="white", padding=10, border_radius=10,
                        border=ft.border.all(1, "#eee"),
                        content=ft.Column([
                            ft.Row([
                                ft.Image(src=item['image'], width=60, height=60, border_radius=5),
                                ft.Container(expand=True, content=ft.Column([
                                    ft.Text(item['title'], size=16, weight="bold"),
                                    ft.Text(f"当前状态: {'进行中' if status == 1 else '已完成'}", size=12,
                                            color="blue" if status == 1 else "green")
                                ]))
                            ]),
                            ft.Divider(height=10),
                            action_row
                        ])
                    ))

                if not data: list_view.controls.append(ft.Text("还没有接单记录哦", text_align="center"))
        except Exception as e:
            print(e)
        if list_view.page: list_view.update()

    load_data()
    return ft.Column([
        ft.Container(padding=10, content=ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: on_back(None)),
            ft.Text("我参与的互助", size=20, weight="bold")
        ])),
        list_view
    ])