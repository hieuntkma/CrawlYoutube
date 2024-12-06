from uuid import uuid4
import random

BOT_CONFIG = {
    "id": "search-yt-001",
    "name": "bot-search-youtube-001",
    "description": "Bot crawl T&T Data by search YouTube",
    "org_id": 2,
    "doc_type" : 1,
    "type": "search",
    "source": "youtube",
    "source_config": {
        "org_id": 2,  # ID của tổ chức sẽ cào
        "crawl_source_code": "yt",
        "crawl_source": 3,
        "source_type": 4,
        "offset": 0,  # Lấy key bắt đầu từ số bao nhiêu
        "limit": 50  # Lấy bao nhiêu key để cào
    },
    "crawl_config": {
        "filter_video" :{
            "today_upload_date": "CAISBAgCEAE",
            "week_upload_date": "CAISBAgDEAE",
        },
        # "max_fails_posts": 10,  # Số bài viết không hợp lệ tối đa
        "chunk_post_length": 25,  # Số lượng bài post được đẩy vào data lake trong một lần
        # "network_time_out": 120000,  # (ms) Thời gian chờ tải mạng
        "delay_range":{
            "min_time" : 3,
            "max_time" : 10
        }
    },
    "logConfig": {
        "logTimeout": 2000  # Thời gian chờ để bắn log lên logStash một lần
    }
}
