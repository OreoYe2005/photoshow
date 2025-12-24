import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client, Client

# 定义模板和静态文件夹位置
app = Flask(__name__, template_folder='../templates', static_folder='../static')

# 🟢 配置 Supabase (请确保这里填的是你自己的 URL 和 Key)
SUPABASE_URL = "https://vupgwbjkdvriurufruua.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ1cGd3YmprZHZyaXVydWZydXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyODUyOTEsImV4cCI6MjA4MDg2MTI5MX0.Hdk6pmuOdv8EKAZwYqUlhQozEhxPybOWt0I85tgF1Hw"


# 初始化客户端
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Supabase 初始化失败: {e}")

@app.route('/')
def home():
    try:
        # 1. 获取所有照片
        response = supabase.table('photos').select("*").order('created_at', desc=True).execute()
        all_data = response.data

        # 2. 随机轮播图
        if len(all_data) > 10:
            hero_photos = random.sample(all_data, 10)
        else:
            hero_photos = all_data

        # 3. 整理相簿
        albums_dict = {}
        for item in all_data:
            album_name = item.get('album', '默认相簿')
            if album_name not in albums_dict:
                albums_dict[album_name] = {
                    "name": album_name,
                    "cover": item['url'],
                    "count": 0
                }
            albums_dict[album_name]['count'] += 1
        
        return render_template('index.html', 
                               albums=list(albums_dict.values()), 
                               hero_photos=hero_photos,
                               supabase_url=SUPABASE_URL, 
                               supabase_key=SUPABASE_KEY)
                               
    except Exception as e:
        print(f"Error in home: {e}")
        return f"加载首页出错 (请检查终端报错): {e}"

@app.route('/album/<album_name>')
def show_album(album_name):
    try:
        # 1. 获取相簿简介
        album_info = supabase.table('albums').select("description").eq('name', album_name).execute()
        album_desc = "这是一个精选相簿。"
        if album_info.data and len(album_info.data) > 0:
            db_desc = album_info.data[0].get('description')
            if db_desc:
                album_desc = db_desc

        # 2. 获取该相簿照片
        response = supabase.table('photos').select("*").eq('album', album_name).order('taken_at', desc=True).execute()
        
        # 3. 获取点赞数据 (优化版：一次性查出)
        photo_ids = [p['id'] for p in response.data]
        likes_map = {}
        
        if photo_ids:
            # 查 likes 表
            likes_res = supabase.table('likes').select('photo_id').in_('photo_id', photo_ids).execute()
            for like in likes_res.data:
                pid = like['photo_id']
                likes_map[pid] = likes_map.get(pid, 0) + 1

        # 4. 分组逻辑
        grouped_photos = []
        for item in response.data:
            try:
                time_str = item.get('taken_at')
                if not time_str: time_str = item['created_at']
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                date_label = dt.strftime('%Y年%m月')
            except:
                date_label = "未知日期"

            photo_id = item.get('id')
            photo_data = {
                "id": photo_id,
                "src": item['url'],
                "title": item['title'],
                "description": item.get('description', ''),
                "likes": likes_map.get(photo_id, 0) # 注入点赞数
            }

            if not grouped_photos or grouped_photos[-1]['date'] != date_label:
                grouped_photos.append({ "date": date_label, "photos": [] })
            grouped_photos[-1]['photos'].append(photo_data)
        
        return render_template('album.html', 
                               album_name=album_name, 
                               album_desc=album_desc, 
                               grouped_photos=grouped_photos,
                               supabase_url=SUPABASE_URL, 
                               supabase_key=SUPABASE_KEY)

    except Exception as e:
        print(f"Error in show_album: {e}")
        return f"加载相簿出错: {e}"

@app.route('/upload')
def upload_page():
    # 传递 Key 给前端 JS
    return render_template('upload.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

# 🟢 修复点：确保这两个路由存在！
@app.route('/login')
def login_page():
    return render_template('login.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

@app.route('/register')
def register_page():
    # 确保 templates 文件夹里真的有 register.html
    return render_template('register.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

if __name__ == '__main__':
    app.run(debug=True, port=5001)