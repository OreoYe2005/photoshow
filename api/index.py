import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client, Client

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# 🟢 配置 Supabase (请确保这里填的是你自己的 URL 和 Key)
SUPABASE_URL = "https://vupgwbjkdvriurufruua.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ1cGd3YmprZHZyaXVydWZydXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyODUyOTEsImV4cCI6MjA4MDg2MTI5MX0.Hdk6pmuOdv8EKAZwYqUlhQozEhxPybOWt0I85tgF1Hw"


supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/')
def home():
    try:
        response = supabase.table('photos').select("*").order('created_at', desc=True).execute()
        all_data = response.data
        if len(all_data) > 10:
            hero_photos = random.sample(all_data, 10)
        else:
            hero_photos = all_data
        
        albums_dict = {}
        for item in all_data:
            album_name = item.get('album', '默认相簿')
            if album_name not in albums_dict:
                albums_dict[album_name] = { "name": album_name, "cover": item['url'], "count": 0 }
            albums_dict[album_name]['count'] += 1
        
        # 传递 URL/Key 方便首页做登录状态检查
        return render_template('index.html', albums=list(albums_dict.values()), hero_photos=hero_photos, supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)
    except Exception as e:
        return f"Error: {e}"

@app.route('/album/<album_name>')
def show_album(album_name):
    try:
        # 1. 获取简介
        album_info = supabase.table('albums').select("description").eq('name', album_name).execute()
        album_desc = album_info.data[0].get('description') if album_info.data else "这是一个精选相簿。"

        # 2. 获取照片 (需要 id)
        response = supabase.table('photos').select("*").eq('album', album_name).order('taken_at', desc=True).execute()
        
        # 3. 🟢 获取该相册所有照片的点赞数
        # 技巧：我们直接查 likes 表，找出 photo_id 在当前照片列表里的数据
        photo_ids = [p['id'] for p in response.data]
        likes_data = []
        if photo_ids:
             # 查询 likes 表里所有相关的点赞
            likes_res = supabase.table('likes').select('photo_id').in_('photo_id', photo_ids).execute()
            likes_data = likes_res.data

        # 统计每个 photo_id 的点赞数
        likes_count_map = {}
        for like in likes_data:
            pid = like['photo_id']
            likes_count_map[pid] = likes_count_map.get(pid, 0) + 1

        grouped_photos = []
        for item in response.data:
            # 🟢 确保每张照片都有 ID (为了前端点赞)
            photo_id = item.get('id') 
            
            try:
                time_str = item.get('taken_at') or item['created_at']
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                date_label = dt.strftime('%Y年%m月')
            except:
                date_label = "未知日期"

            photo_data = {
                "id": photo_id, # 传给前端
                "src": item['url'],
                "title": item['title'],
                "description": item.get('description', ''),
                "likes": likes_count_map.get(photo_id, 0) # 点赞数
            }

            if not grouped_photos or grouped_photos[-1]['date'] != date_label:
                grouped_photos.append({ "date": date_label, "photos": [] })
            grouped_photos[-1]['photos'].append(photo_data)
        
        return render_template('album.html', album_name=album_name, album_desc=album_desc, grouped_photos=grouped_photos, supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)
    except Exception as e:
        return f"Error: {e}"

@app.route('/upload')
def upload_page():
    return render_template('upload.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

# 🟢 新增路由
@app.route('/login')
def login_page():
    return render_template('login.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

@app.route('/register')
def register_page():
    return render_template('register.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

if __name__ == '__main__':
    app.run(debug=True, port=5001)