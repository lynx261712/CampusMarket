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

        # --- 筛选状态 ---
        self.filter_skill_type = None
        self.filter_skill_keyword = ""
        self.filter_lost_keyword = ""
        self.filter_lost_location = ""

        # --- 文件选择器 ---
        self.selected_image_path = None
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        self.page.overlay.append(self.file_picker)

        self.image_path_text = ft.Text("未选择图片 (默认使用空白图)", size=12, color="grey")
        self.upload_btn = ft.ElevatedButton(
            "上传图片", icon=ft.Icons.IMAGE,
            on_click=lambda _: self.file_picker.pick_files(allow_multiple=False,
                                                           allowed_extensions=["jpg", "png", "jpeg"])
        )

        # --- UI组件 ---

        # 1. 搜索框
        self.search_bar = ft.TextField(
            hint_text="搜索...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=20,
            height=40,
            content_padding=10,
            text_size=14,
            bgcolor="white",
            on_submit=self.do_search,
            expand=True
        )

        # 2. 筛选按钮
        self.filter_btn = ft.IconButton(
            icon=ft.Icons.FILTER_LIST,
            tooltip="高级筛选",
            icon_color="blue",
            on_click=self.open_filter_dispatcher
        )

        # 3. 标签云区域 (初始化)
        self.tags_row = ft.Row(wrap=True, spacing=5, run_spacing=5)

        # 4. 分类切换
        self.category_toggle = ft.SegmentedButton(
            selected={"skill"},
            allow_multiple_selection=False,
            on_change=self.handle_category_change,
            segments=[
                ft.Segment(value="skill", label=ft.Text("技能银行"), icon=ft.Icon(ft.Icons.TOKEN)),
                ft.Segment(value="lost", label=ft.Text("失物招领"), icon=ft.Icon(ft.Icons.SEARCH))
            ]
        )

        # 5. 列表网格
        self.main_grid = ft.GridView(expand=True, spacing=10, run_spacing=10, padding=10)

        # 6. 发布页组件
        self.input_title = ft.TextField(label="标题 (简短清晰)")
        self.input_desc = ft.TextField(label="详细描述", multiline=True, min_lines=3)
        self.input_loc = ft.TextField(label="地点", icon=ft.Icons.LOCATION_ON)
        self.input_cost = ft.TextField(label="代价/悬赏", icon=ft.Icons.MONETIZATION_ON, visible=False)
        self.pub_type_selector = ft.RadioGroup(content=ft.Column([
            ft.Text("请选择发布类型:", weight="bold"),
            ft.Radio(value="lost_0", label="丢失了 (失物)"),
            ft.Radio(value="lost_1", label="捡到了 (招领)"),
            ft.Radio(value="skill_1", label="我能提供 (技能)"),
            ft.Radio(value="skill_2", label="需要帮助 (需求)")
        ]), value="lost_0", on_change=self.update_pub_ui)

    # --- 文件选择回调 ---
    def on_file_picked(self, e: ft.FilePickerResultEvent):
        if e.files:
            self.selected_image_path = e.files[0].path
            self.image_path_text.value = f"已选择: {e.files[0].name}"
            self.image_path_text.color = "blue"
        else:
            self.selected_image_path = None
            self.image_path_text.value = "未选择图片"
            self.image_path_text.color = "grey"
        self.page.update()

    # --- 分类切换回调 ---
    def handle_category_change(self, e):
        self.current_category = list(e.control.selected)[0]
        self.load_data()

    # --- 搜索回调 ---
    def do_search(self, e):
        self.load_data(self.search_bar.value)

    # --- 【核心】点击标签回调 (自动切换分类) ---
    def on_tag_click(self, e):
        # 1. 获取标签上的数据
        tag_data = e.control.data  # 这是一个字典: {'text': 'xx', 'cat': 'skill'}
        tag_text = tag_data['text']
        target_cat = tag_data['cat']  # 目标分类

        # 2. 填入搜索框
        self.search_bar.value = tag_text

        # 3. 判断是否需要切换分类 Tab
        if self.current_category != target_cat:
            self.current_category = target_cat
            # 更新 UI 上的 SegmentedButton 选中状态
            self.category_toggle.selected = {target_cat}
            self.category_toggle.update()

        # 4. 执行搜索
        self.load_data(tag_text)
        self.page.update()

    # --- 【核心】加载热门标签 ---
    def load_tags(self):
        try:
            res = APIClient.get_tags()
            if res.status_code == 200:
                # 后端现在返回的是列表对象: [{"text":"xx", "cat":"skill"}, ...]
                tags = res.json().get('data', [])

                self.tags_row.controls.clear()
                for t in tags:
                    # 根据分类给标签不同的颜色，增强提示
                    # 技能=浅蓝背景，失物=浅红背景
                    is_skill = (t['cat'] == 'skill')
                    chip_color = "#e3f2fd" if is_skill else "#ffebee"
                    text_color = "blue" if is_skill else "red"
                    icon = ft.Icons.TOKEN if is_skill else ft.Icons.SEARCH

                    self.tags_row.controls.append(
                        ft.Chip(
                            label=ft.Text(t['text']),
                            leading=ft.Icon(icon, size=14, color=text_color),
                            on_click=self.on_tag_click,
                            bgcolor=chip_color,
                            label_style=ft.TextStyle(color=text_color, size=12),
                            data=t  # 【关键】把整个对象存进去，以便点击时读取分类
                        )
                    )
        except Exception as ex:
            print(f"Tags error: {ex}")

    # --- 筛选分发逻辑 ---
    def open_filter_dispatcher(self, e):
        if self.current_category == "skill":
            self.open_skill_filter(e)
        else:
            self.open_lost_filter_dialog(e)

    # --- 技能筛选弹窗 ---
    def open_skill_filter(self, e):
        input_kw = ft.TextField(
            label="关键词", value=self.filter_skill_keyword, prefix_icon=ft.Icons.SEARCH
        )
        btn_provide = ft.ElevatedButton("只看【我能提供】", data=1)
        btn_need = ft.ElevatedButton("只看【需要帮助】", data=2)

        def update_btn_style():
            btn_provide.bgcolor = "blue" if self.filter_skill_type == 1 else "grey"
            btn_provide.color = "white"
            btn_need.bgcolor = "blue" if self.filter_skill_type == 2 else "grey"
            btn_need.color = "white"
            if self.page: self.page.update()

        def on_type_click(e):
            clicked_val = e.control.data
            if self.filter_skill_type == clicked_val:
                self.filter_skill_type = None
            else:
                self.filter_skill_type = clicked_val
            update_btn_style()

        btn_provide.on_click = on_type_click
        btn_need.on_click = on_type_click
        update_btn_style()

        def do_confirm(e):
            self.filter_skill_keyword = input_kw.value
            self.page.dialog.open = False
            self.page.update()
            self.load_data()

        dlg = ft.AlertDialog(
            title=ft.Text("筛选技能"),
            content=ft.Column([
                input_kw,
                ft.Text("类型筛选:", weight="bold"),
                ft.Row([btn_provide, btn_need], alignment=ft.MainAxisAlignment.SPACE_AROUND),
            ], height=180, tight=True),
            actions=[
                ft.TextButton("取消", on_click=lambda _: setattr(dlg, 'open', False) or self.page.update()),
                ft.TextButton("确定", on_click=do_confirm),
            ]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    # --- 失物招领筛选弹窗 ---
    def open_lost_filter_dialog(self, e):
        input_kw = ft.TextField(label="关键词", value=self.filter_lost_keyword)
        input_loc = ft.TextField(label="地点", value=self.filter_lost_location)

        def do_confirm(e):
            self.filter_lost_keyword = input_kw.value
            self.filter_lost_location = input_loc.value
            dlg.open = False
            self.page.update()
            self.load_data()

        def do_clear(e):
            self.filter_lost_keyword = ""
            self.filter_lost_location = ""
            input_kw.value = ""
            input_loc.value = ""
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("高级筛选"),
            content=ft.Column([input_kw, input_loc], height=180, tight=True),
            actions=[
                ft.TextButton("清空条件", on_click=do_clear),
                ft.TextButton("确定", on_click=do_confirm),
            ]
        )
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    # --- 加载数据 ---
    def load_data(self, keyword_from_bar=""):
        self.main_grid.controls.clear()

        # 布局比例
        if self.current_category == "skill":
            self.main_grid.runs_count = 2
            self.main_grid.child_aspect_ratio = 0.75
        else:
            self.main_grid.runs_count = 1
            self.main_grid.child_aspect_ratio = 2.5

        try:
            if self.current_category == "skill":
                final_keyword = keyword_from_bar if keyword_from_bar else self.filter_skill_keyword
                res = APIClient.get_skills(final_keyword)
                if res.status_code == 200:
                    data = res.json().get('data', [])
                    for item in data:
                        if self.filter_skill_type is not None:
                            if item.get('type') != self.filter_skill_type: continue
                        self.main_grid.controls.append(
                            create_skill_card(item, lambda e: self.on_item_click(e.control.data, "skill")))
            else:
                res = APIClient.get_lost_items(
                    keyword=keyword_from_bar or self.filter_lost_keyword,
                    location=self.filter_lost_location
                )
                if res.status_code == 200:
                    for item in res.json().get('data', []):
                        self.main_grid.controls.append(
                            create_lost_card(item, lambda e: self.on_item_click(e.control.data, "lost")))
        except Exception as e:
            print(f"Load error: {e}")

        self.page.update()

    # --- 获取主页视图 ---
    def get_main_view(self):
        self.load_data()
        self.load_tags()  # 调用加载标签

        search_row = ft.Row(
            [self.search_bar, self.filter_btn],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    search_row,
                    ft.Container(content=self.tags_row, padding=ft.padding.only(top=5))
                ]),
                padding=ft.padding.only(left=15, right=15, top=10),
                bgcolor="white"
            ),
            ft.Container(padding=10, content=self.category_toggle),
            self.main_grid
        ], spacing=0)

    # --- 发布页 UI 更新 ---
    def update_pub_ui(self, e):
        val = self.pub_type_selector.value
        is_skill = "skill" in val
        self.input_loc.visible = not is_skill
        self.input_cost.visible = is_skill
        self.page.update()

    # --- 获取发布页视图 ---
    def get_post_view(self, on_success_nav):
        def submit(e):
            user = self.get_current_user()
            if not user['id']: return self.show_msg("请先登录")

            selection = self.pub_type_selector.value
            if not selection: return self.show_msg("请选择类型")

            category, type_val = selection.split('_')

            form_data = {
                "title": self.input_title.value,
                "user_id": str(user['id']),
                "type": type_val
            }
            if not form_data["title"]: return self.show_msg("标题不能为空")

            if category == "lost":
                form_data.update({"desc": self.input_desc.value, "location": self.input_loc.value})
                endpoint = "lost-items"
            else:
                form_data.update({"cost": self.input_cost.value or "面议"})
                endpoint = "skills"

            try:
                res = APIClient.post_item(endpoint, form_data, self.selected_image_path)
                if res.status_code == 200:
                    self.show_msg("发布成功！", "green")
                    self.input_title.value = ""
                    self.input_desc.value = ""
                    self.input_loc.value = ""
                    self.input_cost.value = ""
                    self.selected_image_path = None
                    self.image_path_text.value = "未选择图片"
                    on_success_nav(0)
                else:
                    self.show_msg(f"失败: {res.json().get('msg')}")
            except Exception as ex:
                self.show_msg(f"错误: {ex}")

        return ft.Container(padding=20, content=ft.Column([
            ft.Text("发布新内容", size=20, weight="bold"),
            ft.Container(content=self.pub_type_selector, bgcolor="white", padding=10, border=ft.border.all(1, "#eee")),
            self.input_title, self.input_desc, self.input_loc, self.input_cost,
            ft.Row([self.upload_btn, self.image_path_text]),
            ft.ElevatedButton("立即发布", on_click=submit, bgcolor="blue", color="white", width=float("inf"))
        ], scroll=ft.ScrollMode.AUTO))