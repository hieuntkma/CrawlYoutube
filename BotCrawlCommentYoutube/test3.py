import requests
import random
import urllib.parse
from requests.auth import HTTPBasicAuth
import getpass
from decouple import config


from CrawlCommentYoutube.crawl_comment_data import *
from BotConfig.bot_config import *
from BotConfig.mongoDB_config import *

def get_responese(start_index):
    api_url = config("API_URL")
    username = config("API_USERNAME")
    password = config("API_PASSWORD")

    api_url_query = f"{api_url}?q={BOT_CONFIG['api_config']['query']}&sort={BOT_CONFIG['api_config']['sort']}&from={start_index}&size={BOT_CONFIG['api_config']['size']}"

    # Gửi yêu cầu GET tới API
    response = requests.get(api_url_query, auth=HTTPBasicAuth(username, password), verify=False)
    response.raise_for_status()  
    json_data = response.json()
    
    return json_data

def fetch_data():
    data = []
    start_index = 0
    flag = True

    while flag:
        json_data = get_responese(start_index)
        datas = json_data.get("hits", {}).get("hits", [])

        current_time = datetime.now()
        print(len(datas))
        print(start_index)

        for item in datas:
            source_data = item.get("_source", {})
            url = source_data.get("url")
            auth_name = source_data.get("auth_name")
            crawl_time = source_data.get("crawl_time")

            if url and auth_name and crawl_time:
                crawl_datetime = datetime.fromtimestamp(crawl_time)

                if current_time - crawl_datetime <= timedelta(days=2):
                    data.append({"url": url, "auth_name": auth_name})
                else:
                    print("Thời gian không hợp lệ, kết thúc lấy dữ liệu.")
                    flag = False
                    break  
            else:
                print("Lỗi URL hoặc thiếu thông tin.")
        
        start_index += 10
        
    with open("output_file.json", "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, ensure_ascii=False, indent=4)
        print(f"Đã ghi {len("output_file.json")} bản ghi tiếng Việt vào ")

fetch_data()
