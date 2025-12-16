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
        # 1. 获取所有照片数据 (按上传时间倒序)
        response = supabase.table('photos').select("*").order('created_at', desc=True).execute()
        all_data = response.data

        # 2. 🟢 随机抽取 10 张照片做“顶部轮播展示” (Hero Section)
        # 如果照片总数少于 10 张，就全拿出来；否则随机抽 10 张
        if len(all_data) > 10:
            hero_photos = random.sample(all_data, 10)
        else:
            hero_photos = all_data

        # 3. 🟢 整理相簿列表 (计算每个相簿有多少张、封面是啥)
        albums_dict = {}
        for item in all_data:
            album_name = item.get('album', '默认相簿')
            
            # 如果这个相簿还没统计过，初始化一下
            if album_name not in albums_dict:
                albums_dict[album_name] = {
                    "name": album_name,
                    "cover": item['url'], # 用最新的一张做封面
                    "count": 0
                }
            
            # 计数 +1
            albums_dict[album_name]['count'] += 1
        
        # 渲染首页
        return render_template('index.html', 
                               albums=list(albums_dict.values()), 
                               hero_photos=hero_photos)
                               
    except Exception as e:
        print(f"Error in home: {e}")
        return f"加载首页出错: {e}"

@app.route('/album/<album_name>')
def show_album(album_name):
    try:
        # 1. 🟢 从数据库的 albums 表查询“相簿简介”
        # 使用 single() 因为我们只查一个相簿
        album_info = supabase.table('albums').select("description").eq('name', album_name).execute()
        
        # 设置默认简介
        album_desc = "这是一个精选相簿。"
        
        # 如果数据库里查到了，就覆盖默认值
        if album_info.data and len(album_info.data) > 0:
            db_desc = album_info.data[0].get('description')
            if db_desc:
                album_desc = db_desc

        # 2. 🟢 获取该相簿下的所有照片 (按拍摄时间 taken_at 倒序)
        # 如果没有 taken_at，Supabase 默认处理 (我们在下面代码逻辑里兜底)
        response = supabase.table('photos').select("*").eq('album', album_name).order('taken_at', desc=True).execute()
        
        # 3. 🟢 按月份分组逻辑
        grouped_photos = []
        
        for item in response.data:
            # --- 时间处理逻辑 ---
            try:
                # 优先用拍摄时间 (taken_at)，如果没有就用上传时间 (created_at)
                time_str = item.get('taken_at')
                if not time_str:
                    time_str = item['created_at']
                
                # 解析时间字符串 (处理 ISO 格式)
                # replace('Z', '+00:00') 是为了处理时区后缀
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                
                # 格式化成 "2025年12月" 这样的标签
                date_label = dt.strftime('%Y年%m月')
            except:
                date_label = "未知日期"
            # ------------------

            photo_data = {
                "src": item['url'],
                "title": item['title'],
                "description": item.get('description', '')
            }

            # 如果列表是空的，或者当前照片的月份和上一组不一样，就新建一组
            if not grouped_photos or grouped_photos[-1]['date'] != date_label:
                grouped_photos.append({
                    "date": date_label,
                    "photos": []
                })
            
            # 把照片塞进最后一组里
            grouped_photos[-1]['photos'].append(photo_data)
        
        return render_template('album.html', 
                               album_name=album_name, 
                               album_desc=album_desc, 
                               grouped_photos=grouped_photos)

    except Exception as e:
        print(f"Error in show_album: {e}")
        return f"加载相簿出错: {e}"

@app.route('/upload')
def upload_page():
    # 传递 URL 和 Key 给前端 JS 使用，实现直传
    return render_template('upload.html', supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)

# Vercel 需要这个入口
if __name__ == '__main__':
    app.run(debug=True, port=5001)