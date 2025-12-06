import flet as ft
import requests
import os

# 1. 网络环境配置
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
API_BASE_URL = "http://127.0.0.1:5000/api"


def main(page: ft.Page):
    # --- 页面基础设置 ---
    page.title = "校园互助平台"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 400
    page.window.height = 800
    page.padding = 0
    page.bgcolor = "#f0f2f5"

    # 全局变量
    current_user = {"id": None, "name": None}

    # 注册提示框
    snack_bar = ft.SnackBar(ft.Text(""))
    page.overlay.append(snack_bar)

    def show_msg(msg, color="red"):
        snack_bar.content.value = msg
        snack_bar.content.color = color
        snack_bar.open = True
        page.update()

    # ==========================================
    # PART 1: 预定义 UI 组件
    # ==========================================

    # 列表容器
    skill_grid = ft.GridView(expand=True, runs_count=2, max_extent=200, child_aspect_ratio=0.7, spacing=10,
                             run_spacing=10, padding=10)
    lost_grid = ft.GridView(expand=True, runs_count=1, child_aspect_ratio=1.8, spacing=10, run_spacing=10, padding=10)

    # 个人中心容器
    profile_content = ft.Column([])
    my_posts_list = ft.ListView(expand=True, spacing=10, padding=20)

    # 搜索框
    search_bar = ft.TextField(hint_text="搜索...", prefix_icon=ft.Icons.SEARCH, border_radius=20, height=40,
                              content_padding=10, text_size=14)
    search_view = ft.Container(content=search_bar, padding=ft.padding.only(left=15, right=15, top=10, bottom=5),
                               bgcolor="white")

    # 导航按钮
    btn_skill = ft.IconButton(ft.Icons.TOKEN, tooltip="技能银行", data=0)
    btn_lost = ft.IconButton(ft.Icons.SEARCH, tooltip="失物招领", data=1)
    btn_add = ft.IconButton(ft.Icons.ADD_CIRCLE, icon_size=40, data=2)
    btn_user = ft.IconButton(ft.Icons.PERSON, tooltip="我的", data=3)

    # 详情页容器
    detail_view = ft.Container(bgcolor="white")

    # 登录页容器
    login_view = ft.Container(alignment=ft.alignment.center)

    # 发布页组件
    input_title = ft.TextField(label="标题 (简短清晰)", border_color="blue")
    input_desc = ft.TextField(label="详细描述 (特征/具体需求)", multiline=True, min_lines=3)
    input_loc = ft.TextField(label="地点 (失物/拾获地点)", icon=ft.Icons.LOCATION_ON)
    input_cost = ft.Dropdown(
        label="悬赏/代价", icon=ft.Icons.MONETIZATION_ON,
        options=[ft.dropdown.Option("免费/互免"), ft.dropdown.Option("2 积分"), ft.dropdown.Option("一杯奶茶"),
                 ft.dropdown.Option("面议")],
        visible=False
    )
    type_chips = ft.RadioGroup(
        content=ft.Row([
            ft.Container(content=ft.Column([
                ft.Text("失物招领", size=12, color="grey"),
                ft.Row([ft.Radio(value="lost", label="🆘 丢东西", fill_color="red"),
                        ft.Radio(value="found", label="✨ 捡到了", fill_color="green")])
            ])),
            ft.VerticalDivider(width=20),
            ft.Container(content=ft.Column([
                ft.Text("技能银行", size=12, color="grey"),
                ft.Row([ft.Radio(value="skill_supply", label="💪 提供技能", fill_color="blue"),
                        ft.Radio(value="skill_need", label="🙏 急需帮助", fill_color="orange")])
            ]))
        ], scroll=ft.ScrollMode.AUTO)
    )
    type_chips.value = "lost"

    # ==========================================
    # PART 2: 核心逻辑函数
    # ==========================================

    # --- 2.1 卡片创建 ---
    def create_skill_card(item):
        is_supply = (item.get('type', 1) == 1)
        tag_text, tag_color = ("我能提供", "blue") if is_supply else ("急需帮助", "orange")
        return ft.Container(
            bgcolor="white", border_radius=10,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.1, "black")),
            content=ft.Column([
                ft.Image(src=item['image'], width=float("inf"), height=110, fit=ft.ImageFit.COVER,
                         border_radius=ft.border_radius.only(top_left=10, top_right=10)),
                ft.Container(padding=8, content=ft.Column([
                    ft.Container(content=ft.Text(tag_text, size=10, color="white", weight="bold"), bgcolor=tag_color,
                                 padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4),
                    ft.Text(item['title'], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, size=14, weight="bold"),
                    ft.Text(f"需: {item['cost']}", size=12, color="red", weight="bold"),
                ], spacing=5))
            ], spacing=0),
            on_click=lambda e: show_detail(item, "skill")
        )

    def create_lost_card(item):
        is_found = (item.get('type', 0) == 1)
        tag_text, tag_color = ("✨ 捡到了", "green") if is_found else ("🆘 丢东西", "red")
        return ft.Container(
            bgcolor="white", border_radius=10, padding=10,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.colors.with_opacity(0.1, "black")),
            content=ft.Row([
                ft.Image(src=item['image'], width=100, height=100, fit=ft.ImageFit.COVER, border_radius=8),
                ft.Container(expand=True, content=ft.Column([
                    ft.Row([ft.Container(content=ft.Text(tag_text, size=11, color="white"), bgcolor=tag_color,
                                         padding=ft.padding.symmetric(horizontal=6, vertical=2), border_radius=4),
                            ft.Text(item['time'], size=10, color="grey")],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Text(item['title'], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, size=16, weight="bold"),
                    ft.Text(item['desc'], max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, size=12, color="grey"),
                    ft.Row([ft.Icon(ft.Icons.LOCATION_ON, size=12, color="blue"),
                            ft.Text(item['location'], size=12, color="blue")])
                ], spacing=3, alignment=ft.MainAxisAlignment.START))
            ]),
            on_click=lambda e: show_detail(item, "lost")
        )

    # --- 2.2 数据加载 ---
    def load_data(endpoint, grid, card_creator):
        grid.controls.clear()
        try:
            kw = search_bar.value or ""
            res = requests.get(f"{API_BASE_URL}/{endpoint}", params={"q": kw}, timeout=3)
            if res.status_code == 200:
                data = res.json().get('data', [])
                for item in data: grid.controls.append(card_creator(item))
                if not data: grid.controls.append(
                    ft.Column([ft.Icon(ft.Icons.SEARCH_OFF, color="grey"), ft.Text("无内容", color="grey")],
                              alignment=ft.MainAxisAlignment.CENTER))
            page.update()
        except Exception as e:
            print(e)

    def do_search(e):
        if btn_skill.icon_color == "blue":
            load_data("skills", skill_grid, create_skill_card)
        elif btn_lost.icon_color == "blue":
            load_data("lost-items", lost_grid, create_lost_card)

    search_bar.on_submit = do_search

    # --- 2.3 详情页逻辑 ---
    def show_detail(item, category):
        detail_img = ft.Image(src=item['image'], width=float("inf"), height=200, fit=ft.ImageFit.COVER)

        btn_get_contact = ft.ElevatedButton("获取联系方式", bgcolor="blue", color="white", width=float("inf"))

        def get_contact_api(e):
            try:
                res = requests.post(f"{API_BASE_URL}/interact", json={"item_id": item['id'], "category": category})
                if res.status_code == 200:
                    page.dialog = ft.AlertDialog(title=ft.Text("联系方式"),
                                                 content=ft.Text(res.json()['data']['contact'], size=20, weight="bold",
                                                                 color="blue"))
                    page.dialog.open = True;
                    page.update()
            except:
                show_msg("获取失败")

        btn_get_contact.on_click = get_contact_api

        content_val = f"代价: {item.get('cost')}" if category == "skill" else f"描述: {item.get('desc')}"
        meta = [ft.Icon(ft.Icons.PERSON), ft.Text(item.get('user'))] if category == "skill" else [
            ft.Icon(ft.Icons.LOCATION_ON), ft.Text(item.get('location'))]

        detail_view.content = ft.Column([
            ft.Stack([
                detail_img,
                ft.IconButton(ft.Icons.ARROW_BACK, icon_color="white",
                              on_click=lambda e: switch_tab(0 if category == "skill" else 1), left=5, top=5)
            ]),
            ft.Container(padding=20, content=ft.Column([
                ft.Text(item['title'], size=22, weight="bold"), ft.Divider(),
                ft.Text(content_val, size=16), ft.Row(meta), ft.Container(height=20), btn_get_contact
            ]))
        ])
        body.content = detail_view
        page.update()

    # --- 2.4 个人中心与我的发布 ---
    def delete_post(e):
        pid = e.control.data['id'];
        cat = e.control.data['category']
        requests.post(f"{API_BASE_URL}/delete", json={"id": pid, "category": cat})
        show_my_posts(None)

    def show_my_posts(e):
        my_posts_list.controls.clear()
        try:
            res = requests.get(f"{API_BASE_URL}/user/posts/{current_user['id']}")
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
                            ft.Text(item['title'], size=16, weight="bold", max_lines=1,
                                    overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(item['info'], size=12, color="grey", max_lines=1)
                        ], spacing=5)),
                        ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_color="red",
                                      data={"id": item['id'], "category": item['category']}, on_click=delete_post)
                    ])
                ))
            if not items: my_posts_list.controls.append(ft.Text("暂无记录", text_align="center"))
        except:
            pass

        body.content = ft.Column([
            ft.Container(padding=10, content=ft.Row(
                [ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda e: render_profile()),
                 ft.Text("我的发布", size=20, weight="bold")])),
            my_posts_list
        ])
        page.update()

    def logout(e):
        current_user['id'] = None
        body.content = login_view
        page.update()

    def render_profile():
        try:
            res = requests.get(f"{API_BASE_URL}/user/{current_user['id']}")
            if res.status_code == 200:
                u = res.json()['data']
                stats = u['stats']

                edit_name = ft.TextField(label="用户名", value=u['username'])
                edit_contact = ft.TextField(label="联系方式", value=u['contact'])

                def save_info(e):
                    requests.post(f"{API_BASE_URL}/user/update",
                                  json={"user_id": current_user['id'], "username": edit_name.value,
                                        "contact": edit_contact.value})
                    page.dialog.open = False;
                    current_user['name'] = edit_name.value;
                    render_profile()

                def show_edit(e):
                    page.dialog = ft.AlertDialog(title=ft.Text("编辑资料"),
                                                 content=ft.Column([edit_name, edit_contact], height=150),
                                                 actions=[ft.ElevatedButton("保存", on_click=save_info)])
                    page.dialog.open = True;
                    page.update()

                profile_content.controls = [
                    ft.Container(bgcolor="blue", padding=20, border_radius=15, ink=True, on_click=show_edit,
                                 content=ft.Row([
                                     ft.CircleAvatar(foreground_image_src=u['avatar'], radius=30),
                                     ft.Column([ft.Row([ft.Text(u['username'], color="white", size=20, weight="bold"),
                                                        ft.Icon(ft.Icons.EDIT, size=14, color="white70")]),
                                                ft.Text(f"ID: {u['id']}", color="white70"),
                                                ft.Text(f"联系: {u['contact']}", color="white70")]),
                                     ft.Container(expand=True), ft.Column(
                                         [ft.Text(str(u['points']), color="yellow", size=24, weight="bold"),
                                          ft.Text("积分", color="white70")])
                                 ])),
                    ft.Container(height=20),
                    ft.Row([
                        ft.Column([ft.Text(str(stats['posts']), size=18, weight="bold"), ft.Text("发布", size=12)],
                                  horizontal_alignment="center"),
                        ft.Column([ft.Text(str(stats['skills']), size=18, weight="bold"), ft.Text("技能", size=12)],
                                  horizontal_alignment="center"),
                        ft.Column([ft.Text(str(stats['lost']), size=18, weight="bold"), ft.Text("失物", size=12)],
                                  horizontal_alignment="center")
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                    ft.Divider(height=20),
                    ft.ListTile(leading=ft.Icon(ft.Icons.LIST_ALT), title=ft.Text("我的发布记录"),
                                on_click=show_my_posts),
                    ft.ListTile(leading=ft.Icon(ft.Icons.SETTINGS), title=ft.Text("设置"),
                                on_click=lambda e: show_msg("开发中...")),
                    ft.ListTile(leading=ft.Icon(ft.Icons.EXIT_TO_APP, color="red"),
                                title=ft.Text("退出登录", color="red"), on_click=logout),
                ]
                body.content = ft.Container(padding=20, content=profile_content)
                page.update()
        except Exception as e:
            show_msg(f"加载失败: {e}")

    # --- 2.5 登录逻辑 ---
    login_user = ft.TextField(label="用户名", width=280)
    login_pass = ft.TextField(label="密码", password=True, can_reveal_password=True, width=280)
    login_contact = ft.TextField(label="联系方式 (注册必填)", visible=False, width=280)

    auth_state = {"is_register": False}

    def toggle_mode(e):
        auth_state["is_register"] = not auth_state["is_register"]
        login_contact.visible = auth_state["is_register"]
        btn_login_action.text = "立即注册" if auth_state["is_register"] else "登录"
        btn_toggle_mode.text = "已有账号？去登录" if auth_state["is_register"] else "没有账号？去注册"
        page.update()

    def handle_auth(e):
        u, p, c = login_user.value, login_pass.value, login_contact.value
        if not u or not p: return show_msg("请输入账号密码")
        endpoint = "register" if auth_state["is_register"] else "login"
        payload = {"username": u, "password": p}
        if auth_state["is_register"]: payload["contact"] = c

        try:
            res = requests.post(f"{API_BASE_URL}/{endpoint}", json=payload)
            if res.status_code == 200:
                if auth_state["is_register"]:
                    show_msg("注册成功，请登录", "green");
                    toggle_mode(None)
                else:
                    d = res.json()['data']
                    current_user['id'] = d['user_id'];
                    current_user['name'] = d['username']
                    show_msg(f"欢迎 {current_user['name']}", "green");
                    render_profile()
            else:
                show_msg(res.json().get('msg'))
        except Exception as ex:
            show_msg(str(ex))

    btn_login_action = ft.ElevatedButton("登录", on_click=handle_auth, bgcolor="blue", color="white", width=280)
    btn_toggle_mode = ft.TextButton("没有账号？去注册", on_click=toggle_mode)

    login_view.content = ft.Column([
        ft.Icon(ft.Icons.ACCOUNT_CIRCLE, size=80, color="blue"),
        ft.Text("校园互助", size=20, weight="bold"),
        ft.Container(height=20), login_user, login_pass, login_contact,
        ft.Container(height=10), btn_login_action, btn_toggle_mode
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # --- 2.6 发布逻辑 ---
    def update_pub_ui(e):
        is_skill = "skill" in (type_chips.value or "")
        input_loc.visible = not is_skill;
        input_cost.visible = is_skill
        page.update()

    type_chips.on_change = update_pub_ui

    def submit_post(e):
        if not current_user['id']: return show_msg("请先登录")
        cat = type_chips.value
        payload = {"title": input_title.value,
                   "image": f"https://picsum.photos/200/200?random={len(input_title.value)}",
                   "user_id": current_user['id']}
        url = f"{API_BASE_URL}/lost-items" if cat in ["lost", "found"] else f"{API_BASE_URL}/skills"

        if cat in ["lost", "found"]:
            payload.update({"desc": input_desc.value, "location": input_loc.value, "type": 0 if cat == "lost" else 1})
        else:
            payload.update({"cost": input_cost.value or "面议", "type": 1 if cat == "skill_supply" else 2})

        try:
            requests.post(url, json=payload)
            show_msg("发布成功", "green");
            input_title.value = "";
            input_desc.value = ""
            switch_tab(0 if "skill" in cat else 1)
        except:
            show_msg("发布失败")

    post_view = ft.Container(padding=20, content=ft.Column([
        ft.Text("发布", size=24, weight="bold"),
        ft.Container(content=type_chips, bgcolor="white", padding=10, border_radius=10,
                     border=ft.border.all(1, "#eee")),
        input_title, input_desc, input_loc, input_cost,
        ft.ElevatedButton("发布", on_click=submit_post, bgcolor="blue", color="white", width=float("inf"))
    ], spacing=20))

    # ==========================================
    # PART 3: 页面组装
    # ==========================================
    body = ft.Container(expand=True)

    def switch_tab(e):
        idx = e if isinstance(e, int) else e.control.data
        for b in [btn_skill, btn_lost, btn_add, btn_user]: b.icon_color = "grey"
        [btn_skill, btn_lost, btn_add, btn_user][idx].icon_color = "blue"

        if idx == 0:
            body.content = ft.Column([search_view, skill_grid], spacing=0)
            load_data("skills", skill_grid, create_skill_card)
        elif idx == 1:
            body.content = ft.Column([search_view, lost_grid], spacing=0)
            load_data("lost-items", lost_grid, create_lost_card)
        elif idx == 2:
            body.content = post_view
        elif idx == 3:
            if current_user['id']:
                render_profile()
            else:
                body.content = login_view
        page.update()

    for b in [btn_skill, btn_lost, btn_add, btn_user]: b.on_click = switch_tab
    btn_skill.icon_color = "blue"

    bottom_nav = ft.Container(
        bgcolor="white", padding=10, border=ft.border.only(top=ft.BorderSide(1, "#e0e0e0")),
        content=ft.Row([btn_skill, btn_lost, btn_add, btn_user], alignment=ft.MainAxisAlignment.SPACE_AROUND)
    )

    page.add(
        ft.Container(padding=15, bgcolor="white", content=ft.Row(
            [ft.Text("校园互助", size=20, weight="bold"), ft.IconButton("refresh", on_click=lambda e: switch_tab(0))])),
        body,
        bottom_nav
    )

    # 启动日志
    print("App is running...")
    load_data("skills", skill_grid, create_skill_card)


# 防止闪退的保护入口
if __name__ == "__main__":
    ft.app(target=main)