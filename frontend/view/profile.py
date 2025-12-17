import flet as ft
from api_client import APIClient
from view.my_help import MyHelpView
from view.my_posts import MyPostsView


# 【关键】这里必须接收所有参数，否则登录后跳转会报错 TypeError
def ProfileView(user_id, on_logout, show_msg, on_nav_to_help, on_nav_to_my_posts):
    content_col = ft.Column()

    def load_profile():
        try:
            res = APIClient.get_user_info(user_id)
            if res.status_code == 200:
                u = res.json()['data']
                stats = u['stats']

                header = ft.Container(
                    bgcolor="blue", padding=20, border_radius=15,
                    content=ft.Row([
                        ft.CircleAvatar(foreground_image_src=u['avatar'], radius=30),
                        ft.Column([ft.Text(u['username'], color="white", size=20, weight="bold"),
                                   ft.Text(f"联系: {u['contact']}", color="white70")]),
                        ft.Container(expand=True),
                        ft.Column([ft.Text(str(u['points']), color="yellow", size=24, weight="bold"),
                                   ft.Text("积分", color="white70")])
                    ])
                )

                stats_row = ft.Row([
                    ft.Column([ft.Text(str(stats['posts']), size=18, weight="bold"), ft.Text("发布", size=12)],
                              horizontal_alignment="center"),
                    ft.Column([ft.Text(str(stats['skills']), size=18, weight="bold"), ft.Text("技能", size=12)],
                              horizontal_alignment="center"),
                    ft.Column([ft.Text(str(stats['lost']), size=18, weight="bold"), ft.Text("失物", size=12)],
                              horizontal_alignment="center")
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND)

                content_col.controls = [
                    header,
                    ft.Container(height=20),
                    stats_row,
                    ft.Divider(height=30),
                    ft.ListTile(leading=ft.Icon(ft.Icons.HANDSHAKE, color="blue"), title=ft.Text("我参与的互助 (接单)"),
                                on_click=on_nav_to_help),
                    ft.ListTile(leading=ft.Icon(ft.Icons.LIST_ALT, color="orange"), title=ft.Text("我的发布管理"),
                                on_click=on_nav_to_my_posts),
                    ft.Divider(),
                    ft.ListTile(leading=ft.Icon(ft.Icons.EXIT_TO_APP, color="red"),
                                title=ft.Text("退出登录", color="red"), on_click=on_logout),
                ]
                if content_col.page: content_col.update()
        except Exception as e:
            show_msg(f"加载失败: {e}")

    load_profile()
    return ft.Container(padding=20, content=content_col)