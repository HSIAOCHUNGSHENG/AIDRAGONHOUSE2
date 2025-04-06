import os
from cairosvg import svg2png
from PIL import Image

# 確保目標目錄存在
if not os.path.exists('static/images'):
    os.makedirs('static/images')

# SVG文件內容 - 直接嵌入而不是從文件讀取
svg_content = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
  <circle cx="16" cy="16" r="15" fill="#D97742" stroke="#F4C563" stroke-width="2"/>
  <text x="16" y="22" font-family="Arial" font-size="18" font-weight="bold" text-anchor="middle" fill="#FFFFFF">臥</text>
</svg>'''

# 先轉換成PNG
png_path = 'static/images/favicon.png'
svg2png(bytestring=svg_content, write_to=png_path, output_width=256, output_height=256)

# 然後轉換成ICO
ico_path = 'static/images/favicon.ico'
img = Image.open(png_path)
# 創建多個尺寸的圖像以保證兼容性
img.save(ico_path, sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])

print(f"Favicon created successfully at {ico_path}")