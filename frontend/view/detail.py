import flet as ft
from api_client import APIClient


def DetailView(item, category, on_back, show_msg):
    detail_img = ft.Image(src=item['image'], width=float("inf"), height=200, fit=ft.ImageFit.COVER)
    btn_get_contact = ft.ElevatedButton("获取联系方式", bgcolor="blue", color="white", width=float("inf"))

    def get_contact_api(e):
        try:
            res = APIClient.interact(item['id'], category)
            if res.status_code == 200:
                dlg = ft.AlertDialog(title=ft.Text("联系方式"),
                                     content=ft.Text(res.json()['data']['contact'], size=20, weight="bold",
                                                     color="blue"))
                e.page.dialog = dlg
                dlg.open = True
                e.page.update()
            else:
                show_msg("获取失败")
        except Exception as ex:
            show_msg(str(ex))

    btn_get_contact.on_click = get_contact_api

    content_val = f"代价: {item.get('cost')}" if category == "skill" else f"描述: {item.get('desc')}"
    meta = [ft.Icon(ft.Icons.PERSON), ft.Text(item.get('user'))] if category == "skill" else [
        ft.Icon(ft.Icons.LOCATION_ON), ft.Text(item.get('location'))]

    return ft.Column([
        ft.Stack([
            detail_img,
            ft.IconButton(ft.Icons.ARROW_BACK, icon_color="white", on_click=on_back, left=5, top=5)
        ]),
        ft.Container(padding=20, content=ft.Column([
            ft.Text(item['title'], size=22, weight="bold"),
            ft.Divider(),
            ft.Text(content_val, size=16),
            ft.Row(meta),
            ft.Container(height=20),
            btn_get_contact
        ]))
    ])