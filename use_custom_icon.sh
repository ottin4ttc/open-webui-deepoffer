#!/bin/bash

# 使用自定义图标替换 Open WebUI 图标的快捷脚本

echo "========================================"
echo "Open WebUI 自定义图标替换工具"
echo "========================================"
echo ""
echo "请将您的图标图片文件拖拽到终端窗口，或输入完整路径："
read -r icon_path

# 去除路径中的引号和空格
icon_path=$(echo "$icon_path" | sed "s/['\"]//g" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')

# 检查文件是否存在
if [ ! -f "$icon_path" ]; then
    echo "❌ 错误：文件不存在: $icon_path"
    exit 1
fi

echo ""
echo "将使用图片: $icon_path"
echo "确认替换所有图标？(y/n): "
read -r confirm

if [ "$confirm" != "y" ]; then
    echo "操作已取消"
    exit 0
fi

# 运行 Python 脚本
python3 /Users/4ier/ttc/open-webui/quick_replace_icons.py "$icon_path"

echo ""
echo "🎉 完成！请清除浏览器缓存并刷新页面查看新图标。"
