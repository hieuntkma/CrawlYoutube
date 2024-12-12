from pymongo import MongoClient

############### Hiếu DB Test  ###############
# try:
#     client = MongoClient("mongodb://localhost:27017/")

#     db = client["ABPCrawlYTB"]
#     if db is None:
#         raise Exception("DB Not Found! ")
    
#     DB_ABPCrawlYTB = db["ABPCrawlYTB"]
#     DB_keyword = db["keyword"]

# except Exception as xx:
#     print(xx)


################ ABP DB #####################
try:
    client = MongoClient("mongodb://root:tRuGz%3Dz_m*7-egJlfaEB@103.97.125.64:5525/")

    db = client["abp_warehouse"]
    if db is None:
        raise Exception("DB Not Found! ")
    else:
        DB_ABPCrawlYTB = db["youtube_posts_temp"]
        DB_keyword = db["facebook_keyword_tt"]
        DB_source_crawl = db["source_crawl"]
    print("Ket noi thanh cong")
    # a = DB_keyword.find({"keyWord":"T&T GROUP"})

        
except Exception as xx:
    print(xx)

