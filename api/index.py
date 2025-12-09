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
def upload_page():
    if request.method == 'GET':
        return render_template('upload.html')
    
    # 处理上传逻辑
    if request.method == 'POST':
        file = request.files.get('file')
        password = request.form.get('password')
        album = request.form.get('album') # 获取用户输入的相簿名

        if password != "oreo2025": # 简单的密码保护
            return "密码错误！"

        if file:
            # 1. 上传文件到 Storage
            # 为了防止重名覆盖，我们在文件名前加个时间戳
            filename = f"{int(time.time())}_{file.filename}"
            file_bytes = file.read() # 读取文件内容
            
            # 上传到 'photos' 桶
            res = supabase.storage.from_("photos").upload(filename, file_bytes, {"content-type": file.content_type})
            
            # 2. 获取公开访问链接
            public_url = supabase.storage.from_("photos").get_public_url(filename)
            
            # 3. 把信息写入 Database
            data = {
                "title": file.filename.split('.')[0],
                "url": public_url,
                "album": album if album else "未分类"
            }
            supabase.table('photos').insert(data).execute()

            return redirect(url_for('home'))
    
    return "上传失败"

if __name__ == '__main__':
    app.run(debug=True, port=5001)