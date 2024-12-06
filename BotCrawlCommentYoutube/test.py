from langdetect import detect, DetectorFactory
import asyncio
import requests
import random
import urllib.parse
from requests.auth import HTTPBasicAuth
import getpass
from decouple import config


from CrawlCommentYoutube.crawl_comment_data import *
from BotConfig.bot_config import *
from BotConfig.mongoDB_config import *

def filter_data(context):
    try:
        text_language = detect(context)
        if text_language == 'vi':
            return True
    except Exception as xx:
        print(xx)
        return False

def get_response(start_index):
    """Lấy dữ liệu từ API."""
    api_url = config("API_URL")
    username = config("API_USERNAME")
    password = config("API_PASSWORD")

    api_url_query = (
        f"{api_url}?q={BOT_CONFIG['api_config']['query']}&"
        f"sort={BOT_CONFIG['api_config']['sort']}&"
        f"from={start_index}&size={BOT_CONFIG['api_config']['size']}"
    )

    try:
        response = requests.get(api_url_query, auth=HTTPBasicAuth(username, password), verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API: {e}")
        return None

def fetch_data():
    """Lấy dữ liệu từ API trong vòng 1 ngày."""
    data = []
    start_index = 0
    flag = True

    while flag:
        json_data = get_response(start_index)
        if not json_data:
            print("Không nhận được dữ liệu từ API, kết thúc.")
            break

        datas = json_data.get("hits", {}).get("hits", [])
        if not datas:
            print("Không có dữ liệu nào trong lần truy vấn này, kết thúc.")
            break

        print(f"Số mục nhận được: {len(datas)}, Start Index: {start_index}")
        current_time = datetime.now()

        for item in datas:
            source_data = item.get("_source", {})
            crawl_time = source_data.get("crawl_time")
            url = source_data.get("url")
            if url == 'https://youtu.be/QwMGQb8IYFk':
                print(".... : ",start_index)
            try:
                crawl_datetime = datetime.fromtimestamp(crawl_time)
                print(crawl_datetime)
                a = current_time - crawl_datetime
                if current_time - crawl_datetime <= timedelta(days=3):
                    
                    data.append(source_data)
                else:
                    print("Thời gian không hợp lệ, kết thúc lấy dữ liệu.")
                    flag = False
                    break
            except Exception as e:
                print(f"Lỗi khi xử lý thời gian: {e}")
                continue

        start_index += 10  # Tăng chỉ mục để lấy dữ liệu tiếp
    return data

# Ghi dữ liệu ra file JSON
def save_data_to_file(data, file_path="du_lieu_chua_xu_ly.json"):
    if data:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        print(f"Đã ghi {len(data)} mục vào {file_path}")
    else:
        print("Không có dữ liệu để ghi.")

if __name__ == "__main__":
    result = fetch_data()
    save_data_to_file(result)
