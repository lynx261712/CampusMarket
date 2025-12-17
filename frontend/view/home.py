import flet as ft
from api_client import APIClient

# 【核心修改】根据你的截图，cards.py 在 components 文件夹下
# 确保你在 frontend 目录下运行 main.py
from components.cards import create_skill_card, create_lost_card

class HomeView:
    def __init__(self, page, show_msg, on_item_click, get_current_user):
        self.page = page
        self.show_msg = show_msg
        self.on_item_click = on_item_click
        self.get_current_user = get_current_user
        self.current_category = "skill"

        # --- 文件选择器 ---
        self.selected_image_path = None
        self.file_picker = ft.FilePicker(on_result=self.on_file_picked)
        # 【关键】必须添加到 overlay 才能弹出窗口
        self.page.overlay.append(self.file_picker)

        self.image_path_text = ft.Text("未选择图片 (默认使用空白图)", size=12, color="grey")
        self.upload_btn = ft.ElevatedButton(
            "上传图片", icon=ft.Icons.IMAGE,
            on_click=lambda _: self.file_picker.pick_files(allow_multiple=False,
                                                           allowed_extensions=["jpg", "png", "jpeg"])
        )

        # --- UI组件 ---
        self.search_bar = ft.TextField(hint_text="搜索...", prefix_icon=ft.Icons.SEARCH, border_radius=20, height=40,
                                       content_padding=10, text_size=14, bgcolor="white", on_submit=self.do_search)
        self.category_toggle = ft.SegmentedButton(selected={"skill"}, allow_multiple_selection=False,
                                                  on_change=self.handle_category_change,
                                                  segments=[ft.Segment(value="skill", label=ft.Text("技能银行"),
                                                                       icon=ft.Icon(ft.Icons.TOKEN)),
                                                            ft.Segment(value="lost", label=ft.Text("失物招领"),
                                                                       icon=ft.Icon(ft.Icons.SEARCH))])
        self.main_grid = ft.GridView(expand=True, spacing=10, run_spacing=10, padding=10)

        # 发布页组件
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

    def handle_category_change(self, e):
        self.current_category = list(e.control.selected)[0]
        self.load_data()

    def load_data(self, keyword=""):
        self.main_grid.controls.clear()
        # 调整布局比例
        if self.current_category == "skill":
            self.main_grid.runs_count = 2
            self.main_grid.child_aspect_ratio = 0.75
        else:
            self.main_grid.runs_count = 1
            self.main_grid.child_aspect_ratio = 2.5

        try:
            if self.current_category == "skill":
                res = APIClient.get_skills(keyword)
                if res.status_code == 200:
                    for item in res.json().get('data', []):
                        self.main_grid.controls.append(
                            create_skill_card(item, lambda e: self.on_item_click(e.control.data, "skill")))
            else:
                res = APIClient.get_lost_items(keyword=keyword)
                if res.status_code == 200:
                    for item in res.json().get('data', []):
                        self.main_grid.controls.append(
                            create_lost_card(item, lambda e: self.on_item_click(e.control.data, "lost")))
        except Exception as e:
            print(f"Load error: {e}")

        self.page.update()

    def do_search(self, e):
        self.load_data(self.search_bar.value)

    def get_main_view(self):
        self.load_data()
        return ft.Column([
            ft.Container(content=self.search_bar, padding=ft.padding.only(left=15, right=15, top=10), bgcolor="white"),
            ft.Container(padding=10, content=self.category_toggle),
            self.main_grid
        ], spacing=0)

    def update_pub_ui(self, e):
        val = self.pub_type_selector.value
        is_skill = "skill" in val
        self.input_loc.visible = not is_skill
        self.input_cost.visible = is_skill
        self.page.update()

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
                # 调用带文件的 API
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