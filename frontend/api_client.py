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

    # --- 【核心修改】增加 location 参数 ---
    @staticmethod
    def get_lost_items(item_type=None, keyword=None, location=None):
        params = {}
        if keyword: params['keyword'] = keyword
        if location: params['location'] = location
        if item_type is not None: params['type'] = item_type
        return requests.get(f"{API_BASE_URL}/lost-items", params=params)

    # --- 【新增】获取标签云 ---
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
        # endpoint: "skills" or "lost-items"
        return requests.post(f"{API_BASE_URL}/{endpoint}", json=data)

    @staticmethod
    def delete_item(item_id, category):
        return requests.post(f"{API_BASE_URL}/delete", json={"id": item_id, "category": category})

    @staticmethod
    def interact(item_id, category):
        return requests.post(f"{API_BASE_URL}/interact", json={"item_id": item_id, "category": category})