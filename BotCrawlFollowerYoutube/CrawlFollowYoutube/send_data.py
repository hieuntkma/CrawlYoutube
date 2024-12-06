import requests

def send_data_to_api(posts):
    url = "http://103.97.125.64:9091/api/elastic/insert-posts"
    headers = {"Content-Type": "application/json"}
    payload = {
        "index": "not_classify_org_posts",
        "data": posts
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Dữ liệu đã được gửi thành công.")
        else:
            print(f"Lỗi khi gửi dữ liệu: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối API: {e}")
        
def send_special_data_to_api(posts):
    url = "http://103.97.125.64:9091/api/elastic/insert-posts"
    headers = {"Content-Type": "application/json"}
    payload = {
        "index": "facebook_raw_posts",
        "data": posts
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Dữ liệu đã được gửi thành công.")
        else:
            print(f"Lỗi khi gửi dữ liệu: {response.status_code}, {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Lỗi kết nối API: {e}")