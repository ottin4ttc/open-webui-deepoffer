#!/usr/bin/env python3
"""
替换 Open WebUI 项目中的所有图标文件
使用用户提供的新图标生成不同尺寸的版本
"""

import os
import shutil
from PIL import Image, ImageOps
import io

def create_icon_versions(source_image_path):
    """
    从源图片创建不同尺寸的图标版本
    返回一个字典，包含尺寸和对应的 PIL Image 对象
    """
    # 打开源图片
    img = Image.open(source_image_path)
    
    # 如果图片有透明通道，保留它；否则转换为 RGBA
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # 定义需要的图标尺寸
    sizes = {
        16: None,     # favicon-16x16.png
        96: None,     # favicon-96x96.png
        180: None,    # apple-touch-icon.png (通常是 180x180)
        192: None,    # web-app-manifest-192x192.png
        512: None,    # web-app-manifest-512x512.png
        256: None,    # favicon.png (通常是 256x256 或更大)
        1024: None,   # splash.png (启动画面，可能需要更大)
    }
    
    # 为每个尺寸创建图标
    for size in sizes:
        # 创建一个新的正方形图片
        resized_img = img.copy()
        resized_img.thumbnail((size, size), Image.Resampling.LANCZOS)
        
        # 如果图片不是正方形，创建正方形画布并居中
        if resized_img.size[0] != size or resized_img.size[1] != size:
            square_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            # 计算居中位置
            x = (size - resized_img.size[0]) // 2
            y = (size - resized_img.size[1]) // 2
            square_img.paste(resized_img, (x, y))
            sizes[size] = square_img
        else:
            sizes[size] = resized_img
    
    return sizes, img

def create_ico_file(img, output_path):
    """创建 .ico 文件（包含多个尺寸）"""
    # ICO 文件通常包含这些尺寸
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_images = []
    
    for size in ico_sizes:
        resized_img = img.copy()
        resized_img.thumbnail(size, Image.Resampling.LANCZOS)
        
        # 创建正方形画布
        square_img = Image.new('RGBA', size, (0, 0, 0, 0))
        x = (size[0] - resized_img.size[0]) // 2
        y = (size[1] - resized_img.size[1]) // 2
        square_img.paste(resized_img, (x, y))
        ico_images.append(square_img)
    
    # 保存为 ICO 文件
    ico_images[0].save(output_path, format='ICO', sizes=ico_sizes, append_images=ico_images[1:])

def replace_icons(source_image_path):
    """替换所有图标文件"""
    
    print(f"使用源图片: {source_image_path}")
    
    # 创建不同尺寸的图标版本
    sizes, original_img = create_icon_versions(source_image_path)
    
    # 定义要替换的文件映射
    replacements = [
        # backend/open_webui/static 目录
        ('backend/open_webui/static/favicon-16x16.png', sizes[16]),
        ('backend/open_webui/static/favicon-96x96.png', sizes[96]),
        ('backend/open_webui/static/apple-touch-icon.png', sizes[180]),
        ('backend/open_webui/static/favicon.png', sizes[256]),
        ('backend/open_webui/static/favicon-dark.png', sizes[256]),
        ('backend/open_webui/static/logo.png', sizes[512]),
        ('backend/open_webui/static/splash.png', sizes[1024]),
        ('backend/open_webui/static/splash-dark.png', sizes[1024]),
        ('backend/open_webui/static/web-app-manifest-192x192.png', sizes[192]),
        ('backend/open_webui/static/web-app-manifest-512x512.png', sizes[512]),
        ('backend/open_webui/static/swagger-ui/favicon.png', sizes[96]),
        
        # static 目录
        ('static/apple-touch-icon.png', sizes[180]),
        ('static/favicon-96x96.png', sizes[96]),
        ('static/favicon.png', sizes[256]),
        ('static/favicon-dark.png', sizes[256]),
        ('static/splash.png', sizes[1024]),
        ('static/splash-dark.png', sizes[1024]),
        ('static/doge.png', sizes[256]),
        ('static/user.png', sizes[256]),
        
        # static/static 子目录
        ('static/static/apple-touch-icon.png', sizes[180]),
        ('static/static/favicon-16x16.png', sizes[16]),
        ('static/static/favicon-96x96.png', sizes[96]),
        ('static/static/favicon.png', sizes[256]),
        ('static/static/favicon-dark.png', sizes[256]),
        ('static/static/splash.png', sizes[1024]),
        ('static/static/splash-dark.png', sizes[1024]),
        ('static/static/web-app-manifest-192x192.png', sizes[192]),
        ('static/static/web-app-manifest-512x512.png', sizes[512]),
    ]
    
    # 替换 PNG 文件
    for filepath, img in replacements:
        full_path = os.path.join('/Users/4ier/ttc/open-webui', filepath)
        if os.path.exists(full_path):
            print(f"替换: {filepath}")
            img.save(full_path, 'PNG', optimize=True)
        else:
            print(f"跳过（文件不存在）: {filepath}")
    
    # 替换 ICO 文件
    ico_files = [
        'backend/open_webui/static/favicon.ico',
        'static/static/favicon.ico'
    ]
    
    for ico_file in ico_files:
        full_path = os.path.join('/Users/4ier/ttc/open-webui', ico_file)
        if os.path.exists(full_path):
            print(f"替换: {ico_file}")
            create_ico_file(original_img, full_path)
        else:
            print(f"跳过（文件不存在）: {ico_file}")
    
    # 创建 SVG 文件（简单的嵌入式 PNG）
    svg_template = '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <image width="{width}" height="{height}" xlink:href="data:image/png;base64,{base64_data}"/>
</svg>'''
    
    svg_files = [
        'backend/open_webui/static/favicon.svg',
        'static/static/favicon.svg'
    ]
    
    # 将 PNG 转换为 base64 用于 SVG
    import base64
    buffer = io.BytesIO()
    sizes[256].save(buffer, format='PNG')
    base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    for svg_file in svg_files:
        full_path = os.path.join('/Users/4ier/ttc/open-webui', svg_file)
        if os.path.exists(full_path):
            print(f"替换: {svg_file}")
            svg_content = svg_template.format(
                width=256,
                height=256,
                base64_data=base64_data
            )
            with open(full_path, 'w') as f:
                f.write(svg_content)
        else:
            print(f"跳过（文件不存在）: {svg_file}")
    
    print("\n✅ 图标替换完成！")
    print("\n注意：")
    print("1. 请清除浏览器缓存以查看新图标")
    print("2. 重启应用服务器")
    print("3. 在某些情况下，可能需要硬刷新（Ctrl+Shift+R 或 Cmd+Shift+R）")

if __name__ == "__main__":
    # 提示用户输入源图片路径
    print("=" * 60)
    print("Open WebUI 图标替换工具")
    print("=" * 60)
    
    source_image = input("\n请输入新图标的完整路径（例如: /path/to/icon.png）: ").strip()
    
    if not source_image:
        print("❌ 错误：请提供图标文件路径")
        exit(1)
    
    if not os.path.exists(source_image):
        print(f"❌ 错误：文件不存在: {source_image}")
        exit(1)
    
    try:
        # 测试是否可以打开图片
        test_img = Image.open(source_image)
        test_img.close()
    except Exception as e:
        print(f"❌ 错误：无法打开图片文件: {e}")
        exit(1)
    
    # 确认操作
    print(f"\n将使用 '{source_image}' 替换所有图标文件")
    confirm = input("确定要继续吗？(y/n): ").strip().lower()
    
    if confirm != 'y':
        print("操作已取消")
        exit(0)
    
    print("\n开始替换图标...\n")
    
    try:
        replace_icons(source_image)
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        exit(1)
