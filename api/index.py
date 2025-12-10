import os
from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client, Client

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
    # 1. 获取照片
    response = supabase.table('photos').select("*").eq('album', album_name).execute()
    photos = []
    
    for item in response.data:
        photos.append({
            "src": item['url'],
            "title": item['title'],
            "description": item.get('description', '') # 获取数据库里的描述，如果没有就是空
        })
    
    # 2. 获取相簿说明 (如果代码里没配置，就显示默认文字)
    album_desc = ALBUM_DESCRIPTIONS.get(album_name, "这是一个精选相簿。")

    return render_template('album.html', 
                           album_name=album_name, 
                           album_desc=album_desc, # 传给前端
                           photos=photos)

@app.route('/upload')
def upload_page():
    return render_template('upload.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

if __name__ == '__main__':
    app.run(debug=True, port=5001)