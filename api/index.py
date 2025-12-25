import os
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from supabase import create_client, Client

# 🟢 1. 路径配置 (确保能找到文件)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
template_dir = os.path.join(root_dir, 'templates')
static_dir = os.path.join(root_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)

# 🟢 配置 Supabase (请确保这里填的是你自己的 URL 和 Key)
SUPABASE_URL = "https://vupgwbjkdvriurufruua.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZ1cGd3YmprZHZyaXVydWZydXVhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjUyODUyOTEsImV4cCI6MjA4MDg2MTI5MX0.Hdk6pmuOdv8EKAZwYqUlhQozEhxPybOWt0I85tgF1Hw"



try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Supabase init failed: {e}")

# 🟢 3. 核武器：读取本地 JS 文件内容的函数
def get_supabase_js_content():
    try:
        # 寻找 static/supabase.min.js
        file_path = os.path.join(static_dir, 'supabase.min.js')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print(f"❌ 严重错误: 找不到文件 {file_path}")
            return "console.error('SERVER ERROR: supabase.min.js not found on server disk');"
    except Exception as e:
        print(f"❌ 读取 JS 文件出错: {e}")
        return f"console.error('SERVER ERROR: {str(e)}');"

# 缓存一下 JS 内容，不用每次请求都读硬盘
SUPABASE_JS_CODE = get_supabase_js_content()

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
        
        return render_template('index.html', 
                               albums=list(albums_dict.values()), 
                               hero_photos=hero_photos,
                               supabase_url=SUPABASE_URL, 
                               supabase_key=SUPABASE_KEY)
    except Exception as e:
        print(f"Home Error: {e}")
        return f"Error loading home: {e}", 500

@app.route('/album/<album_name>')
def show_album(album_name):
    try:
        album_info = supabase.table('albums').select("description").eq('name', album_name).execute()
        album_desc = "这是一个精选相簿。"
        if album_info.data and len(album_info.data) > 0:
            db_desc = album_info.data[0].get('description')
            if db_desc: album_desc = db_desc

        response = supabase.table('photos').select("*").eq('album', album_name).order('taken_at', desc=True).execute()
        
        photo_ids = [p['id'] for p in response.data]
        likes_map = {}
        if photo_ids:
            likes_res = supabase.table('likes').select('photo_id').in_('photo_id', photo_ids).execute()
            for like in likes_res.data:
                pid = like['photo_id']
                likes_map[pid] = likes_map.get(pid, 0) + 1

        grouped_photos = []
        for item in response.data:
            try:
                time_str = item.get('taken_at') or item['created_at']
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                date_label = dt.strftime('%Y年%m月')
            except:
                date_label = "未知日期"

            photo_id = item.get('id')
            photo_data = {
                "id": photo_id, "src": item['url'], "title": item['title'],
                "description": item.get('description', ''), "likes": likes_map.get(photo_id, 0)
            }

            if not grouped_photos or grouped_photos[-1]['date'] != date_label:
                grouped_photos.append({ "date": date_label, "photos": [] })
            grouped_photos[-1]['photos'].append(photo_data)
        
        # 🟢 重点：把读取到的 JS 代码 (supabase_js_code) 传给前端
        return render_template('album.html', 
                               album_name=album_name, 
                               album_desc=album_desc, 
                               grouped_photos=grouped_photos,
                               supabase_url=SUPABASE_URL, 
                               supabase_key=SUPABASE_KEY,
                               supabase_js_code=SUPABASE_JS_CODE) # <--- 传这个变量
    except Exception as e:
        print(f"Album Error: {e}")
        return f"Error loading album: {e}", 500

@app.route('/upload')
def upload_page():
    return render_template('upload.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

@app.route('/login')
def login_page():
    return render_template('login.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

@app.route('/register')
def register_page():
    return render_template('register.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

if __name__ == '__main__':
    app.run(debug=True, port=5001)