import flet as ft
from view.login import LoginView
from view.profile import ProfileView
from view.detail import DetailView
from view.home import HomeView


def main(page: ft.Page):
    page.title = "校园互助平台"
    page.window.width = 400
    page.window.height = 800
    page.bgcolor = "#f0f2f5"
    page.padding = 0

    # 全局状态
    current_user = {"id": None, "name": None}

    # 提示框
    snack_bar = ft.SnackBar(ft.Text(""))
    page.overlay.append(snack_bar)

    def show_msg(msg, color="red"):
        snack_bar.content.value = msg
        snack_bar.content.color = color
        snack_bar.open = True
        page.update()

    # 容器
    body = ft.Container(expand=True)

    # 导航回调
    def switch_tab(e):
        # 兼容：如果是 int (代码调用) 还是 Control (点击事件)
        idx = e if isinstance(e, int) else e.control.data

        # 更新底部图标颜色
        for i, btn in enumerate(nav_bar.content.controls):
            btn.icon_color = "blue" if i == idx else "grey"

        if idx == 0:  # 首页 (合并了技能和失物)
            body.content = home_view.get_main_view()
        elif idx == 1:  # 发布
            body.content = home_view.get_post_view(switch_tab)
        elif idx == 2:  # 个人中心
            if current_user['id']:
                body.content = ProfileView(current_user['id'], logout, show_msg)
            else:
                body.content = LoginView(login_success, show_msg)
        page.update()

    def login_success(user_data):
        current_user['id'] = user_data['user_id']
        current_user['name'] = user_data['username']
        show_msg(f"欢迎 {current_user['name']}", "green")
        switch_tab(2)  # 登录成功跳转到个人中心

    def logout(e):
        current_user['id'] = None
        switch_tab(2)  # 刷新回登录页

    def go_detail(item, category):
        body.content = DetailView(item, category, lambda e: switch_tab(0), show_msg)
        page.update()

    # 初始化 Views
    home_view = HomeView(page, show_msg, go_detail, lambda: current_user)

    # 底部导航 (减少为3个按钮)
    nav_bar = ft.Container(
        bgcolor="white", padding=10, border=ft.border.only(top=ft.BorderSide(1, "#e0e0e0")),
        content=ft.Row([
            ft.IconButton(ft.Icons.HOME, tooltip="首页", data=0, on_click=switch_tab),
            ft.IconButton(ft.Icons.ADD_CIRCLE, icon_size=40, tooltip="发布", data=1, on_click=switch_tab),
            ft.IconButton(ft.Icons.PERSON, tooltip="我的", data=2, on_click=switch_tab)
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
    )

    page.add(body, nav_bar)

    # 启动默认加载首页
    switch_tab(0)


if __name__ == "__main__":
    ft.app(target=main)