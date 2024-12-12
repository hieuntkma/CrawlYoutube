import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime, timedelta
import re
from slugify import slugify
import os
from functools import partial
import sys

from .send_data import *
from BotConfig.bot_config import BOT_CONFIG
from BotConfig.mongoDB_config import *

def convert_html_to_json(html_content):
    # Tìm kiếm ytInitialData trong HTML
    def extract_yt_initial_data(html_content):
        match = re.search(r'var ytInitialData = (\{.*?\});</script>', html_content, re.DOTALL)
        if match:
            return match.group(1)  # Trả về chuỗi JSON
        return None

    yt_initial_data_str = extract_yt_initial_data(html_content)
    if not yt_initial_data_str:
        raise ValueError("Không tìm thấy 'ytInitialData' trong nội dung HTML.")

    try:
        yt_initial_json_data = json.loads(yt_initial_data_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Lỗi khi phân tích chuỗi JSON: {e}")

    response = yt_initial_json_data
    return response

def extract_rich_grid_contents(html_content):
    yt_initial_json_data = convert_html_to_json(html_content)

    try:
        contents = yt_initial_json_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
        for tab in contents:
            if tab.get("tabRenderer", {}).get("selected"):
                rich_grid_contents = tab["tabRenderer"]["content"]["richGridRenderer"]["contents"]
                rich_items = []
                for item in rich_grid_contents:
                    if "richItemRenderer" in item:
                        rich_item = item["richItemRenderer"]
                        # Trích xuất các dữ liệu trong richItemRenderer
                        rich_items.append(rich_item["content"])
                
                return rich_items
    except KeyError as e:
        raise ValueError(f"Lỗi khi trích xuất dữ liệu: {e}")

    return None

async def crawl_follow_youtube_videos_data(channel_url,auth_id,auth_name, org_ids):
    
    responses = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
                locale='en-US',  # Đặt ngôn ngữ thành tiếng Anh
                )
        page = await context.new_page()

        url = await get_redirect_url(channel_url)
        print("redirect to: ",url)
        
        async def handle_response(response):
            if url in response.url:
                html_content = await response.body()
                # Chuyển bytes -> str
                html_content = html_content.decode('utf-8')
                
                # Trích xuất richGridContents
                rich_grid_contents = extract_rich_grid_contents(html_content)
                
                responses.append(rich_grid_contents)
                
                if url in BOT_CONFIG['tracking_source_config']['url_special']:
                    convert_follow_special_data(rich_grid_contents,channel_url,auth_id,auth_name,org_ids)
                
                else: 
                    convert_follow_data(rich_grid_contents,channel_url,auth_id,auth_name)

        page.on("response", handle_response)

        await page.goto(url)
        await page.wait_for_timeout(5000)

        await browser.close()

        return responses

async def get_redirect_url(target_url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale='en-US',  
        )
        page = await context.new_page()

        redirected_url = None  # Biến lưu URL redirect

        async def handle_response(response):
            nonlocal redirected_url
            # Kiểm tra nếu phản hồi là redirect
            if 300 <= response.status < 400:
                location = response.headers.get("location")
                if location and re.match(r"https://www\.youtube\.com/.+/videos", location):
                    print(f"Redirected to: {location}")
                    redirected_url = location

        page.on("response", handle_response)

        # Điều hướng đến URL ban đầu
        await page.goto(target_url)
        await page.wait_for_timeout(5000)  
        await browser.close()

        if redirected_url:
            return redirected_url
        
        return target_url

def convert_to_timestamp_for_follow(relative_time):
    try:
        # Xóa "(edited)" nếu có
        relative_time = relative_time.replace("(edited)", "").strip()

        # Tách dữ liệu bằng regex
        match = re.match(r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", relative_time)
        if match:
            value, unit = int(match.group(1)), match.group(2)

            # Lấy thời gian hiện tại
            now = datetime.now()

            # Chuyển đổi giá trị về timestamp
            if unit == "second":
                delta = timedelta(seconds=value)
            elif unit == "minute":
                delta = timedelta(minutes=value)
            elif unit == "hour":
                delta = timedelta(hours=value)
            elif unit == "day":
                delta = timedelta(days=value)
            elif unit == "week":
                delta = timedelta(weeks=value)
            elif unit == "month":
                # Giả định 1 tháng là 30 ngày
                delta = timedelta(days=value * 30)
            elif unit == "year":
                delta = timedelta(days=value * 365)
            else:
                raise ValueError("Đơn vị thời gian không hợp lệ.")

            timestamp = int((now - delta).timestamp())

            return timestamp

        # Nếu không khớp với định dạng
        print("Định dạng thời gian không hợp lệ.")
        return None

    except Exception as e:
        print(f"Lỗi khi chuyển đổi thời gian: {e}")
        return None

def convert_follow_data(responses, channel_url,auth_id,auth_name):
    
    data = [] 
    for item in responses:
        
        channel_url = channel_url or None
        auth_id = auth_id or None
        auth_name = auth_name or None
        
        publish_date = item.get("videoRenderer", {}).get("publishedTimeText", {}).get("simpleText", {}) or None
        publish_date_timestamp = convert_to_timestamp_for_follow(publish_date) if publish_date is not None else None
        
        view_text = item.get("videoRenderer", {}).get("viewCountText", {}).get("simpleText", {}) or None
        if view_text is not None:
            match = re.search(r'\d+', view_text.replace(",", ""))
            view_count = int(match.group()) if match else 0
        else:
            view_count = 0
        
        video_id = item.get("videoRenderer", {}).get("videoId", {}) or None
        video_url = f"https://youtu.be/{video_id}" if video_id else None
        
        auth_url = channel_url.replace("/videos", "") if channel_url else None
        
        title = item["videoRenderer"]["title"]["runs"][0]["text"] or None
        description_snippet = item["videoRenderer"].get("descriptionSnippet")
        if description_snippet and "runs" in description_snippet:
            description = description_snippet["runs"][0].get("text", None)
        else:
            description = None
        
        # if channel_url in BOT_CONFIG['tracking_source_config']['url_special']:
        #     for org_id in org_ids:
                
        processed_item = {
            # "id": BOT_CONFIG["id"] or None,
            # "org_id": BOT_CONFIG["org_id"] or None,
            "doc_type": BOT_CONFIG["doc_type"] or None,
            "source_type": BOT_CONFIG["source_config"]["source_type"] or None,
            "crawl_source": BOT_CONFIG["source_config"]["crawl_source"] or None,
            "crawl_source_code": BOT_CONFIG["source_config"]["crawl_source_code"] or None,
            "pub_time": publish_date_timestamp,
            "crawl_time": int(datetime.now().timestamp()),
            "sentiment": 0,
            "title": None,
            "description": description,
            "content": title,
            "url": video_url,
            "media_urls": "[]",
            "subject_id": None,
            "web_tags": '[]', 
            "web_keywords": '[]',
            "reactions": 0,
            "comments": 0,
            "shares": 0,
            "favors": 0,
            "views": view_count,
            "auth_id": auth_id,
            "auth_url": auth_url,
            "auth_name": auth_name,
            "auth_type": 1,
            "source_id": auth_id,
            "source_url": auth_url,
            "source_name": auth_name,
            "@timestamp": datetime.now().isoformat() if datetime.now() else None,
        }

        data.append(processed_item)
            
    if data:
        print(f"Gửi {len(data)} bài viết lên API")
        send_data_to_api(data)  # Gửi dữ liệu lên API
        data.clear()

def convert_follow_special_data(responses, channel_url,auth_id,auth_name, org_ids):
    
    data = [] 
    for item in responses:
        
        channel_url = channel_url or None
        auth_id = auth_id or None
        auth_name = auth_name or None
        
        publish_date = item.get("videoRenderer", {}).get("publishedTimeText", {}).get("simpleText", {}) or None
        publish_date_timestamp = convert_to_timestamp_for_follow(publish_date) if publish_date is not None else None
        
        view_text = item.get("videoRenderer", {}).get("viewCountText", {}).get("simpleText", {}) or None
        if view_text is not None:
            match = re.search(r'\d+', view_text.replace(",", ""))
            view_count = int(match.group()) if match else 0
        else:
            view_count = 0
        
        video_id = item.get("videoRenderer", {}).get("videoId", {}) or None
        video_url = f"https://youtu.be/{video_id}" if video_id else None
        
        auth_url = channel_url.replace("/videos", "") if channel_url else None
        
        title = item["videoRenderer"]["title"]["runs"][0]["text"] or None
        description_snippet = item["videoRenderer"].get("descriptionSnippet")
        if description_snippet and "runs" in description_snippet:
            description = description_snippet["runs"][0].get("text", None)
        else:
            description = None
        
        for org_id in org_ids:
            processed_item = {
                # "id": BOT_CONFIG["id"] or None,
                "org_id": org_id or None,
                "doc_type": BOT_CONFIG["doc_type"] or None,
                "source_type": BOT_CONFIG["source_config"]["source_type"] or None,
                "crawl_source": BOT_CONFIG["source_config"]["crawl_source"] or None,
                "crawl_source_code": BOT_CONFIG["source_config"]["crawl_source_code"] or None,
                "pub_time": publish_date_timestamp,
                "crawl_time": int(datetime.now().timestamp()),
                "sentiment": 0,
                "title": None,
                "description": description,
                "content": title,
                "url": video_url,
                "media_urls": "[]",
                "subject_id": None,
                "web_tags": '[]', 
                "web_keywords": '[]',
                "reactions": 0,
                "comments": 0,
                "shares": 0,
                "favors": 0,
                "views": view_count,
                "auth_id": auth_id,
                "auth_url": auth_url,
                "auth_name": auth_name,
                "auth_type": 1,
                "source_id": auth_id,
                "source_url": auth_url,
                "source_name": auth_name,
                'isPriority': True,
                "@timestamp": datetime.now().isoformat() if datetime.now() else None,
            }

            data.append(processed_item)
            
        if data:
            print(f"Gửi {len(data)} bài viết lên API")
            send_special_data_to_api(data)  # Gửi dữ liệu lên API
            data.clear()

