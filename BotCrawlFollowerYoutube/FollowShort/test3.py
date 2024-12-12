# import re
# import json

# # Đọc nội dung file HTML
# with open('video_page2.html', 'r', encoding='utf-8') as file:
#     html_content = file.read()

# # Sử dụng regex để tìm `ytInitialData`
# match = re.search(r'var ytInitialData = (\{.*?\});</script>', html_content, re.DOTALL)
# if match:
#     # Lấy nội dung JSON
#     yt_initial_data = match.group(1)

#     try:
#         # Chuyển JSON thành dictionary
#         yt_data = json.loads(yt_initial_data)
        
#         # Ghi toàn bộ dữ liệu vào file JSON
#         with open('yt_initial_data2.json', 'w', encoding='utf-8') as file:
#             json.dump(yt_data, file, ensure_ascii=False, indent=4)
        
#         print("Dữ liệu đã được lưu vào 'yt_initial_data.json'.")
        
#         # Truy cập vào richGridRenderer -> contents
#         try:
#             # contents = yt_data['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['richGridRenderer']['contents']
            
#             contents = yt_data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"]
        
#             for tab in contents:
#                 if tab.get("tabRenderer", {}).get("selected"):
#                     rich_grid_contents = tab["tabRenderer"]["content"]["richGridRenderer"]["contents"]
#                     rich_items = []
#                     for item in rich_grid_contents:
#                         if "richItemRenderer" in item:
#                             rich_item = item["richItemRenderer"]
#                             # Trích xuất các dữ liệu trong richItemRenderer
#                             rich_items.append(rich_item["content"])
            
#             # Ghi phần nội dung này ra file riêng
#             with open('contentstest.json', 'w', encoding='utf-8') as file:
#                 json.dump(contents, file, ensure_ascii=False, indent=4)
            
#             print("Phần nội dung đã được lưu vào 'contents.json'.")
#         except KeyError:
#             print("Không tìm thấy dữ liệu 'richGridRenderer' hoặc 'contents'.")
#     except json.JSONDecodeError:
#         print("Lỗi: Không thể giải mã JSON từ 'ytInitialData'.")
# else:
#     print("Không tìm thấy 'ytInitialData'.")

    
    
# import json
# import re

# # Đọc HTML nội dung
# with open('video_page.html', 'r', encoding='utf-8') as file:
#     html_content = file.read()

# # Tìm đối tượng ytInitialData trong HTML
# match = re.search(r'var ytInitialData = (\{.*?\});</script>', html_content, re.DOTALL)
# if match:
#     yt_initial_data = match.group(1)
    
#     # Chuyển JSON thành dictionary
#     yt_data = json.loads(yt_initial_data)
    
#     # Duyệt qua richGridRenderer -> contents
#     try:
#         contents = yt_data['contents']
#         with open('j2.json', 'w', encoding='utf-8') as file:
#             file.write(contents)
#         print("HTML content has been saved to j.json")
#     except KeyError:
#         print("Không tìm thấy dữ liệu 'richGridRenderer' hoặc 'contents'.")
# else:
#     print("Không tìm thấy ytInitialData.")



# import re

# def extract_view_count(view_text):
#     """
#     Trích xuất số lượt xem từ chuỗi view_text.
#     Xử lý các trường hợp có đơn vị K, M, B (nghìn, triệu, tỷ).

#     Args:
#         view_text (str): Chuỗi chứa thông tin lượt xem (ví dụ: "1.1K views").
    
#     Returns:
#         int: Số lượt xem dưới dạng số nguyên. Trả về 0 nếu không trích xuất được.
#     """
#     if view_text:
#         # Loại bỏ các ký tự không liên quan, chuẩn hóa chuỗi
#         view_text = view_text.replace(",", "").lower()  # Loại bỏ dấu phẩy và chuyển chữ thường
#         # Tìm số và đơn vị (K, M, B) bằng regex
#         match = re.search(r"(\d+(\.\d+)?)([kmb]?)", view_text)
#         if match:
#             number = float(match.group(1))  # Lấy phần số
#             unit = match.group(3)  # Lấy phần đơn vị (nếu có)
            
#             # Chuyển đổi theo đơn vị
#             if unit == "k":  # Nghìn
#                 return int(number * 1_000)
#             elif unit == "m":  # Triệu
#                 return int(number * 1_000_000)
#             elif unit == "b":  # Tỷ
#                 return int(number * 1_000_000_000)
#             else:  # Không có đơn vị
#                 return int(number)
#     return 0  # Trả về 0 nếu không tìm thấy số

# # Ví dụ dữ liệu
# item = {
#     "shortsLockupViewModel": {
#         "overlayMetadata": {
#             "primaryText": {
#                 "content": "Bàn Thắng Đẹp Nhất Sự Nghiệp Của Quang Hải #shorts"
#             },
#             "secondaryText": {
#                 "content": "899 views"
#             }
#         }
#     }
# }

# # Lấy chuỗi view_text từ JSON
# view_text = item.get("shortsLockupViewModel", {}).get("overlayMetadata", {}).get("secondaryText", {}).get("content", None)

# # Gọi hàm để lấy số lượt xem
# view_count = extract_view_count(view_text)

# print("Số lượt xem:", view_count)

import re
def extract_view_count(view_text):
    
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
    
    
view_text1 = "15 view"
view_text2 = "1.5K views"
view_text3 = "2M views"
view_text4 = "0 view"
view_text5 = "3.2B views"
view_text6 = "views"

print(extract_view_count(view_text1))  # Kết quả: 1
print(extract_view_count(view_text2))  # Kết quả: 1500
print(extract_view_count(view_text3))  # Kết quả: 2000000
print(extract_view_count(view_text4))  # Kết quả: 0
print(extract_view_count(view_text5))  # Kết quả: 3200000000
print(extract_view_count(view_text6))  # Kết quả: 0