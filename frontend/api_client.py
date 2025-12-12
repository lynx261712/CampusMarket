import requests
import os

# 允许本地代理，防止 requests 报错
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
API_BASE_URL = "http://127.0.0.1:5000/api"


class APIClient:
    @staticmethod
    def login(username, password):
        return requests.post(f"{API_BASE_URL}/login", json={"username": username, "password": password})

    @staticmethod
    def register(username, password, contact):
        return requests.post(f"{API_BASE_URL}/register",
                             json={"username": username, "password": password, "contact": contact})

    @staticmethod
    def get_skills(keyword=None):
        return requests.get(f"{API_BASE_URL}/skills", params={"q": keyword})

    @staticmethod
    def get_lost_items(item_type=None, keyword=None, location=None):
        params = {}
        if keyword: params['keyword'] = keyword
        if location: params['location'] = location
        if item_type is not None: params['type'] = item_type
        return requests.get(f"{API_BASE_URL}/lost-items", params=params)

    @staticmethod
    def get_search_tags():
        return requests.get(f"{API_BASE_URL}/lost-items/tags")

    @staticmethod
    def get_user_info(user_id):
        return requests.get(f"{API_BASE_URL}/user/{user_id}")

    @staticmethod
    def get_user_posts(user_id):
        return requests.get(f"{API_BASE_URL}/user/posts/{user_id}")

    @staticmethod
    def update_user(data):
        return requests.post(f"{API_BASE_URL}/user/update", json=data)

    @staticmethod
    def post_item(endpoint, data):
        return requests.post(f"{API_BASE_URL}/{endpoint}", json=data)

    @staticmethod
    def delete_item(item_id, category):
        return requests.post(f"{API_BASE_URL}/delete", json={"id": item_id, "category": category})

    @staticmethod
    def interact(item_id, category):
        return requests.post(f"{API_BASE_URL}/interact", json={"item_id": item_id, "category": category})

    # --- 【重点】以下是此次报错缺失的方法，请务必加上 ---

    @staticmethod
    def accept_order(item_id, category, user_id):
        """接单接口"""
        return requests.post(f"{API_BASE_URL}/order/accept",
                             json={"id": item_id, "category": category, "user_id": user_id})

    @staticmethod
    def finish_order(item_id, category):
        """确认完成接口"""
        return requests.post(f"{API_BASE_URL}/order/finish", json={"id": item_id, "category": category})

    @staticmethod
    def review_order(item_id, category, action):
        """评价接口"""
        return requests.post(f"{API_BASE_URL}/order/review",
                             json={"id": item_id, "category": category, "action": action})

    @staticmethod
    def get_my_helps(user_id):
        """获取我参与的互助列表"""
        return requests.get(f"{API_BASE_URL}/user/helps/{user_id}")