import flet as ft
from api_client import APIClient


# 【关键修改】增加了 on_nav_to_my_posts 参数
def ProfileView(user_id, on_logout, show_msg, on_nav_to_help, on_nav_to_my_posts):
    content_col = ft.Column()

    def load_profile():
        try:
            res = APIClient.get_user_info(user_id)
            if res.status_code == 200:
                u = res.json()['data']
                stats = u['stats']

                # 头部用户信息
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

                # 统计数据行
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

                    # 菜单区
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.HANDSHAKE, color="blue"),
                        title=ft.Text("我参与的互助 (接单)"),
                        subtitle=ft.Text("查看我帮助他人的订单状态"),
                        on_click=on_nav_to_help
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.LIST_ALT, color="orange"),
                        title=ft.Text("我的发布管理"),
                        subtitle=ft.Text("管理我发布的内容、确认完成与评价"),
                        # 【关键】点击跳转到新页面
                        on_click=on_nav_to_my_posts
                    ),
                    ft.Divider(),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.EXIT_TO_APP, color="red"),
                        title=ft.Text("退出登录", color="red"),
                        on_click=on_logout
                    ),
                ]
                if content_col.page: content_col.update()
        except Exception as e:
            show_msg(f"加载失败: {e}")

    load_profile()
    return ft.Container(padding=20, content=content_col)