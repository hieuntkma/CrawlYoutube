import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime
import re
from slugify import slugify
import os
from langdetect import detect, DetectorFactory


from BotConfig.bot_config import BOT_CONFIG
from BotConfig.mongoDB_config import *
from CrawlPreviewData.send_data import send_data_to_api
    
responses = []

# Cuộn tới cuối
async def scroll_to_bottom(page):
    previous_height = await page.evaluate("document.documentElement.scrollHeight")    
    while True:
        await page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight);")
        await asyncio.sleep(2)  # Đợi 2 giây để nội dung mới tải
        new_height = await page.evaluate("document.documentElement.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height
    
    video_elements = await page.query_selector_all('ytd-video-renderer')
    return video_elements

async def crawl_youtube_data(search_query, wait_time):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        async def handle_response(response):
            url = response.url
            if '/youtubei/v1/player' in url:
                try:
                    data = await response.json()
                    video_details = data.get("videoDetails")
                    micro_format = data.get("microformat")
                    if video_details and micro_format:
                        content = video_details.get("title") or ""
                        description = video_details.get("shortDescription") or ""
                        
                        context = content + " " +description
                        
                        if context: 
                            check_vietnamese_text = filter_data(context)
                            if check_vietnamese_text is False:
                                raise ValueError("Nội dung không phải tiếng Việt, dừng xử lý")

                        video_data = {
                            "videoDetails": video_details,
                            "microformat": micro_format
                        }
                        
                        responses.append(video_data)
                        print(len(responses))
                        # if len(responses) >= BOT_CONFIG["crawl_config"]["chunk_post_length"]:
                        if len(responses) >= 5:
                            try:
                                a = convert_preview_data(responses)
                                print(f"Đã thu thập {len(responses)} video")
                                responses.clear()
                            except Exception as e:
                                print(e)

                except Exception as e:
                    print(f"{e}")

        page.on('response', handle_response)

        print(f'Tìm kiếm video với từ khóa: {search_query}')
        #search theo ngày
        await page.goto(f'https://www.youtube.com/results?search_query={search_query}&sp={BOT_CONFIG["crawl_config"]["filter_video"]["today_upload_date"]}')
        #search theo tuần
        # await page.goto(f'https://www.youtube.com/results?search_query={search_query}&sp={BOT_CONFIG["crawl_config"]["filter_video"]["week_upload_date"]}')
        await page.wait_for_timeout(5000)

        video_elements = await scroll_to_bottom(page)
        print(f"Số lượng video tìm thấy: {len(video_elements)}")
        
        for i, video_element in enumerate(video_elements):
            print(search_query)
            print(f'Di chuột vào video thứ {i + 1}')
            await video_element.hover()
            await asyncio.sleep(wait_time)

        await browser.close()
        
        if responses:
            convert_preview_data(responses)
        
        return len(video_elements)

    
def convert_to_timestamp(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
        return int(dt.timestamp())
    except ValueError:
        print("Chuỗi thời gian không hợp lệ.")
        return None

def filter_data(context):
    try:
        context_2 = context
        text_language = detect(context_2)
        if text_language == 'vi':
            return True
        return False
    except Exception as xx:
        print(xx)
        return False

def convert_preview_data(responses):
    
    data_batch = []
    
    for item in responses:
        video_details = item.get("videoDetails", {}) or None
        micro_format = item.get("microformat", {}).get("playerMicroformatRenderer", {}) or None
        
        if video_details is None or micro_format is None:
            continue
        
        publish_date_str = micro_format.get("publishDate") or None
        publish_date_timestamp = convert_to_timestamp(publish_date_str) if publish_date_str else None

        owner_profile_url = micro_format.get("ownerProfileUrl")
        author_id_match = re.search(r'@[^/]+', owner_profile_url) if owner_profile_url else None
        author_id = author_id_match.group(0) if author_id_match else None
        
        external_channel_id = micro_format.get("externalChannelId") or None
        author_url = f"https://youtube.com/channel/{external_channel_id}" if external_channel_id else None
        video_url = f"https://youtu.be/{video_details.get('videoId')}" if video_details.get("videoId") else None
        
        processed_item = {
            # "id": BOT_CONFIG["id"] or None,
            # "org_id": BOT_CONFIG["org_id"] or None,
            "doc_type": BOT_CONFIG["doc_type"] or None,
            "source_type": BOT_CONFIG["source_config"]["source_type"] or None,
            "crawl_source": BOT_CONFIG["source_config"]["crawl_source"] or None,
            "crawl_source_code": BOT_CONFIG["source_config"]["crawl_source_code"] or None,
            "pub_time": publish_date_timestamp,
            "crawl_time": int(datetime.now().timestamp()),
            # "title": video_details.get("title") or None,
            # "description": None,
            # "content": video_details.get("shortDescription") or None,
            "sentiment": 0,
            "title": None,
            "description": video_details.get("shortDescription") or None,
            "content": video_details.get("title") or None,
            "url": video_url,
            "media_urls": "[]",
            "subject_id": None,
            "web_tags": '[]', 
            "web_keywords": '[]',
            "reactions": 0,
            "comments": 0,
            "shares": 0,
            "favors": 0,
            "views": int(video_details.get("viewCount") or 0),
            "auth_id": author_id,
            "auth_url": author_url,
            "auth_name": video_details.get("author") or None,
            "auth_type": 1,
            "source_id": author_id,
            "source_url": author_url,
            "source_name": video_details.get("author") or None,
            "@timestamp": datetime.now().isoformat() if datetime.now() else None,
        }
        
        data_batch.append(processed_item)
        if data_batch:
            try :
                send_data_to_api(data_batch)  # Gửi dữ liệu lên API
                print(f"Gửi {len(data_batch)} bài viết lên API")
                data_batch.clear()
            except Exception as e:
                print(e)

        # if existing_video:
        #     print("trùng")
        #     continue
        # DB_ABPCrawlYTB.insert_one(processed_item)
        # print("Đã gửi dữ liệu về db")
        
        