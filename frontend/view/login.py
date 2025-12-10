import flet as ft
from api_client import APIClient


def LoginView(on_login_success, show_msg):
    login_user = ft.TextField(label="用户名", width=280)
    login_pass = ft.TextField(label="密码", password=True, can_reveal_password=True, width=280)
    login_contact = ft.TextField(label="联系方式 (注册必填)", visible=False, width=280)

    state = {"is_register": False}
    btn_action = ft.ElevatedButton("登录", bgcolor="blue", color="white", width=280)
    btn_toggle = ft.TextButton("没有账号？去注册")

    def toggle_mode(e):
        state["is_register"] = not state["is_register"]
        login_contact.visible = state["is_register"]
        btn_action.text = "立即注册" if state["is_register"] else "登录"
        btn_toggle.text = "已有账号？去登录" if state["is_register"] else "没有账号？去注册"
        e.page.update()

    def handle_auth(e):
        u, p, c = login_user.value, login_pass.value, login_contact.value
        if not u or not p: return show_msg("请输入账号密码")

        try:
            if state["is_register"]:
                res = APIClient.register(u, p, c)
                if res.status_code == 200:
                    show_msg("注册成功，请登录", "green")
                    toggle_mode(e)
                else:
                    show_msg(res.json().get('msg'))
            else:
                res = APIClient.login(u, p)
                if res.status_code == 200:
                    d = res.json()['data']
                    on_login_success(d)  # 回调主程序
                else:
                    show_msg(res.json().get('msg'))
        except Exception as ex:
            show_msg(str(ex))

    btn_action.on_click = handle_auth
    btn_toggle.on_click = toggle_mode

    return ft.Container(
        alignment=ft.alignment.center,
        content=ft.Column([
            ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color="blue"),
            ft.Text("校园互助", size=20, weight="bold"),
            ft.Container(height=20), login_user, login_pass, login_contact,
            ft.Container(height=10), btn_action, btn_toggle
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )