#!/usr/bin/env python3
"""
快速替换 Open WebUI 项目中的所有图标文件
使用默认的纯色图标或用户指定的图标
"""

import os
import sys
from PIL import Image, ImageDraw

def create_default_icon():
    """创建一个默认的 TTC 风格图标（基于用户头像的配色）"""
    # 创建一个 1024x1024 的图片
    size = 1024
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 使用青绿色背景（类似用户提供的头像背景）
    background_color = (54, 140, 130)  # 青绿色
    draw.ellipse([0, 0, size, size], fill=background_color)
    
    # 添加简单的文字标识
    try:
        from PIL import ImageFont
        # 尝试使用系统字体
        font_size = 300
        try:
            # macOS 系统字体路径
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            # 使用默认字体
            font = ImageFont.load_default()
    except:
        font = None
    
    # 在中心绘制 "TTC" 文字
    text = "TTC"
    if font:
        # 获取文字边界框
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (size - text_width) // 2
        text_y = (size - text_height) // 2 - 50  # 稍微向上偏移
        draw.text((text_x, text_y), text, fill='white', font=font)
    
    return img

def create_icon_versions(img):
    """从源图片创建不同尺寸的图标版本"""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    sizes = {
        16: None,
        32: None,
        48: None,
        64: None,
        96: None,
        128: None,
        180: None,
        192: None,
        256: None,
        512: None,
        1024: None,
    }
    
    for size in sizes:
        resized_img = img.copy()
        resized_img.thumbnail((size, size), Image.Resampling.LANCZOS)
        
        if resized_img.size[0] != size or resized_img.size[1] != size:
            square_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            x = (size - resized_img.size[0]) // 2
            y = (size - resized_img.size[1]) // 2
            square_img.paste(resized_img, (x, y))
            sizes[size] = square_img
        else:
            sizes[size] = resized_img
    
    return sizes

def create_ico_file(img, output_path):
    """创建 .ico 文件"""
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_images = []
    
    for size in ico_sizes:
        resized_img = img.copy()
        resized_img.thumbnail(size, Image.Resampling.LANCZOS)
        square_img = Image.new('RGBA', size, (0, 0, 0, 0))
        x = (size[0] - resized_img.size[0]) // 2
        y = (size[1] - resized_img.size[1]) // 2
        square_img.paste(resized_img, (x, y))
        ico_images.append(square_img)
    
    ico_images[0].save(output_path, format='ICO', sizes=ico_sizes, append_images=ico_images[1:])

def replace_all_icons(img):
    """替换所有图标文件"""
    sizes = create_icon_versions(img)
    
    replacements = [
        # backend/open_webui/static
        ('backend/open_webui/static/favicon-16x16.png', 16),
        ('backend/open_webui/static/favicon-96x96.png', 96),
        ('backend/open_webui/static/apple-touch-icon.png', 180),
        ('backend/open_webui/static/favicon.png', 256),
        ('backend/open_webui/static/favicon-dark.png', 256),
        ('backend/open_webui/static/logo.png', 512),
        ('backend/open_webui/static/splash.png', 1024),
        ('backend/open_webui/static/splash-dark.png', 1024),
        ('backend/open_webui/static/web-app-manifest-192x192.png', 192),
        ('backend/open_webui/static/web-app-manifest-512x512.png', 512),
        ('backend/open_webui/static/swagger-ui/favicon.png', 96),
        
        # static
        ('static/apple-touch-icon.png', 180),
        ('static/favicon-96x96.png', 96),
        ('static/favicon.png', 256),
        ('static/favicon-dark.png', 256),
        ('static/splash.png', 1024),
        ('static/splash-dark.png', 1024),
        ('static/doge.png', 256),
        ('static/user.png', 256),
        
        # static/static
        ('static/static/apple-touch-icon.png', 180),
        ('static/static/favicon-16x16.png', 16),
        ('static/static/favicon-96x96.png', 96),
        ('static/static/favicon.png', 256),
        ('static/static/favicon-dark.png', 256),
        ('static/static/splash.png', 1024),
        ('static/static/splash-dark.png', 1024),
        ('static/static/web-app-manifest-192x192.png', 192),
        ('static/static/web-app-manifest-512x512.png', 512),
    ]
    
    success_count = 0
    skip_count = 0
    
    for filepath, size in replacements:
        full_path = os.path.join('/Users/4ier/ttc/open-webui', filepath)
        if os.path.exists(full_path):
            print(f"✓ 替换: {filepath}")
            sizes[size].save(full_path, 'PNG', optimize=True)
            success_count += 1
        else:
            print(f"- 跳过: {filepath} (文件不存在)")
            skip_count += 1
    
    # 替换 ICO 文件
    ico_files = [
        'backend/open_webui/static/favicon.ico',
        'static/static/favicon.ico'
    ]
    
    for ico_file in ico_files:
        full_path = os.path.join('/Users/4ier/ttc/open-webui', ico_file)
        if os.path.exists(full_path):
            print(f"✓ 替换: {ico_file}")
            create_ico_file(img, full_path)
            success_count += 1
        else:
            print(f"- 跳过: {ico_file} (文件不存在)")
            skip_count += 1
    
    # 创建 SVG 文件
    import base64
    import io
    
    svg_template = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="256" height="256" viewBox="0 0 256 256">
  <image width="256" height="256" xlink:href="data:image/png;base64,{base64_data}"/>
</svg>'''
    
    buffer = io.BytesIO()
    sizes[256].save(buffer, format='PNG')
    base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    svg_files = [
        'backend/open_webui/static/favicon.svg',
        'static/static/favicon.svg'
    ]
    
    for svg_file in svg_files:
        full_path = os.path.join('/Users/4ier/ttc/open-webui', svg_file)
        if os.path.exists(full_path):
            print(f"✓ 替换: {svg_file}")
            with open(full_path, 'w') as f:
                f.write(svg_template.format(base64_data=base64_data))
            success_count += 1
        else:
            print(f"- 跳过: {svg_file} (文件不存在)")
            skip_count += 1
    
    return success_count, skip_count

def main():
    print("=" * 60)
    print("Open WebUI 图标快速替换工具")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # 使用命令行参数指定的图片
        source_image = sys.argv[1]
        if os.path.exists(source_image):
            print(f"\n使用指定图片: {source_image}")
            try:
                img = Image.open(source_image)
            except Exception as e:
                print(f"❌ 无法打开图片: {e}")
                return 1
        else:
            print(f"❌ 文件不存在: {source_image}")
            return 1
    else:
        # 创建默认图标
        print("\n未指定图片，创建默认 TTC 图标...")
        img = create_default_icon()
        # 保存一份供参考
        img.save('/Users/4ier/ttc/open-webui/default_icon.png')
        print("默认图标已保存到: default_icon.png")
    
    print("\n开始替换图标...")
    print("-" * 40)
    
    success, skip = replace_all_icons(img)
    
    print("-" * 40)
    print(f"\n✅ 完成！成功替换 {success} 个文件，跳过 {skip} 个文件")
    print("\n下一步：")
    print("1. 清除浏览器缓存")
    print("2. 重启 Open WebUI 服务")
    print("3. 硬刷新页面 (Ctrl+Shift+R 或 Cmd+Shift+R)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
