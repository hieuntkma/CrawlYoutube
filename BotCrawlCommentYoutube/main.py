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
            pub_time = source_data.get("pub_time")

            if url and auth_name and pub_time:
                pub_datetime = datetime.fromtimestamp(pub_time)
                print(pub_datetime)
                if current_time - pub_datetime <= timedelta(days=BOT_CONFIG['crawl_config']['pub_day_range']):
                    data.append({"url": url, "auth_name": auth_name})
                else:
                    print("Thời gian video không hợp lệ, kết thúc lấy dữ liệu.")
                    flag = False
                    break
            else:
                print("Lỗi URL")
        
        start_index += 10
    return data

# url = [{"url" : "https://www.youtube.com/watch?v=l686mVbW96o",
#        "auth_name" : "Hieu"
#        }]

async def main():
    while True:
        for video_data in fetch_data():
        # for video_data in url:
            video_url = video_data["url"]
            auth_name = video_data["auth_name"]
            if auth_name and video_url:
                check_comment_flag = await crawl_comment_youtube_data(video_url,auth_name)
                if check_comment_flag:
                    print("cho 5p")
                    await asyncio.sleep(300)
                else:
                    print("kh co cmt tiep")
                    continue
        
        await asyncio.sleep(BOT_CONFIG['crawl_config']['sleep_time'])

if __name__ == "__main__":
    asyncio.run(main())
