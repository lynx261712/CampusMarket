import flet as ft
# 这些引用是正确的，因为 main.py 同级目录下有 view 文件夹
from view.login import LoginView
from view.profile import ProfileView
from view.detail import DetailView
from view.home import HomeView
from view.my_help import MyHelpView
from view.my_posts import MyPostsView


def main(page: ft.Page):
    # 页面基础设置
    page.title = "校园互助平台"
    page.window.width = 400
    page.window.height = 800
    page.bgcolor = "#f0f2f5"
    page.padding = 0

    # 全局状态
    current_user = {"id": None, "name": None}

    # 全局提示框
    snack_bar = ft.SnackBar(ft.Text(""))
    page.overlay.append(snack_bar)

    def show_msg(msg, color="red"):
        snack_bar.content.value = msg
        snack_bar.content.color = color
        snack_bar.open = True
        page.update()

    body = ft.Container(expand=True)

    # ================= 路由与回调 =================

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
        # 跳转详情页
        body.content = DetailView(item, category, lambda e: switch_tab(0), show_msg, current_user)
        page.update()

    def go_my_help(e):
        # 跳转'我参与的互助'
        body.content = MyHelpView(current_user['id'], lambda e: switch_tab(2), show_msg)
        page.update()

    def go_my_posts(e):
        # 跳转'我的发布管理'
        body.content = MyPostsView(current_user['id'], lambda e: switch_tab(2), show_msg)
        page.update()

    def switch_tab(e):
        idx = e if isinstance(e, int) else e.control.data

        # 更新底部导航高亮
        for i, btn in enumerate(nav_bar.content.controls):
            btn.icon_color = "blue" if i == idx else "grey"

        # 页面切换逻辑
        if idx == 0:
            body.content = home_view.get_main_view()
        elif idx == 1:
            body.content = home_view.get_post_view(on_success_nav=switch_tab)
        elif idx == 2:
            if current_user['id']:
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

    # 初始化首页视图
    home_view = HomeView(page, show_msg, go_detail, lambda: current_user)

    # 底部导航栏
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