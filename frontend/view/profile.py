import flet as ft
from api_client import APIClient


def ProfileView(user_id, on_logout, show_msg):
    content_col = ft.Column()
    my_posts_list = ft.ListView(expand=True, spacing=10, padding=20)

    # --- 删除发布的逻辑 ---
    def delete_post(e):
        data = e.control.data
        APIClient.delete_item(data['id'], data['category'])
        load_my_posts(None)  # 刷新列表

    # --- 加载“我的发布”逻辑 ---
    def load_my_posts(e):
        my_posts_list.controls.clear()
        try:
            res = APIClient.get_user_posts(user_id)
            items = res.json().get('data', [])
            for item in items:
                my_posts_list.controls.append(ft.Container(
                    bgcolor="white", padding=10, border_radius=10,
                    shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.1, "black")),
                    content=ft.Row([
                        ft.Image(src=item['image'], width=60, height=60, border_radius=5),
                        ft.Container(expand=True, content=ft.Column([
                            ft.Row([ft.Container(content=ft.Text(item['tag'], size=10, color="white"),
                                                 bgcolor=item['color'], padding=5, border_radius=4),
                                    ft.Text(item['create_time'], size=10, color="grey")],
                                   alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(item['title'], size=16, weight="bold", max_lines=1),
                        ], spacing=5)),
                        ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="red",
                                      data={"id": item['id'], "category": item['category']}, on_click=delete_post)
                    ])
                ))
            if not items:
                my_posts_list.controls.append(ft.Text("暂无记录", text_align="center", color="grey"))

        except:
            pass

        content_col.controls = [
            ft.Container(padding=10, content=ft.Row(
                [ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: load_profile()),
                 ft.Text("我的发布", size=20, weight="bold")])),
            my_posts_list
        ]
        if content_col.page: content_col.update()

    # --- 加载个人主页逻辑 ---
    def load_profile():
        try:
            res = APIClient.get_user_info(user_id)
            if res.status_code == 200:
                u = res.json()['data']
                stats = u['stats']

                # --- 【新增】编辑资料弹窗逻辑 ---
                def show_edit_dialog(e):
                    edit_name = ft.TextField(label="用户名", value=u['username'])
                    edit_contact = ft.TextField(label="联系方式", value=u['contact'])

                    def save_info(e):
                        try:
                            # 调用 API 更新
                            resp = APIClient.update_user({
                                "user_id": user_id,
                                "username": edit_name.value,
                                "contact": edit_contact.value
                            })
                            if resp.status_code == 200:
                                show_msg("修改成功", "green")
                                e.page.dialog.open = False
                                e.page.update()
                                load_profile()  # 重新加载以显示新信息
                            else:
                                show_msg("修改失败")
                        except Exception as ex:
                            show_msg(str(ex))

                    # 弹出对话框
                    e.page.dialog = ft.AlertDialog(
                        title=ft.Text("编辑资料"),
                        content=ft.Column([edit_name, edit_contact], height=150),
                        actions=[ft.ElevatedButton("保存", on_click=save_info)]
                    )
                    e.page.dialog.open = True
                    e.page.update()

                # -----------------------------------

                # 头部卡片 (添加了 ink=True 和 on_click)
                header = ft.Container(
                    bgcolor="blue", padding=20, border_radius=15,
                    ink=True,  # 点击水波纹效果
                    on_click=show_edit_dialog,  # 【关键】绑定点击事件
                    content=ft.Row([
                        ft.CircleAvatar(foreground_image_src=u['avatar'], radius=30),
                        ft.Column([
                            ft.Row([
                                ft.Text(u['username'], color="white", size=20, weight="bold"),
                                ft.Icon(ft.Icons.EDIT, size=16, color="white70")  # 加个小图标提示可编辑
                            ]),
                            ft.Text(f"联系: {u['contact']}", color="white70")
                        ]),
                        ft.Container(expand=True),
                        ft.Column([
                            ft.Text(str(u['points']), color="yellow", size=24, weight="bold"),
                            ft.Text("积分", color="white70")
                        ])
                    ])
                )

                # 统计行
                stats_row = ft.Row([
                    ft.Column([ft.Text(str(stats['posts']), size=18, weight="bold"), ft.Text("发布", size=12)],
                              horizontal_alignment="center"),
                    ft.Column([ft.Text(str(stats['skills']), size=18, weight="bold"), ft.Text("技能", size=12)],
                              horizontal_alignment="center"),
                    ft.Column([ft.Text(str(stats['lost']), size=18, weight="bold"), ft.Text("失物", size=12)],
                              horizontal_alignment="center")
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND)

                content_col.controls = [
                    header, ft.Container(height=20), stats_row, ft.Divider(height=20),
                    ft.ListTile(leading=ft.Icon(ft.Icons.LIST_ALT), title=ft.Text("我的发布记录"),
                                on_click=load_my_posts),
                    ft.ListTile(leading=ft.Icon(ft.Icons.EXIT_TO_APP, color="red"),
                                title=ft.Text("退出登录", color="red"), on_click=on_logout),
                ]

                # 安全刷新
                if content_col.page:
                    content_col.update()

        except Exception as e:
            show_msg(f"加载失败: {e}")

    # 初始化
    load_profile()
    return ft.Container(padding=20, content=content_col)