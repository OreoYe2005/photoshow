import os
from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client, Client
import time

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# --- 1. 配置 Supabase (请填入你的真实信息) ---
# 为了安全，建议以后放到环境变量里，但现在先直接填
SUPABASE_URL = "https://vupgwbjkdvriurufruua.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ1cGd3YmprZHZyaXVydWZydXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyODUyOTEsImV4cCI6MjA4MDg2MTI5MX0.Hdk6pmuOdv8EKAZwYqUlhQozEhxPybOWt0I85tgF1Hw"

# 初始化客户端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 首页：从数据库获取照片并按相簿分类 ---
@app.route('/')
def home():
    # 从 'photos' 表里查所有数据，按创建时间倒序
    response = supabase.table('photos').select("*").order('created_at', desc=True).execute()
    data = response.data # 这是一个列表

    # 我们需要在 Python 里把数据整理成之前那种 "相簿列表" 的格式
    # 格式目标：[{'name': '人像', 'cover': 'url...', 'count': 5}, ...]
    albums_dict = {}

    for item in data:
        album_name = item.get('album', '默认相簿')
        if album_name not in albums_dict:
            albums_dict[album_name] = {
                "name": album_name,
                "cover": item['url'], # 用第一张图做封面
                "count": 0
            }
        albums_dict[album_name]['count'] += 1
    
    # 转成列表
    albums = list(albums_dict.values())

    return render_template('index.html', albums=albums)

# --- 3. 相簿详情页 ---
@app.route('/album/<album_name>')
def show_album(album_name):
    # 查询指定相簿的所有照片
    response = supabase.table('photos').select("*").eq('album', album_name).execute()
    photos = []
    
    for item in response.data:
        photos.append({
            "src": item['url'],
            "title": item['title']
        })
                
    return render_template('album.html', album_name=album_name, photos=photos)

# --- 4. 上传页面 ---
@app.route('/upload', methods=['GET', 'POST'])
# api/index.py 的 upload_page 部分

@app.route('/upload')
def upload_page():
    # 我们只需要渲染页面，不需要处理 POST 请求了 (上传逻辑移到了前端)
    # 关键：把 Key 传给网页，这样网页里的 JS 才能用
    return render_template('upload.html', 
                         supabase_url=SUPABASE_URL, 
                         supabase_key=SUPABASE_KEY)

if __name__ == '__main__':
    app.run(debug=True, port=5001)