import os
from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client, Client
from datetime import datetime

app = Flask(__name__, template_folder='../templates', static_folder='../static')

SUPABASE_URL = "https://vupgwbjkdvriurufruua.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ1cGd3YmprZHZyaXVydWZydXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyODUyOTEsImV4cCI6MjA4MDg2MTI5MX0.Hdk6pmuOdv8EKAZwYqUlhQozEhxPybOWt0I85tgF1Hw"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 🟢 新增：在这里配置你的相簿说明 ---
# 格式： "相簿名": "说明文字"
ALBUM_DESCRIPTIONS = {
    "风光": "记录旅途中的大好河山，每一帧都是壁纸。",
    "人像": "定格每一个动人的瞬间，捕捉眼神里的光。",
    "街拍": "城市的角落，平凡生活中的不平凡。",
    "默认": "我的随手拍。"
}

@app.route('/')
def home():
    # 首页逻辑保持不变
    response = supabase.table('photos').select("*").order('created_at', desc=True).execute()
    data = response.data
    albums_dict = {}

    for item in data:
        album_name = item.get('album', '默认相簿')
        if album_name not in albums_dict:
            albums_dict[album_name] = {
                "name": album_name,
                "cover": item['url'],
                "count": 0
            }
        albums_dict[album_name]['count'] += 1
    
    return render_template('index.html', albums=list(albums_dict.values()))

@app.route('/album/<album_name>')
def show_album(album_name):
    # 1. 获取照片 (确保按时间倒序排列)
    response = supabase.table('photos').select("*").eq('album', album_name).order('created_at', desc=True).execute()
    
    # 2. 分组逻辑
    grouped_photos = []
    
    for item in response.data:
        # 解析时间 (Supabase 返回的是 UTC 时间字符串，如 2025-12-09T...)
        # 注意：这里简单处理，直接取前7位 (YYYY-MM) 做分组其实最快，但为了格式好看我们转换一下
        try:
            # 将字符串转为时间对象
            dt = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            # 格式化成 "2025年12月"
            date_label = dt.strftime('%Y年%m月')
        except:
            date_label = "未知日期"

        # 处理照片数据对象
        photo_data = {
            "src": item['url'],
            "title": item['title'],
            "description": item.get('description', '')
        }

        # 核心算法：如果你是列表里的第一个，或者你的日期和上一组不一样，就新建一组
        if not grouped_photos or grouped_photos[-1]['date'] != date_label:
            grouped_photos.append({
                "date": date_label,
                "photos": []
            })
        
        # 把照片塞进最后一组里
        grouped_photos[-1]['photos'].append(photo_data)
    
    # 获取相簿说明
    album_desc = ALBUM_DESCRIPTIONS.get(album_name, "这是一个精选相簿。")

    # 注意：这里传给前端的变量名变了，以前叫 photos，现在叫 grouped_photos
    return render_template('album.html', 
                           album_name=album_name, 
                           album_desc=album_desc, 
                           grouped_photos=grouped_photos)

@app.route('/upload')
def upload_page():
    return render_template('upload.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

if __name__ == '__main__':
    app.run(debug=True, port=5001)