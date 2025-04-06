import os
from PIL import Image, ImageDraw, ImageFont
import io

# 確保目標目錄存在
if not os.path.exists('static/images'):
    os.makedirs('static/images')

# 創建一個32x32的圖像
img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 繪製圓形
draw.ellipse((4, 4, 60, 60), fill=(217, 119, 66), outline=(244, 197, 99), width=2)

# 將圖像保存為PNG
png_path = 'static/images/favicon.png'
img.save(png_path)

# 轉換為ICO
ico_path = 'static/images/favicon.ico'
img.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])

print(f"Favicon created successfully at {ico_path}")