import asyncio
import requests
import random
import urllib.parse
from requests.auth import HTTPBasicAuth
import getpass
from decouple import config


from CrawlFollowYoutube.crawl_follow_data_shorts import *
from BotConfig.bot_config import *
from BotConfig.mongoDB_config import *

def get_crawl_source():
    result = []
    all_objects = []

    try:
        
        all_source_object = DB_source_crawl.find({"source" : "youtube"})
        # all_keyword_object = DB_keyword.find({"orgId": 2}).limit(10)
        if all_source_object is None:
            raise Exception("Not Found!")
        for source in all_source_object:
            all_objects.append({"name" : source["name"],
                                "url_shorts" : source["url"]+"/shorts",
                                "auth_id": source["url"].split('/')[-1].lstrip('@'),
                                "org_ids": source.get("orgId", []) 
                               })
                
    except Exception as xx:
        print(xx)
    return all_objects

data = [
    {"name": "Tập đoàn T&T Group", "url_shorts": "https://www.youtube.com/@tapoanttgroup6026/shorts", "auth_id": "@tapoanttgroup6026", 'org_ids': [5, 6, 10, 12, 13, 14, 11, 2, 15, 50]},
    {"name": "On Sports", "url_shorts": "https://www.youtube.com/@OnSportschannel/shorts", "auth_id": "@OnSportschannel", 'org_ids': [5, 6, 10, 12, 13, 14, 11, 2, 15, 50]},
    {"name": "Hanoi Football Club", "url_shorts": "https://www.youtube.com/@officialhanoifc/shorts", "auth_id": "@officialhanoifc", 'org_ids': [5, 6, 10, 12, 13, 14, 11, 2, 15, 50]},
]

async def main():
    while True:
        # for source_data in get_crawl_source():
        for source_data in data:
            auth_id = source_data["auth_id"] or None
            channel_url_shorts = source_data["url_shorts"] or None
            auth_name = source_data["name"] or None
            org_ids = source_data["org_ids"] or None
            
            if auth_name and channel_url_shorts and auth_name:
                responses_shorts = await crawl_follow_youtube_shorts_data(channel_url_shorts,
                                                                          auth_id,
                                                                          auth_name, 
                                                                          org_ids)
                
                if responses_shorts:
                    print("Chờ 5p sang bài tiếp theo")
                    await asyncio.sleep(5)
                else:
                    print("Kênh không có shorts!")
                    continue
        else:
            continue

        # await asyncio.sleep(BOT_CONFIG['crawl_config']['sleep_time'])

if __name__ == "__main__":
    asyncio.run(main())
