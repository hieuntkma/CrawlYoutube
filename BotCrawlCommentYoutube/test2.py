import json
from langdetect import detect

def is_vietnamese(text):
    try:
        language = detect(text)
        return language == "vi"
    except Exception as e:
        print(f"Lỗi khi phát hiện ngôn ngữ: {e}")
        return False

def filter_vietnamese_data(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as infile:
        data = json.load(infile)

    filtered_data = []

    for item in data:
        content = item.get("content", "")
        description = item.get("description", "")
        
        combined_text = f"{content} {description}".strip()
        
        if combined_text and is_vietnamese(combined_text):
            filtered_data.append(item)

    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(filtered_data, outfile, ensure_ascii=False, indent=4)
        print(f"Đã ghi {len(filtered_data)} bản ghi tiếng Việt vào {output_file}")

# Sử dụng hàm
input_file = "du_lieu_chua_xu_ly.json"  # Đổi thành tệp dữ liệu gốc
output_file = "test.json"  # Tệp kết quả
filter_vietnamese_data(input_file, output_file)