import flet as ft
from api_client import APIClient

def MyPostsView(user_id, on_back, show_msg):
    posts_list = ft.ListView(expand=True, spacing=10, padding=10)

    def finish_order(e):
        data = e.control.data
        try:
            res = APIClient.finish_order(data['id'], data['category'])
            if res.status_code == 200:
                show_msg("订单已确认完成", "green")
                load_data()
            else: show_msg("操作失败")
        except: show_msg("网络错误")

    def review_order(e):
        action = e.control.data['action']
        item_data = e.control.data['item']
        try:
            res = APIClient.review_order(item_data['id'], item_data['category'], action)
            if res.status_code == 200:
                show_msg(res.json().get('msg'), "green")
                load_data()
            else: show_msg(res.json().get('msg'))
        except: show_msg("网络错误")

    def delete_post(e):
        data = e.control.data
        APIClient.delete_item(data['id'], data['category'])
        load_data()

    def load_data():
        posts_list.controls.clear()
        try:
            res = APIClient.get_user_posts(user_id)
            items = res.json().get('data', [])
            for item in items:
                status = item.get('status', 0)
                if status == 0:
                    status_widget = ft.Container(content=ft.Text("等待接单", size=10, color="white"), bgcolor="grey", padding=5, border_radius=4)
                    action_widget = ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="red", data=item, on_click=delete_post)
                elif status == 1:
                    status_widget = ft.Container(content=ft.Text("进行中", size=10, color="white"), bgcolor="blue", padding=5, border_radius=4)
                    action_widget = ft.ElevatedButton("确认完成", height=30, style=ft.ButtonStyle(padding=5), data=item, on_click=finish_order)
                else:
                    status_widget = ft.Container(content=ft.Text("已完成", size=10, color="white"), bgcolor="green", padding=5, border_radius=4)
                    review_s = item.get('review', 0)
                    if review_s == 0:
                        action_widget = ft.Row([
                            ft.IconButton(ft.Icons.THUMB_UP, icon_color="orange", tooltip="打赏", data={"action":"reward", "item":item}, on_click=review_order),
                            ft.IconButton(ft.Icons.THUMB_DOWN, icon_color="grey", tooltip="投诉", data={"action":"complain", "item":item}, on_click=review_order)
                        ], spacing=0)
                    else:
                        action_widget = ft.Text("已评价", size=12, color="orange")

                posts_list.controls.append(ft.Container(
                    bgcolor="white", padding=10, border_radius=10,
                    content=ft.Row([
                        ft.Image(src=item['image'], width=60, height=60, border_radius=5),
                        ft.Container(expand=True, content=ft.Column([
                            ft.Row([status_widget, ft.Text(item['create_time'], size=10, color="grey")], alignment="spaceBetween"),
                            ft.Text(item['title'], size=16, weight="bold", max_lines=1),
                        ], spacing=5)),
                        action_widget
                    ])
                ))
            if not items: posts_list.controls.append(ft.Text("暂无记录", text_align="center"))
        except: pass
        if posts_list.page: posts_list.update()

    load_data()
    return ft.Column([
        ft.Container(padding=10, content=ft.Row([ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: on_back(None)), ft.Text("我的发布管理", size=20, weight="bold")])),
        posts_list
    ])