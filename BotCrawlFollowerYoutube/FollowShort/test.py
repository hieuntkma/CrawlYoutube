# import requests
# import json
# import pandas as pd
# from requests.auth import HTTPBasicAuth

# # Define the Elasticsearch query
# query = {
#     "query": {
#         "bool": {
#             "must": [
#                 {"term": {"crawl_source": 3}},
#                 {"term": {"doc_type": 1}},
#                 {"range": {"crawl_time": {"gt": 1733199553}}},
#                 {
#                     "terms": {
#                         "auth_name": [
#                             "Tập đoàn T&T Group",
#                             "Hanoi Football Club",
#                             "Ngân hàng SHB"
#                         ]
#                     }
#                 }
#             ]
#         }
#     },
#     "sort": [
#         {"crawl_time": {"order": "desc"}}
#     ],
#     "size": 100
# }

# # Elasticsearch URL
# url = "http://103.97.125.64:7749/not_classify_org_posts/_search"

# # Authentication credentials
# username = 'elastic'
# password = 'tRuGz=z_m*7-egJlfaEB'

# # Send the request with basic authentication
# response = requests.get(url, headers={"Content-Type": "application/json"}, json=query, auth=HTTPBasicAuth(username, password))

# # Check if the request was successful
# if response.status_code == 200:
#     data = response.json()
    
#     # Prepare data for DataFrame
#     rows = []
#     for hit in data['hits']['hits']:
#         source = hit['_source']
        
#         # Extract the required fields
#         pub_time = source.get('pub_time', '')
#         content = source.get('content', '').encode('utf-8').decode('utf-8')  # Ensure UTF-8 encoding
#         description = source.get('description', '').encode('utf-8').decode('utf-8')  # Ensure UTF-8 encoding
#         url = source.get('url', '')
#         auth_id = source.get('auth_id', '')
#         auth_url = source.get('auth_url', '')
#         auth_name = source.get('auth_name', '')
        
#         # Append the extracted data to rows
#         rows.append([pub_time, content, description, url, auth_id, auth_url, auth_name])
    
#     # Convert rows to DataFrame
#     df = pd.DataFrame(rows, columns=["pub_time", "content", "description", "url", "auth_id", "auth_url", "auth_name"])
    
#     # Save the DataFrame to an Excel file
#     df.to_excel('output_data.xlsx', index=False)

#     print("Data has been saved to output_data.xlsx")
# else:
#     print(f"Error: {response.status_code}, {response.text}")


# # # channel_url = "https://www.youtube.com/@thethao5.1/videos"
# # # auth_url = channel_url.replace("/videos", "")
# # # print(auth_url)

import pandas as pd
import json
from datetime import datetime, timezone

# Load JSON data
with open('data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

# Prepare the data by extracting and ensuring UTF-8 encoding for content and description
formatted_data = []
for item in data:
    pub_time = item.get('pub_time', '') or None
    content = item.get('content', '') or None
    description = item.get('description', '') or None
    
    # Check if content and description are not None before encoding
    if content:
        content = content.encode('utf-8').decode('utf-8')
    if description:
        description = description.encode('utf-8').decode('utf-8')
    
    url = item.get('url', '') or None
    auth_id = item.get('auth_id', '') or None
    auth_url = item.get('auth_url', '') or None
    auth_name = item.get('auth_name', '') or None
    formatted_data.append({
        'pub_time': pub_time,
        'content': content,  # Ensure UTF-8 encoding for content
        'description': description,  # Ensure UTF-8 encoding for description
        'url': url,
        'auth_id': auth_id,
        'auth_url': auth_url,
        'auth_name': auth_name
    })

# Convert the formatted data to a DataFrame
df = pd.DataFrame(formatted_data)

# Ensure the file is not open and the process can write to it
try:
    # Save to Excel file
    df.to_excel('output_data.xlsx', index=False, engine='openpyxl')
    print("Data has been saved to output_data.xlsx")
except PermissionError:
    print("Permission error: The file may be open or locked by another process.")
