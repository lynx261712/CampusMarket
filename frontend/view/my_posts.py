import flet as ft
from api_client import APIClient


def MyPostsView(user_id, on_back, show_msg):
    # 列表容器
    posts_list = ft.ListView(expand=True, spacing=10, padding=10)

    # --- 业务逻辑 (从 ProfileView 移过来的) ---
    def finish_order(e):
        data = e.control.data
        try:
            res = APIClient.finish_order(data['id'], data['category'])
            if res.status_code == 200:
                show_msg("订单已确认完成", "green")
                load_data()  # 刷新列表
            else:
                show_msg("操作失败")
        except:
            show_msg("网络错误")

    def review_order(e):
        action = e.control.data['action']
        item_data = e.control.data['item']
        try:
            res = APIClient.review_order(item_data['id'], item_data['category'], action)
            if res.status_code == 200:
                show_msg(res.json().get('msg'), "green")
                load_data()
            else:
                show_msg(res.json().get('msg'))
        except:
            show_msg("网络错误")

    def delete_post(e):
        data = e.control.data
        APIClient.delete_item(data['id'], data['category'])
        load_data()

    # --- 加载数据 ---
    def load_data():
        posts_list.controls.clear()
        try:
            res = APIClient.get_user_posts(user_id)
            items = res.json().get('data', [])
            for item in items:
                # 状态处理逻辑
                status = item.get('status', 0)

                # 1. 状态标签和操作按钮生成
                if status == 0:
                    status_widget = ft.Container(content=ft.Text("等待接单", size=10, color="white"), bgcolor="grey",
                                                 padding=5, border_radius=4)
                    action_widget = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="red", data=item,
                                                  on_click=delete_post)
                elif status == 1:
                    status_widget = ft.Container(content=ft.Text("进行中", size=10, color="white"), bgcolor="blue",
                                                 padding=5, border_radius=4)
                    # 进行中 -> 显示确认完成按钮
                    action_widget = ft.ElevatedButton("确认完成", height=30, style=ft.ButtonStyle(padding=5), data=item,
                                                      on_click=finish_order)
                else:  # status == 2
                    status_widget = ft.Container(content=ft.Text("已完成", size=10, color="white"), bgcolor="green",
                                                 padding=5, border_radius=4)
                    # 已完成 -> 显示评价或已评价
                    review_s = item.get('review', 0)
                    if review_s == 0:
                        action_widget = ft.Row([
                            ft.IconButton(ft.Icons.THUMB_UP, icon_color="orange", tooltip="打赏",
                                          data={"action": "reward", "item": item}, on_click=review_order),
                            ft.IconButton(ft.Icons.THUMB_DOWN, icon_color="grey", tooltip="投诉",
                                          data={"action": "complain", "item": item}, on_click=review_order)
                        ], spacing=0)
                    else:
                        txt = "已打赏" if review_s == 1 else "已投诉"
                        col = "orange" if review_s == 1 else "red"
                        action_widget = ft.Text(txt, size=12, color=col)

                # 2. 组装卡片
                posts_list.controls.append(ft.Container(
                    bgcolor="white", padding=10, border_radius=10,
                    content=ft.Row([
                        ft.Image(src=item['image'], width=60, height=60, border_radius=5),
                        ft.Container(expand=True, content=ft.Column([
                            ft.Row([status_widget, ft.Text(item['create_time'], size=10, color="grey")],
                                   alignment="spaceBetween"),
                            ft.Text(item['title'], size=16, weight="bold", max_lines=1),
                        ], spacing=5)),
                        action_widget
                    ])
                ))
            if not items: posts_list.controls.append(ft.Text("您还没有发布过内容", text_align="center", color="grey"))
        except Exception as e:
            print(e)
            posts_list.controls.append(ft.Text("加载失败", text_align="center"))

        if posts_list.page: posts_list.update()

    load_data()

    return ft.Column([
        ft.Container(padding=10, content=ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: on_back(None)),
            ft.Text("我的发布管理", size=20, weight="bold")
        ])),
        posts_list
    ])