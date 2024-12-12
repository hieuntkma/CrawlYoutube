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
        raise ValueError(f"Lỗi khi trích xuất dữ liệu")

    return None

async def crawl_follow_youtube_shorts_data(channel_url,auth_id,auth_name, org_ids):
    
    responses = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
                locale='en-US',
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

def extract_view_count_for_short(view_text):
    
    if not view_text:
        return 0
    match = re.search(r'(\d+(\.\d+)?)([KMB]?)', view_text.replace(",", ""))
    if match:
        number = float(match.group(1))  
        unit = match.group(3).upper()  

        if unit == "K":
            return int(number * 1_000)
        elif unit == "M":
            return int(number * 1_000_000)
        elif unit == "B":
            return int(number * 1_000_000_000)
        else:
            return int(number)
    else:
        return 0  

def convert_follow_data(responses, channel_url,auth_id,auth_name):
    
    data = [] 
    for item in responses:
        
        channel_url = channel_url or None
        auth_id = auth_id or None
        auth_name = auth_name or None
        
        publish_date_timestamp = datetime.now().timestamp() if datetime.now() else None
        
        view_text = item.get("shortsLockupViewModel", {}).get("overlayMetadata", {}).get("secondaryText", {}).get("content", None)
        view_count = extract_view_count_for_short(view_text)
        
        entity_id = item.get("shortsLockupViewModel", {}).get("entityId", "")
        match = re.search(r"item-(.*)", entity_id)
        video_id = match.group(1) if match else None
        video_url = f"https://youtu.be/{video_id}" if video_id else None

        
        auth_url = channel_url.replace("/videos", "") if channel_url else None
        
        title = item["shortsLockupViewModel"]["overlayMetadata"]["primaryText"]["content"] or None
        # description_snippet = item["shortsLockupViewModel"].get("descriptionSnippet")
        # if description_snippet and "runs" in description_snippet:
        #     description = description_snippet["runs"][0].get("text", None)
        # else:
        #     description = None
        
        # if channel_url in BOT_CONFIG['tracking_source_config']['url_special']:
        #     for org_id in org_ids:
                
        processed_item = {
            # "id": BOT_CONFIG["id"] or None,
            # "org_id": BOT_CONFIG["org_id"] or None,
            "doc_type": BOT_CONFIG["doc_type"] or None,
            "source_type": BOT_CONFIG["source_config"]["source_type"] or None,
            "crawl_source": BOT_CONFIG["source_config"]["crawl_source"] or None,
            "crawl_source_code": BOT_CONFIG["source_config"]["crawl_source_code"] or None,
            "pub_time": int(publish_date_timestamp),
            "crawl_time": int(datetime.now().timestamp()),
            "sentiment": 0,
            "title": None,
            "description": None,
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
    
    # if data:
    #     with open("data.json", "w", encoding="utf-8") as file:
    #         json.dump(data, file, ensure_ascii=False, indent=4)

    #     print(f"Đã thêm item .")
    #     data.append(processed_item)
    
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
        
        publish_date_timestamp = datetime.now().isoformat() if datetime.now() else None
        
        view_text = item.get("shortsLockupViewModel", {}).get("overlayMetadata", {}).get("secondaryText", {}) or None
        view_count = extract_view_count_for_short(view_text)
        
        entity_id = item.get("shortsLockupViewModel", {}).get("entityId", "")
        video_id = re.search(r"item-(\w+)", entity_id).group(1) if re.search(r"item-(\w+)", entity_id) else None
        video_url = f"https://youtu.be/{video_id}" if video_id else None
        
        auth_url = channel_url.replace("/videos", "") if channel_url else None
        
        title = item["shortsLockupViewModel"]["overlayMetadata"]["primaryText"]["content"] or None
        # description_snippet = item["shortsLockupViewModel"].get("descriptionSnippet")
        # if description_snippet and "runs" in description_snippet:
        #     description = description_snippet["runs"][0].get("text", None)
        # else:
        #     description = None
        
        # if channel_url in BOT_CONFIG['tracking_source_config']['url_special']:
        #     for org_id in org_ids:
                
        for org_id in org_ids:
            processed_item = {
                # "id": BOT_CONFIG["id"] or None,
                "org_id": org_id or None,
                "doc_type": BOT_CONFIG["doc_type"] or None,
                "source_type": BOT_CONFIG["source_config"]["source_type"] or None,
                "crawl_source": BOT_CONFIG["source_config"]["crawl_source"] or None,
                "crawl_source_code": BOT_CONFIG["source_config"]["crawl_source_code"] or None,
                "pub_time": int(publish_date_timestamp),
                "crawl_time": int(datetime.now().timestamp()),
                "sentiment": 0,
                "title": None,
                "description": None,
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
            
        
        # if data:
        #     with open("data_spec.json", "w", encoding="utf-8") as file:
        #         json.dump(data, file, ensure_ascii=False, indent=4)

        #     print(f"Đã thêm item .")
        #     data.append(processed_item)
        
        if data:
            print(f"Gửi {len(data)} bài viết lên API")
            send_special_data_to_api(data)  # Gửi dữ liệu lên API
            data.clear()

