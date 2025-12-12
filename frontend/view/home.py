import flet as ft
from api_client import APIClient
from components.cards import create_skill_card, create_lost_card


class HomeView:
    def __init__(self, page, show_msg, on_item_click, get_current_user):
        self.page = page
        self.show_msg = show_msg
        self.on_item_click = on_item_click
        self.get_current_user = get_current_user

        self.current_category = "skill"

        self.filter_skill_type = None
        self.filter_lost_keyword = ""
        self.filter_lost_location = ""

        # --- UI 组件 ---
        self.search_bar = ft.TextField(
            hint_text="搜索...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=20,
            height=40,
            content_padding=10,
            text_size=14,
            bgcolor="white",
            on_submit=self.do_search
        )

        self.category_toggle = ft.SegmentedButton(
            selected={"skill"},
            allow_multiple_selection=False,
            allow_empty_selection=False,
            on_change=self.handle_category_change,
            segments=[
                ft.Segment(value="skill", label=ft.Text("技能银行"), icon=ft.Icon(ft.Icons.TOKEN)),
                ft.Segment(value="lost", label=ft.Text("失物招领"), icon=ft.Icon(ft.Icons.SEARCH)),
            ]
        )

        self.filter_btn = ft.IconButton(
            icon=ft.Icons.FILTER_LIST,
            tooltip="高级筛选",
            on_click=self.open_filter_dispatcher,
            bgcolor="white"
        )

        self.toolbar = ft.Container(
            padding=ft.padding.symmetric(horizontal=15, vertical=5),
            content=ft.Row(
                controls=[self.category_toggle, self.filter_btn],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

        self.main_grid = ft.GridView(expand=True, spacing=10, run_spacing=10, padding=10)

        # --- 发布页组件 (修改为4个选项) ---
        self.input_title = ft.TextField(label="标题 (简短清晰)")
        self.input_desc = ft.TextField(label="详细描述", multiline=True, min_lines=3)
        self.input_loc = ft.TextField(label="地点", icon=ft.Icons.LOCATION_ON)
        self.input_cost = ft.TextField(label="代价/悬赏", icon=ft.Icons.MONETIZATION_ON, visible=False)

        # 【修改点】4个选项
        self.pub_type_selector = ft.RadioGroup(content=ft.Column([
            ft.Text("请选择发布类型:", weight="bold"),
            ft.Radio(value="lost_0", label="丢失了 (失物)"),
            ft.Radio(value="lost_1", label="捡到了 (招领)"),
            ft.Radio(value="skill_1", label="我能提供 (技能)"),
            ft.Radio(value="skill_2", label="需要帮助 (需求)")
        ]), value="lost_0", on_change=self.update_pub_ui)

    # ... (中间的筛选逻辑保持不变，省略以节省篇幅，请保留原有的 handle_category_change, open_filter_dispatcher 等方法) ...
    # 为保证代码完整性，这里我简写了中间部分，实际使用时请保留原文件中的筛选逻辑代码

    def handle_category_change(self, e):
        self.current_category = list(e.control.selected)[0]
        self.filter_skill_type = None
        self.filter_lost_keyword = ""
        self.filter_lost_location = ""
        self.search_bar.value = ""
        self.load_data()

    def open_filter_dispatcher(self, e):
        if self.current_category == "skill":
            self.open_skill_filter(e)
        else:
            self.open_lost_filter_dialog(e)

    def open_skill_filter(self, e):
        def set_type(val):
            self.filter_skill_type = val
            self.page.close_bottom_sheet()
            self.load_data()

        self.page.open(ft.BottomSheet(ft.Container(padding=20, content=ft.Column([
            ft.Text("技能类型筛选", weight="bold", size=16), ft.Divider(),
            ft.ListTile(leading=ft.Icon(ft.Icons.ALL_INCLUSIVE), title=ft.Text("全部显示"),
                        on_click=lambda e: set_type(None)),
            ft.ListTile(leading=ft.Icon(ft.Icons.HANDSHAKE), title=ft.Text("只看提供"), on_click=lambda e: set_type(1)),
            ft.ListTile(leading=ft.Icon(ft.Icons.HELP), title=ft.Text("只看需求"), on_click=lambda e: set_type(2)),
        ], tight=True))))

    def open_lost_filter_dialog(self, e):
        # ... (保留原有的标签云逻辑) ...
        # 这里为了简洁省略，请保留原代码
        input_kw = ft.TextField(label="关键词", value=self.filter_lost_keyword, prefix_icon=ft.Icons.TEXT_FIELDS)
        input_loc = ft.TextField(label="地点", value=self.filter_lost_location, prefix_icon=ft.Icons.LOCATION_ON)

        def apply_filter(e):
            self.filter_lost_keyword = input_kw.value
            self.filter_lost_location = input_loc.value
            self.page.close_bottom_sheet()
            self.load_data()

        self.page.open(ft.BottomSheet(ft.Container(padding=20, height=400, content=ft.Column([
            ft.Text("筛选", weight="bold"), input_kw, input_loc,
            ft.ElevatedButton("确认", on_click=apply_filter)
        ]))))

    def load_data(self, keyword_from_bar=""):
        self.main_grid.controls.clear()
        if self.current_category == "skill":
            self.main_grid.runs_count = 2
            self.main_grid.child_aspect_ratio = 0.75
        else:
            self.main_grid.runs_count = 1
            self.main_grid.child_aspect_ratio = 2.5

        try:
            if self.current_category == "skill":
                res = APIClient.get_skills(keyword_from_bar)
                if res.status_code == 200:
                    data = res.json().get('data', [])
                    if self.filter_skill_type: data = [i for i in data if i['type'] == self.filter_skill_type]
                    for item in data: self.main_grid.controls.append(
                        create_skill_card(item, lambda e: self.on_item_click(e.control.data, "skill")))
            else:
                final_kw = keyword_from_bar if keyword_from_bar else self.filter_lost_keyword
                res = APIClient.get_lost_items(keyword=final_kw, location=self.filter_lost_location)
                if res.status_code == 200:
                    data = res.json().get('data', [])
                    for item in data: self.main_grid.controls.append(
                        create_lost_card(item, lambda e: self.on_item_click(e.control.data, "lost")))

            if not self.main_grid.controls:
                self.main_grid.controls.append(
                    ft.Column([ft.Icon(ft.Icons.SEARCH_OFF, size=60, color="grey"), ft.Text("无内容", color="grey")],
                              alignment="center"))
        except Exception as e:
            print(f"Load Error: {e}")
        self.page.update()

    def do_search(self, e):
        self.load_data(self.search_bar.value)

    def get_main_view(self):
        self.load_data()
        return ft.Column(
            [ft.Container(content=self.search_bar, padding=ft.padding.only(left=15, right=15, top=10), bgcolor="white"),
             self.toolbar, self.main_grid], spacing=0)

    # --- 发布功能区 (核心修改) ---
    def update_pub_ui(self, e):
        # 只要包含 "skill" 就认为是技能类，显示代价框，隐藏地点框
        val = self.pub_type_selector.value
        is_skill = "skill" in val
        self.input_loc.visible = not is_skill
        self.input_cost.visible = is_skill
        self.page.update()

    def get_post_view(self, on_success_nav):
        def submit(e):
            user = self.get_current_user()
            if not user['id']: return self.show_msg("请先登录")

            selection = self.pub_type_selector.value  # 例如 "lost_0"
            category, type_val = selection.split('_')  # "lost", "0"

            payload = {"title": self.input_title.value, "user_id": user['id']}

            if category == "lost":
                payload.update({
                    "desc": self.input_desc.value,
                    "location": self.input_loc.value,
                    "type": int(type_val)  # 0=丢了, 1=捡了
                })
                endpoint = "lost-items"
            else:
                payload.update({
                    "cost": self.input_cost.value or "面议",
                    "type": int(type_val)  # 1=提供, 2=需求 (注意这里前端value我设的 skill_1/skill_2)
                })
                endpoint = "skills"

            try:
                APIClient.post_item(endpoint, payload)
                self.show_msg("发布成功！", "green")
                self.current_category = category
                self.category_toggle.selected = {category}

                # 清空
                self.input_title.value = ""
                self.input_desc.value = ""
                on_success_nav(0)
            except Exception as ex:
                self.show_msg(f"发布失败: {ex}")

        return ft.Container(
            padding=20,
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.EDIT_SQUARE, color="blue"), ft.Text("发布新内容", size=20, weight="bold")]),
                ft.Divider(),
                ft.Container(
                    content=self.pub_type_selector,
                    bgcolor="white", padding=10, border_radius=10,
                    border=ft.border.all(1, "#eee")
                ),
                self.input_title,
                self.input_desc,
                self.input_loc,
                self.input_cost,
                ft.Container(height=20),
                ft.ElevatedButton("立即发布", on_click=submit, bgcolor="blue", color="white", width=float("inf"),
                                  height=50)
            ], scroll=ft.ScrollMode.AUTO)
        )