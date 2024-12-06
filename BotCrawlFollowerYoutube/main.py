import asyncio
import requests
import random
import urllib.parse
from requests.auth import HTTPBasicAuth
import getpass
from decouple import config


from CrawlFollowYoutube.crawl_follow_data_videos import *
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
                                "url_videos" : source["url"]+"/videos",
                                "auth_id": source["url"].split('/')[-1].lstrip('@'),
                                "org_ids": source.get("orgId", []) 
                               })
                
    except Exception as xx:
        print(xx)
    return all_objects

# data = [
#     {"name": "Tập đoàn T&T Group", "url_videos": "https://www.youtube.com/@tapoanttgroup6026/videos", "auth_id": "@tapoanttgroup6026", 'org_ids': [5, 6, 10, 12, 13, 14, 11, 2, 15, 50]},
# ]

async def main():
    while True:
        for source_data in get_crawl_source():
        # for source_data in data:
            auth_id = source_data["auth_id"] or None
            channel_url_videos = source_data["url_videos"] or None
            auth_name = source_data["name"] or None
            org_ids = source_data["org_ids"] or None
            
            if auth_name and channel_url_videos and channel_url_videos and auth_name:
                responses_videos = await crawl_follow_youtube_videos_data(channel_url_videos,
                                                                          auth_id,
                                                                          auth_name, 
                                                                          org_ids)
                
                if responses_videos:
                    print("cho 5p")
                    await asyncio.sleep(300)
                else:
                    print("Khong lay duoc video")
                    continue

        await asyncio.sleep(BOT_CONFIG['crawl_config']['sleep_time'])

if __name__ == "__main__":
    asyncio.run(main())
