import flet as ft
from view.login import LoginView
from view.profile import ProfileView
from view.detail import DetailView
from view.home import HomeView
from view.my_help import MyHelpView
from view.my_posts import MyPostsView  # 【新增】导入新页面


def main(page: ft.Page):
    # --- 页面基础设置 ---
    page.title = "校园互助平台"
    page.window.width = 400
    page.window.height = 800
    page.bgcolor = "#f0f2f5"
    page.padding = 0

    # 全局变量
    current_user = {"id": None, "name": None}

    # 提示框
    snack_bar = ft.SnackBar(ft.Text(""))
    page.overlay.append(snack_bar)

    def show_msg(msg, color="red"):
        snack_bar.content.value = msg
        snack_bar.content.color = color
        snack_bar.open = True
        page.update()

    body = ft.Container(expand=True)

    # ==========================================
    #  导航与回调
    # ==========================================

    def login_success(user_data):
        current_user['id'] = user_data['user_id']
        current_user['name'] = user_data['username']
        show_msg(f"欢迎 {current_user['name']}", "green")
        switch_tab(2)

    def logout(e):
        current_user['id'] = None
        current_user['name'] = None
        show_msg("已退出登录", "green")
        switch_tab(2)

    def go_detail(item, category):
        body.content = DetailView(item, category, lambda e: switch_tab(0), show_msg, current_user)
        page.update()

    def go_my_help(e):
        """跳转到'我的帮助'"""
        # 【修改】传入 show_msg
        body.content = MyHelpView(current_user['id'], lambda e: switch_tab(2), show_msg)
        page.update()

    def go_my_posts(e):
        """【新增】跳转到'我的发布管理'"""
        body.content = MyPostsView(
            user_id=current_user['id'],
            on_back=lambda e: switch_tab(2),  # 返回个人中心
            show_msg=show_msg
        )
        page.update()

    def switch_tab(e):
        idx = e if isinstance(e, int) else e.control.data

        # 更新底部导航颜色
        for i, btn in enumerate(nav_bar.content.controls):
            btn.icon_color = "blue" if i == idx else "grey"

        # 路由逻辑
        if idx == 0:  # 首页
            body.content = home_view.get_main_view()

        elif idx == 1:  # 发布页
            body.content = home_view.get_post_view(on_success_nav=switch_tab)

        elif idx == 2:  # 个人中心
            if current_user['id']:
                # 【关键修改】传递所有跳转回调
                body.content = ProfileView(
                    user_id=current_user['id'],
                    on_logout=logout,
                    show_msg=show_msg,
                    on_nav_to_help=go_my_help,
                    on_nav_to_my_posts=go_my_posts
                )
            else:
                body.content = LoginView(login_success, show_msg)

        page.update()

    # 初始化
    home_view = HomeView(page, show_msg, go_detail, lambda: current_user)

    nav_bar = ft.Container(
        bgcolor="white", padding=10, border=ft.border.only(top=ft.BorderSide(1, "#e0e0e0")),
        content=ft.Row([
            ft.IconButton(ft.Icons.HOME, tooltip="首页", data=0, on_click=switch_tab),
            ft.IconButton(ft.Icons.ADD_CIRCLE, icon_size=40, tooltip="发布", data=1, on_click=switch_tab),
            ft.IconButton(ft.Icons.PERSON, tooltip="我的", data=2, on_click=switch_tab)
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
    )

    page.add(body, nav_bar)
    switch_tab(0)


if __name__ == "__main__":
    ft.app(target=main)