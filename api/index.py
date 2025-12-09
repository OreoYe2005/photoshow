import os
from flask import Flask, render_template

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# 获取图片文件夹的基础路径
BASE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), '../static/images')

# 辅助函数：检查是否是图片
def is_image(filename):
    return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))

# 路由 1: 首页 (展示相簿列表)
@app.route('/')
def home():
    albums = []
    
    # 扫描 static/images 下的所有文件夹
    if os.path.exists(BASE_IMAGE_PATH):
        # 获取所有子文件夹名称
        dirs = [d for d in os.listdir(BASE_IMAGE_PATH) if os.path.isdir(os.path.join(BASE_IMAGE_PATH, d))]
        
        for album_name in dirs:
            album_path = os.path.join(BASE_IMAGE_PATH, album_name)
            # 找一张图做封面 (取文件夹里的第一张图片)
            cover_image = "/static/placeholder.jpg" # 默认图，防止文件夹为空
            files = sorted(os.listdir(album_path))
            for f in files:
                if is_image(f):
                    cover_image = f"/static/images/{album_name}/{f}"
                    break
            
            albums.append({
                "name": album_name,
                "cover": cover_image,
                "count": len([f for f in files if is_image(f)]) # 统计照片数量
            })

    return render_template('index.html', albums=albums)

# 路由 2: 相簿详情页 (展示具体照片)
@app.route('/album/<album_name>')
def show_album(album_name):
    photos = []
    target_folder = os.path.join(BASE_IMAGE_PATH, album_name)
    
    if os.path.exists(target_folder):
        files = sorted(os.listdir(target_folder))
        for f in files:
            if is_image(f):
                photos.append({
                    "src": f"/static/images/{album_name}/{f}",
                    "title": f.split('.')[0]
                })
                
    return render_template('album.html', album_name=album_name, photos=photos)

if __name__ == '__main__':
    app.run(debug=True, port=5001)