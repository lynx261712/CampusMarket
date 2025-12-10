import flet as ft
from api_client import APIClient
from components.cards import create_skill_card, create_lost_card


class HomeView:
    def __init__(self, page, show_msg, on_item_click, get_current_user):
        self.page = page
        self.show_msg = show_msg
        self.on_item_click = on_item_click
        self.get_current_user = get_current_user

        # --- 状态管理 ---
        self.current_category = "skill"  # "skill" 或 "lost"
        self.current_filter = None  # None=全部, 1/2/0 根据类型不同

        # --- UI 组件 ---

        # 1. 搜索框
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

        # 2. 顶部工具栏 (左边切换，右边筛选)
        # 【修复点】icon 参数必须包裹在 ft.Icon() 中
        self.category_toggle = ft.SegmentedButton(
            selected={"skill"},
            allow_multiple_selection=False,
            allow_empty_selection=False,
            on_change=self.handle_category_change,
            segments=[
                ft.Segment(
                    value="skill",
                    label=ft.Text("技能银行"),
                    icon=ft.Icon(ft.Icons.TOKEN)  # <--- 修改了这里
                ),
                ft.Segment(
                    value="lost",
                    label=ft.Text("失物招领"),
                    icon=ft.Icon(ft.Icons.SEARCH)  # <--- 修改了这里
                ),
            ]
        )

        self.filter_btn = ft.IconButton(
            icon=ft.Icons.FILTER_LIST,
            tooltip="筛选条件",
            on_click=self.open_filter_dialog,
            bgcolor="white"
        )

        # 工具栏容器
        self.toolbar = ft.Container(
            padding=ft.padding.symmetric(horizontal=15, vertical=5),
            content=ft.Row(
                controls=[
                    self.category_toggle,
                    self.filter_btn
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

        # 3. 列表容器 (共用一个GridView)
        self.main_grid = ft.GridView(
            expand=True,
            runs_count=2,
            max_extent=200,
            child_aspect_ratio=0.7,
            spacing=10,
            run_spacing=10,
            padding=10
        )

        # 4. 发布页组件
        self.input_title = ft.TextField(label="标题")
        self.input_desc = ft.TextField(label="描述", multiline=True)
        self.input_loc = ft.TextField(label="地点", icon=ft.Icons.LOCATION_ON)
        self.input_cost = ft.TextField(label="代价", icon=ft.Icons.MONETIZATION_ON, visible=False)
        self.pub_type_selector = ft.RadioGroup(content=ft.Row([
            ft.Radio(value="lost", label="失物"), ft.Radio(value="skill", label="技能")
        ]), value="lost", on_change=self.update_pub_ui)

    # --- 逻辑处理 ---

    def handle_category_change(self, e):
        # 切换大类时，重置筛选条件并刷新
        self.current_category = list(e.control.selected)[0]
        self.current_filter = None  # 重置筛选
        self.load_data()

    def open_filter_dialog(self, e):
        # 根据当前大类，显示不同的筛选选项
        if self.current_category == "skill":
            options = [
                ft.PopupMenuItem(text="全部显示", on_click=lambda e: self.set_filter(None)),
                ft.PopupMenuItem(text="只看提供 (赚积分)", on_click=lambda e: self.set_filter(1)),
                ft.PopupMenuItem(text="只看需求 (花积分)", on_click=lambda e: self.set_filter(2)),
            ]
        else:
            options = [
                ft.PopupMenuItem(text="全部显示", on_click=lambda e: self.set_filter(None)),
                ft.PopupMenuItem(text="只看寻物 (丢失)", on_click=lambda e: self.set_filter(0)),
                ft.PopupMenuItem(text="只看招领 (捡到)", on_click=lambda e: self.set_filter(1)),
            ]

        # 使用 BottomSheet 展示筛选菜单
        self.page.open(ft.BottomSheet(
            ft.Container(
                padding=20,
                content=ft.Column(
                    [ft.Text("筛选条件", weight="bold", size=16)] +
                    [ft.ListTile(title=ft.Text(opt.text), on_click=opt.on_click) for opt in options],
                    tight=True
                )
            )
        ))

    def set_filter(self, val):
        self.current_filter = val
        self.page.close_bottom_sheet()  # 关闭弹窗
        self.load_data()

    def load_data(self, keyword=""):
        self.main_grid.controls.clear()

        # 根据分类调整 Grid 布局参数
        if self.current_category == "skill":
            self.main_grid.child_aspect_ratio = 0.75
            self.main_grid.runs_count = 2
        else:
            self.main_grid.child_aspect_ratio = 1.8
            self.main_grid.runs_count = 1

        try:
            if self.current_category == "skill":
                # 获取技能
                res = APIClient.get_skills(keyword)
                if res.status_code == 200:
                    data = res.json().get('data', [])
                    # 前端筛选
                    if self.current_filter is not None:
                        data = [i for i in data if i['type'] == self.current_filter]

                    for item in data:
                        self.main_grid.controls.append(
                            create_skill_card(item, lambda e: self.on_item_click(e.control.data, "skill"))
                        )
            else:
                # 获取失物
                res = APIClient.get_lost_items(item_type=self.current_filter, keyword=keyword)
                if res.status_code == 200:
                    data = res.json().get('data', [])
                    for item in data:
                        self.main_grid.controls.append(
                            create_lost_card(item, lambda e: self.on_item_click(e.control.data, "lost"))
                        )

            if not self.main_grid.controls:
                self.main_grid.controls.append(
                    ft.Column([ft.Icon(ft.Icons.SEARCH_OFF, size=50, color="grey"),
                               ft.Text("没有找到相关内容", color="grey")],
                              alignment=ft.MainAxisAlignment.CENTER)
                )

        except Exception as e:
            print(f"Error loading data: {e}")
            self.show_msg("加载失败，请检查网络")

        self.page.update()

    def do_search(self, e):
        self.load_data(self.search_bar.value)

    # --- 视图入口 ---
    def get_main_view(self):
        # 首次加载
        self.load_data()
        return ft.Column([
            ft.Container(content=self.search_bar, padding=ft.padding.only(left=15, right=15, top=10), bgcolor="white"),
            self.toolbar,
            self.main_grid
        ], spacing=0)

    # --- 发布页逻辑 ---
    def update_pub_ui(self, e):
        is_skill = self.pub_type_selector.value == "skill"
        self.input_loc.visible = not is_skill
        self.input_cost.visible = is_skill
        self.page.update()

    def get_post_view(self, on_success_nav):
        def submit(e):
            user = self.get_current_user()
            if not user['id']: return self.show_msg("请先登录")

            cat = self.pub_type_selector.value
            payload = {"title": self.input_title.value, "user_id": user['id']}

            if cat == "lost":
                payload.update({"desc": self.input_desc.value, "location": self.input_loc.value})
                endpoint = "lost-items"
            else:
                payload.update({"cost": self.input_cost.value or "面议"})
                endpoint = "skills"

            try:
                APIClient.post_item(endpoint, payload)
                self.show_msg("发布成功", "green")
                # 发布成功后，切换回首页并自动选中对应的分类
                self.current_category = cat
                self.category_toggle.selected = {cat}
                on_success_nav(0)
            except:
                self.show_msg("失败")

        return ft.Container(padding=20, content=ft.Column([
            ft.Text("发布新内容", size=24, weight="bold"),
            ft.Container(content=self.pub_type_selector, bgcolor="white", padding=10, border_radius=10,
                         border=ft.border.all(1, "#eee")),
            self.input_title, self.input_desc, self.input_loc, self.input_cost,
            ft.ElevatedButton("发布", on_click=submit, bgcolor="blue", color="white", width=float("inf"))
        ]))