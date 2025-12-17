import flet as ft
from api_client import APIClient


def ProfileView(user_id, on_logout, show_msg, on_nav_to_help, on_nav_to_my_posts):
    content_col = ft.Column()

    # ==========================================
    #  1. 定义修改文本信息的弹窗 (改名/改联系方式)
    # ==========================================
    input_name = ft.TextField(label="新用户名")
    input_contact = ft.TextField(label="新联系方式")

    def confirm_update_text(e):
        if not input_name.value or not input_contact.value:
            return show_msg("内容不能为空")

        try:
            res = APIClient.update_user(user_id, username=input_name.value, contact=input_contact.value)
            if res.status_code == 200:
                show_msg("信息修改成功", "green")
                e.page.dialog.open = False
                e.page.update()
                load_profile()  # 刷新界面显示
            else:
                show_msg(f"失败: {res.json().get('msg')}")
        except Exception as ex:
            show_msg(str(ex))

    # 定义弹窗组件
    edit_dialog = ft.AlertDialog(
        title=ft.Text("修改个人信息"),
        content=ft.Column([
            ft.Text("请输入新的信息:", size=14, color="grey"),
            input_name,
            input_contact
        ], height=180, tight=True),
        actions=[
            ft.TextButton("取消", on_click=lambda e: setattr(e.page.dialog, 'open', False) or e.page.update()),
            ft.TextButton("保存", on_click=confirm_update_text),
        ]
    )

    def open_edit_dialog(e):
        e.page.dialog = edit_dialog
        edit_dialog.open = True
        e.page.update()

    # ==========================================
    #  2. 定义头像修改逻辑 (点击头像选择文件)
    # ==========================================
    def on_avatar_picked(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            try:
                show_msg("正在上传头像...", "blue")
                res = APIClient.update_user(user_id, avatar_path=file_path)
                if res.status_code == 200:
                    show_msg("头像更新成功", "green")
                    load_profile()  # 刷新
                else:
                    show_msg("上传失败")
            except Exception as ex:
                show_msg(str(ex))

    avatar_picker = ft.FilePicker(on_result=on_avatar_picked)

    # ==========================================
    #  3. 页面加载与布局构建
    # ==========================================
    def load_profile():
        # 挂载必要的 Overlay 组件
        if content_col.page and avatar_picker not in content_col.page.overlay:
            content_col.page.overlay.append(avatar_picker)

        try:
            res = APIClient.get_user_info(user_id)
            if res.status_code == 200:
                u = res.json()['data']
                stats = u['stats']

                # 预填旧数据到输入框
                input_name.value = u['username']
                input_contact.value = u['contact']

                # --- 顶部蓝色卡片 ---
                # 头像部分：保留点击头像修改图片的功能
                avatar_widget = ft.GestureDetector(
                    on_tap=lambda _: avatar_picker.pick_files(allow_multiple=False,
                                                              allowed_extensions=["jpg", "png", "jpeg"]),
                    content=ft.Stack([
                        ft.CircleAvatar(foreground_image_src=u['avatar'], radius=35),
                        # 相机小图标
                        ft.Container(
                            content=ft.Icon(ft.Icons.CAMERA_ALT, size=14, color="white"),
                            bgcolor=ft.colors.with_opacity(0.6, "black"),
                            border_radius=15, padding=3,
                            bottom=0, right=0
                        )
                    ], width=70, height=70)
                )

                header = ft.Container(
                    bgcolor="blue", padding=20, border_radius=15,
                    content=ft.Row([
                        avatar_widget,
                        ft.Container(width=10),
                        ft.Column([
                            ft.Text(u['username'], color="white", size=22, weight="bold"),
                            ft.Text(f"联系: {u['contact']}", color="white70", size=14)
                        ], spacing=5),
                        ft.Container(expand=True),
                        ft.Column([
                            ft.Text(str(u['points']), color="yellow", size=24, weight="bold"),
                            ft.Text("积分", color="white70", size=12)
                        ], horizontal_alignment="center")
                    ])
                )

                # --- 统计数据行 ---
                stats_row = ft.Row([
                    ft.Column([ft.Text(str(stats['posts']), size=18, weight="bold"), ft.Text("发布", size=12)],
                              horizontal_alignment="center"),
                    ft.Column([ft.Text(str(stats['skills']), size=18, weight="bold"), ft.Text("技能", size=12)],
                              horizontal_alignment="center"),
                    ft.Column([ft.Text(str(stats['lost']), size=18, weight="bold"), ft.Text("失物", size=12)],
                              horizontal_alignment="center")
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND)

                # --- 菜单列表 ---
                content_col.controls = [
                    header,
                    ft.Container(height=20),
                    stats_row,
                    ft.Divider(height=20, color="transparent"),

                    # 功能菜单
                    ft.Container(
                        bgcolor="white", border_radius=10, padding=5,
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.HANDSHAKE, color="blue"),
                                title=ft.Text("我参与的互助 (接单)"),
                                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, color="grey"),
                                on_click=on_nav_to_help
                            ),
                            ft.Divider(height=1),
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.LIST_ALT, color="orange"),
                                title=ft.Text("我的发布管理"),
                                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, color="grey"),
                                on_click=on_nav_to_my_posts
                            ),
                            ft.Divider(height=1),
                            # 【新增】专门的修改信息按钮
                            ft.ListTile(
                                leading=ft.Icon(ft.Icons.EDIT_SQUARE, color="teal"),
                                title=ft.Text("修改个人信息"),
                                subtitle=ft.Text("修改用户名、联系方式", size=12),
                                trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, color="grey"),
                                on_click=open_edit_dialog
                            ),
                        ], spacing=0)
                    ),

                    ft.Container(height=20),
                    # 退出按钮单独放
                    ft.Container(
                        bgcolor="white", border_radius=10,
                        content=ft.ListTile(
                            leading=ft.Icon(ft.Icons.EXIT_TO_APP, color="red"),
                            title=ft.Text("退出登录", color="red"),
                            on_click=on_logout
                        )
                    )
                ]
                if content_col.page: content_col.update()
        except Exception as e:
            print(f"Profile Error: {e}")
            show_msg(f"加载失败: {e}")

    # 包装组件以利用生命周期
    wrapper = ft.Container(padding=15, content=content_col)

    # 【核心修复点】这里去掉了参数 e
    def on_mount():
        load_profile()

    wrapper.did_mount = on_mount
    return wrapper