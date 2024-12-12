# import asyncio
# import re
# from playwright.async_api import async_playwright

# async def crawl_with_url(target_url):
#     async with async_playwright() as p:
#         browser = await p.chromium.launch(headless=True)
#         context = await browser.new_context(
#             locale='en-US',  
#         )
#         page = await context.new_page()

#         redirected_url = None  # Biến lưu URL redirect

#         async def handle_response(response):
#             nonlocal redirected_url
#             # Kiểm tra nếu phản hồi là redirect
#             if 300 <= response.status < 400:
#                 location = response.headers.get("location")
#                 if location and re.match(r"https://www\.youtube\.com/.+/videos", location):
#                     print(f"Redirected to: {location}")
#                     redirected_url = location

#         page.on("response", handle_response)

#         # Điều hướng đến URL ban đầu
#         await page.goto(target_url)
#         await page.wait_for_timeout(5000)  
#         await browser.close()

#         return redirected_url

# # Ví dụ sử dụng hàm
# url = "https://www.youtube.com/@BongaHD/shorts"
# redirected_url = asyncio.run(crawl_with_url(url))
# if redirected_url:
#     print(f"Final redirected URL: {redirected_url}")
# else:
#     print("No redirection occurred.")

import re

entity_id = "item-mu-epMGc8l8"
match = re.search(r"item-(.*)", entity_id)
video_id = match.group(1) if match else None
video_url = f"https://youtu.be/{video_id}" if video_id else None

print(video_url)