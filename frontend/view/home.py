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

        # 筛选状态缓存
        self.filter_skill_type = None
        self.filter_lost_keyword = ""
        self.filter_lost_location = ""

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

        # 2. 顶部切换栏 (修复了 icon 报错)
        self.category_toggle = ft.SegmentedButton(
            selected={"skill"},
            allow_multiple_selection=False,
            allow_empty_selection=False,
            on_change=self.handle_category_change,
            segments=[
                ft.Segment(
                    value="skill",
                    label=ft.Text("技能银行"),
                    icon=ft.Icon(ft.Icons.TOKEN)  # 修复点：必须用 ft.Icon 包裹
                ),
                ft.Segment(
                    value="lost",
                    label=ft.Text("失物招领"),
                    icon=ft.Icon(ft.Icons.SEARCH)  # 修复点：必须用 ft.Icon 包裹
                ),
            ]
        )

        # 3. 筛选按钮
        self.filter_btn = ft.IconButton(
            icon=ft.Icons.FILTER_LIST,
            tooltip="高级筛选",
            on_click=self.open_filter_dispatcher,
            bgcolor="white"
        )

        # 4. 顶部工具栏容器
        self.toolbar = ft.Container(
            padding=ft.padding.symmetric(horizontal=15, vertical=5),
            content=ft.Row(
                controls=[self.category_toggle, self.filter_btn],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

        # 5. 主列表容器
        self.main_grid = ft.GridView(
            expand=True,
            spacing=10,
            run_spacing=10,
            padding=10
        )

        # --- 发布页组件 ---
        self.input_title = ft.TextField(label="标题 (简短清晰)")
        self.input_desc = ft.TextField(label="详细描述", multiline=True, min_lines=3)
        self.input_loc = ft.TextField(label="地点", icon=ft.Icons.LOCATION_ON)
        self.input_cost = ft.TextField(label="代价/悬赏", icon=ft.Icons.MONETIZATION_ON, visible=False)
        self.pub_type_selector = ft.RadioGroup(content=ft.Row([
            ft.Radio(value="lost", label="失物招领"),
            ft.Radio(value="skill", label="技能互助")
        ]), value="lost", on_change=self.update_pub_ui)

    # ==========================
    # 核心逻辑区
    # ==========================

    def handle_category_change(self, e):
        """切换大类 (技能/失物)"""
        self.current_category = list(e.control.selected)[0]
        # 切换时清空筛选条件，避免逻辑混乱
        self.filter_skill_type = None
        self.filter_lost_keyword = ""
        self.filter_lost_location = ""
        self.search_bar.value = ""
        self.load_data()

    def open_filter_dispatcher(self, e):
        """根据当前分类打开对应的筛选弹窗"""
        if self.current_category == "skill":
            self.open_skill_filter(e)
        else:
            self.open_lost_filter_dialog(e)

    # --- 1. 技能筛选 (简单版) ---
    def open_skill_filter(self, e):
        def set_type(val):
            self.filter_skill_type = val
            self.page.close_bottom_sheet()
            self.load_data()

        self.page.open(ft.BottomSheet(
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("技能类型筛选", weight="bold", size=16),
                    ft.Divider(),
                    ft.ListTile(leading=ft.Icon(ft.Icons.ALL_INCLUSIVE), title=ft.Text("全部显示"),
                                on_click=lambda e: set_type(None)),
                    ft.ListTile(leading=ft.Icon(ft.Icons.HANDSHAKE), title=ft.Text("只看提供 (赚积分)"),
                                on_click=lambda e: set_type(1)),
                    ft.ListTile(leading=ft.Icon(ft.Icons.HELP), title=ft.Text("只看需求 (花积分)"),
                                on_click=lambda e: set_type(2)),
                ], tight=True)
            )
        ))

    # --- 2. 失物招领筛选 (高级版：标签云) ---
    def open_lost_filter_dialog(self, e):
        # 输入框
        input_kw = ft.TextField(label="关键词", hint_text="物品名称/特征", value=self.filter_lost_keyword,
                                prefix_icon=ft.Icons.TEXT_FIELDS, height=40, text_size=12)
        input_loc = ft.TextField(label="地点", hint_text="在哪丢的/捡的", value=self.filter_lost_location,
                                 prefix_icon=ft.Icons.LOCATION_ON, height=40, text_size=12)

        # 标签容器
        tags_kw_container = ft.Row(wrap=True, spacing=6)
        tags_loc_container = ft.Row(wrap=True, spacing=6)

        # 辅助函数：创建可点击的标签
        def create_chip(text, target_input):
            def on_chip_click(e):
                target_input.value = text
                target_input.update()

            return ft.Container(
                content=ft.Text(text, size=10, color="blue"),
                bgcolor=ft.colors.BLUE_50,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=10,
                on_click=on_chip_click,
                ink=True
            )

        # 从后端获取推荐标签 (如果后端还没写好，这里会跳过，不会报错)
        try:
            res = APIClient.get_search_tags()
            if res.status_code == 200:
                data = res.json().get('data', {})
                # 添加“猜你想搜”
                for t in data.get('keywords', []):
                    tags_kw_container.controls.append(create_chip(t, input_kw))
                # 添加“热门地点”
                for l in data.get('locations', []):
                    tags_loc_container.controls.append(create_chip(l, input_loc))
        except:
            # 如果后端接口没通，显示几个默认的占位符，保证演示效果
            for t in ["校园卡", "耳机", "水杯"]: tags_kw_container.controls.append(create_chip(t, input_kw))
            for l in ["食堂", "图书馆", "操场"]: tags_loc_container.controls.append(create_chip(l, input_loc))

        def apply_filter(e):
            self.filter_lost_keyword = input_kw.value
            self.filter_lost_location = input_loc.value
            self.page.close_bottom_sheet()
            self.load_data()

        def clear_filter(e):
            self.filter_lost_keyword = ""
            self.filter_lost_location = ""
            self.page.close_bottom_sheet()
            self.load_data()

        # 底部弹窗布局
        self.page.open(ft.BottomSheet(
            ft.Container(
                padding=20,
                height=450,
                border_radius=ft.border_radius.only(top_left=20, top_right=20),
                content=ft.Column([
                    ft.Row([ft.Icon(ft.Icons.FILTER_ALT), ft.Text("精确查找", size=18, weight="bold")],
                           alignment="center"),
                    ft.Divider(),

                    ft.Text("关键词", size=12, weight="bold"),
                    input_kw,
                    ft.Row([ft.Icon(ft.Icons.TRENDING_UP, size=14, color="grey"),
                            ft.Text("猜你想搜:", size=11, color="grey")]),
                    tags_kw_container,

                    ft.Container(height=10),

                    ft.Text("地点范围", size=12, weight="bold"),
                    input_loc,
                    ft.Row(
                        [ft.Icon(ft.Icons.PLACE, size=14, color="grey"), ft.Text("热门地点:", size=11, color="grey")]),
                    tags_loc_container,

                    ft.Container(expand=True),

                    ft.Row([
                        ft.OutlinedButton("重置", on_click=clear_filter, expand=1),
                        ft.ElevatedButton("确认筛选", on_click=apply_filter, bgcolor="blue", color="white", expand=2),
                    ])
                ])
            )
        ))

    def load_data(self, keyword_from_bar=""):
        """加载数据主逻辑"""
        self.main_grid.controls.clear()

        # --- 布局核心差异化 ---
        if self.current_category == "skill":
            # 技能：双栏，竖长卡片 (保持原样)
            self.main_grid.runs_count = 2
            self.main_grid.child_aspect_ratio = 0.75
        else:
            # 失物：单栏，宽扁卡片 (【修改点】满足你的单栏要求)
            self.main_grid.runs_count = 1
            self.main_grid.child_aspect_ratio = 2.5

        try:
            if self.current_category == "skill":
                # 加载技能
                res = APIClient.get_skills(keyword_from_bar)
                if res.status_code == 200:
                    data = res.json().get('data', [])
                    # 前端简单过滤类型
                    if self.filter_skill_type:
                        data = [i for i in data if i['type'] == self.filter_skill_type]
                    for item in data:
                        self.main_grid.controls.append(
                            create_skill_card(item, lambda e: self.on_item_click(e.control.data, "skill")))
            else:
                # 加载失物 (支持后端高级筛选)
                # 如果搜索栏有输入，优先用搜索栏；否则用筛选弹窗的关键词
                final_kw = keyword_from_bar if keyword_from_bar else self.filter_lost_keyword

                res = APIClient.get_lost_items(
                    keyword=final_kw,
                    location=self.filter_lost_location
                )

                if res.status_code == 200:
                    data = res.json().get('data', [])
                    for item in data:
                        self.main_grid.controls.append(
                            create_lost_card(item, lambda e: self.on_item_click(e.control.data, "lost")))

            # 空状态提示
            if not self.main_grid.controls:
                self.main_grid.controls.append(
                    ft.Column([
                        ft.Icon(ft.Icons.SEARCH_OFF, size=60, color="grey"),
                        ft.Text("没有找到相关内容", color="grey")
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment="center")
                )
        except Exception as e:
            print(f"Load Error: {e}")
            self.show_msg("网络请求失败")

        self.page.update()

    def do_search(self, e):
        self.load_data(self.search_bar.value)

    # ==========================
    # 视图入口
    # ==========================

    def get_main_view(self):
        """获取主页视图 (搜索+工具栏+列表)"""
        # 每次进入重新加载一次数据
        self.load_data()
        return ft.Column([
            ft.Container(content=self.search_bar, padding=ft.padding.only(left=15, right=15, top=10), bgcolor="white"),
            self.toolbar,
            self.main_grid
        ], spacing=0)

    # ==========================
    # 发布功能区
    # ==========================

    def update_pub_ui(self, e):
        is_skill = self.pub_type_selector.value == "skill"
        self.input_loc.visible = not is_skill
        self.input_cost.visible = is_skill
        self.page.update()

    def get_post_view(self, on_success_nav):
        """获取发布页视图"""

        def submit(e):
            user = self.get_current_user()
            if not user['id']: return self.show_msg("请先登录")

            cat = self.pub_type_selector.value
            payload = {"title": self.input_title.value, "user_id": user['id']}

            if cat == "lost":
                payload.update({"desc": self.input_desc.value, "location": self.input_loc.value})
                endpoint = "lost-items"
                success_msg = "发布成功！感谢互助，人品+5 (模拟)"
            else:
                payload.update({"cost": self.input_cost.value or "面议"})
                endpoint = "skills"
                success_msg = "发布成功！消耗 2 积分 (模拟)"

            try:
                APIClient.post_item(endpoint, payload)
                self.show_msg(success_msg, "green")

                # 发布成功后，自动切回主页并选中对应分类
                self.current_category = cat
                self.category_toggle.selected = {cat}

                # 清空输入框
                self.input_title.value = ""
                self.input_desc.value = ""
                self.input_loc.value = ""
                self.input_cost.value = ""

                on_success_nav(0)  # 0 代表跳转回首页 Tab
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