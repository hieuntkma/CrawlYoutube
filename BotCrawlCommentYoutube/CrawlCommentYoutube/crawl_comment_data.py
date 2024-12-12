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
# from CrawlPreviewData.send_data import send_data_to_api

responses = []

# # Cuộn tới cuối
async def scroll_to_bottom(page):
    await page.evaluate("window.scrollBy(0, 200);")
    await asyncio.sleep(5)
    previous_height = await page.evaluate("document.documentElement.scrollHeight")    
    while True:
        await page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight);")
        await asyncio.sleep(2)
        new_height = await page.evaluate("document.documentElement.scrollHeight")
        if new_height == previous_height:
            break
        previous_height = new_height
    await asyncio.sleep(3)  


async def click_more_replies(comment):
    """Nhấn vào nút 'more-replies' để mở thêm trả lời bình luận."""
    while True:
        try:
            # Tìm nút "more-replies" và nhấp vào nó
            more_replies_button = await comment.query_selector("#more-replies")
            if more_replies_button:
                await more_replies_button.click()
                print("Nhấn vào nút 'more-replies'.")
                await asyncio.sleep(1)  # Đợi tải các trả lời mới
            else:
                break
        except Exception as e:
            print(f"Lỗi khi nhấn vào nút 'more-replies'")
            break


async def click_show_more_replies(reply_element):
    """Nhấn vào nút 'Show more replies' để mở thêm các trả lời."""
    while True:
        # Tìm nút 'Show more replies'
        show_more_button = await reply_element.query_selector("ytd-continuation-item-renderer #button ytd-button-renderer")
        if show_more_button:
            try:
                await show_more_button.scroll_into_view_if_needed()
                await show_more_button.click()
                print("Nhấn vào nút 'Show more replies'.")
                await asyncio.sleep(1)  # Đợi tải các trả lời mới
            except Exception as e:
                print(f"Lỗi khi nhấn vào nút 'Show more replies'")
                break
        else:
            break


async def process_comments(page):
    """Duyệt qua các bình luận và trả lời để mở rộng chúng."""

    comment_elements = await page.query_selector_all("ytd-comment-thread-renderer")
    
    for comment in comment_elements:
        # Mở tất cả các trả lời của bình luận
        await click_more_replies(comment)
    
        # Mở thêm các trả lời nếu có nút 'Show more replies'
        reply_elements = await comment.query_selector_all("ytd-comment-replies-renderer")
        for reply_element in reply_elements:
            await click_show_more_replies(reply_element)


async def crawl_comment_youtube_data(video_url, auth_name):
    check_comment_flag = False
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
                locale='en-US',  # Đặt ngôn ngữ thành tiếng Anh
                # timezone_id='America/New_York'
                )
        page = await context.new_page()

        async def handle_response(response):
            nonlocal check_comment_flag 
            url = response.url
            # if '/youtubei/v1/player' in url:
            if 'youtubei/v1/next' in url:
                try:
                    data = await response.json()

                    framework_updates = data.get("frameworkUpdates", {})
                    entity_batch_update = framework_updates.get("entityBatchUpdate", {})
                    mutations = entity_batch_update.get("mutations", [])

                    for mutation in mutations:
                        if mutation.get("type") == "ENTITY_MUTATION_TYPE_REPLACE":
                            payload = mutation.get("payload", {})
                            comment_entity_payload = payload.get("commentEntityPayload")
                            if comment_entity_payload:
                                responses.append(comment_entity_payload)
                                if len(responses) >=  50:
                                    convert_comment_data(responses, video_url, auth_name)
                                    responses.clear()
                                check_comment_flag = True
                except Exception as e:
                    print(e)
        
        page.on('response', handle_response)
        
        await page.goto(f'{video_url}')
        
        await page.wait_for_timeout(5000)
        
        await page.evaluate("""
            const player = document.querySelector('video');
            if (player) {
                player.pause();
            }
        """)
        
        await page.wait_for_timeout(5000)
        
        await scroll_to_bottom(page)
        
        await process_comments(page)
        
        await browser.close()
        
        if responses and len(responses) < 50:
            convert_comment_data(responses, video_url, auth_name)
        return check_comment_flag
        
        

# hàm này chỉ sử dụng cho comment youtube
def convert_to_timestamp_for_comment(relative_time):
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

        print("Định dạng thời gian không hợp lệ.")
        return None

    except Exception as e:
        print(f"Lỗi khi chuyển đổi thời gian: {e}")
        return None
    
# hàm lấy số lượng like chỉ sử dụng cho comment
def extract_like_and_reply_count(like_count_str):
    """Trích xuất số lượng like từ chuỗi và trả về số nguyên."""
    match = re.search(r'(\d+(\.\d+)?)([KMB]?)\s*likes', like_count_str)

    if match:
        number = float(match.group(1))
        unit = match.group(3)

        if unit == 'K':
            number *= 1000
        elif unit == 'M':
            number *= 1000000
        elif unit == 'B':
            number *= 1000000000

        return int(number)  
    else:
        return None

# Regex để lấy video ID
def extract_video_id(url):
    pattern = r"(?:youtu\.be\/|v=|\/v\/|\/embed\/|\/shorts\/)([^#&?\/\s]+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None
    

def convert_comment_data(responses, url, auth_name):
    
    data = [] 
    
    for item in responses:
        
        author = {
            "author_id" : item.get("author", {}).get("displayName", {}) or None,
            "channel_id" : item.get("author", {}).get("channelId", {}) or None,
        }
        
        properties = {
            "comment_id" : item.get("properties", {}).get("commentId", {}) or None,
            "publish_date_str" : item.get("properties", {}).get("publishedTime", {}) or None,
            "reply_level" : item.get("properties", {}).get("replyLevel", {}) or None,
            "content" : item.get("properties", {}).get("content", {}).get("content", {}) or None,
        }
        
        toolbar = {
            "like_count" : item.get("toolbar", {}).get("likeCountA11y", {}) or None,
            "reply_count" : item.get("toolbar", {}).get("replyCountA11y", {}) or None,
        }
        
        like_count = extract_like_and_reply_count(toolbar["like_count"]) if toolbar["like_count"] else None
        reply_count = extract_like_and_reply_count(toolbar["reply_count"]) if toolbar["reply_count"] else None
        
        publish_date_timestamp = convert_to_timestamp_for_comment(properties['publish_date_str']) if properties['publish_date_str'] else None
        video_id = extract_video_id(url)
        
        comment_url = f"https://youtu.be/{video_id}&lc={properties['comment_id']}" if video_id else None
        
        author_url = f"https://www.youtube.com/channel/{author['channel_id']}" if author["channel_id"] else None
        
        # existing_comment = DB_ABPCrawlYTB.find_one({"url": video_url})
        
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
            "description": None,
            "content": properties['content'] or None,
            "url": comment_url,
            "media_urls": "[]",
            "subject_id": None,
            "web_tags": '[]', 
            "web_keywords": '[]',
            "reactions": like_count or 0,
            "comments": reply_count or 0,
            "shares": 0,
            "favors": 0,
            "views": 0,
            "auth_id": author["author_id"],
            "auth_url": author_url,
            "auth_name": author["author_id"].lstrip('@') or None,
            "auth_type": 1,
            "source_id": author["author_id"],
            "source_url": author_url,
            "source_name": auth_name or None,
            "@timestamp": datetime.now().isoformat() if datetime.now() else None,
        }
        
        data.append(processed_item)
    
    # if data:
    #     with open("data.json", "w", encoding="utf-8") as file:
    #         json.dump(data, file, ensure_ascii=False, indent=4)

        # print(f"Đã thêm item .")
        # data.append(processed_item)
        
    if data:
        print(f"Gửi {len(data)} bài viết lên API")
        send_data_to_api(data)
        data.clear()


