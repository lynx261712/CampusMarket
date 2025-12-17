import requests
import os

# 避免本地代理干扰
os.environ["NO_PROXY"] = "127.0.0.1,localhost"
API_BASE_URL = "http://127.0.0.1:5000/api"

class APIClient:
    @staticmethod
    def login(username, password):
        return requests.post(f"{API_BASE_URL}/login", json={"username": username, "password": password})

    @staticmethod
    def register(username, password, contact):
        return requests.post(f"{API_BASE_URL}/register", json={"username": username, "password": password, "contact": contact})

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

    # --- 带文件上传的发布接口 ---
    @staticmethod
    def post_item(endpoint, form_data, file_path=None):
        url = f"{API_BASE_URL}/{endpoint}"
        # 如果有文件路径且文件存在
        if file_path and os.path.exists(file_path):
            try:
                # 必须以二进制模式打开
                with open(file_path, 'rb') as f:
                    # files 字典: key='image' 对应后端 request.files['image']
                    files = {'image': (os.path.basename(file_path), f)}
                    # 注意：传 files 时不要传 json=...，而是用 data=form_data
                    return requests.post(url, data=form_data, files=files)
            except Exception as e:
                print(f"File upload error: {e}")
                return requests.post(url, data=form_data)
        else:
            return requests.post(url, data=form_data)

    @staticmethod
    def get_user_info(user_id):
        return requests.get(f"{API_BASE_URL}/user/{user_id}")

    @staticmethod
    def get_user_posts(user_id):
        return requests.get(f"{API_BASE_URL}/user/posts/{user_id}")

    @staticmethod
    def delete_item(item_id, category):
        return requests.post(f"{API_BASE_URL}/delete", json={"id": item_id, "category": category})

    @staticmethod
    def interact(item_id, category):
        return requests.post(f"{API_BASE_URL}/interact", json={"item_id": item_id, "category": category})

    @staticmethod
    def accept_order(item_id, category, user_id):
        return requests.post(f"{API_BASE_URL}/order/accept", json={"id": item_id, "category": category, "user_id": user_id})

    @staticmethod
    def finish_order(item_id, category):
        return requests.post(f"{API_BASE_URL}/order/finish", json={"id": item_id, "category": category})

    @staticmethod
    def review_order(item_id, category, action):
        return requests.post(f"{API_BASE_URL}/order/review", json={"id": item_id, "category": category, "action": action})

    @staticmethod
    def get_my_helps(user_id):
        return requests.get(f"{API_BASE_URL}/user/helps/{user_id}")