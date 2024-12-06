import asyncio
from CrawlPreviewData.crawl_preview_data import *
from BotConfig.bot_config import *
from BotConfig.mongoDB_config import *
import random
import urllib.parse

def get_keywords_search():
    result = []
    all_objects = []
    try:
        all_keyword_object = DB_keyword.find({"orgId": 2}).limit(BOT_CONFIG["source_config"]["limit"])
        # all_keyword_object = DB_keyword.find({"orgId": 2}).limit(10)
        if all_keyword_object is None:
            raise Exception("Not Found!")
        for keyword in all_keyword_object:
            all_objects.append(keyword["keyWord"])
            
    except Exception as xx:
        print(xx)

    for key in all_objects:
        try:
            kw = encoded_keywords_search(key)
            if kw is None:
                raise Exception("Cannot encoded")
            result.append(kw)
        except Exception as xx:
            print(xx)
    return result

def encoded_keywords_search(keywords):
    encoded_query = urllib.parse.quote(keywords)
    return encoded_query

async def main():
    while True:
        for encoded_query in get_keywords_search():
            wait_time = random.uniform(BOT_CONFIG["crawl_config"]["delay_range"]["min_time"], 
                                    BOT_CONFIG["crawl_config"]["delay_range"]["max_time"]
                                    )
            
            video_count = await crawl_youtube_data(encoded_query, wait_time)
            # video_count = await crawl_youtube_data(encoded_keywords_search("SHB"), wait_time)
            
            if video_count < 5:
                print("Chờ 2 giây trước khi crawl từ khóa tiếp theo")
                await asyncio.sleep(120)
            elif video_count <= 30:
                print("Chờ 5 phút trước khi crawl từ khóa tiếp theo")
                await asyncio.sleep(300)
            elif video_count <= 100:
                print("Chờ 15 phút trước khi crawl từ khóa tiếp theo...")
                await asyncio.sleep(900)
            else:
                print("Chờ 15 phút trước khi crawl từ khóa tiếp theo...")
                await asyncio.sleep(1800)
            
if __name__ == "__main__":
    asyncio.run(main())
