"""
AI文字生成图片的降级方案
当image_generate模块不可用时，用PIL生成简易像素风格图案
"""
import random
from PIL import Image, ImageDraw
import io
import base64

# 简单的颜色映射
COLOR_THEMES = {
    "猫": [(255,165,0), (255,200,100), (200,120,50), (255,220,180), (100,80,60)],
    "狗": [(180,140,100), (220,180,140), (140,100,70), (255,220,180), (80,60,40)],
    "花": [(255,100,150), (255,180,200), (100,200,100), (255,255,100), (200,50,100)],
    "星": [(255,255,100), (255,200,50), (255,255,255), (100,100,200), (50,50,150)],
    "心": [(255,50,80), (255,100,120), (255,150,170), (200,30,60), (255,200,210)],
    "default": [(255,100,100), (100,255,100), (100,100,255), (255,255,100), (255,100,255), (100,255,255)],
}

def generate_pixel_art(prompt, size=200):
    """根据文字描述生成简易像素风格图案"""
    # 选择配色
    colors = COLOR_THEMES["default"]
    for key in COLOR_THEMES:
        if key in prompt:
            colors = COLOR_THEMES[key]
            break
    
    img = Image.new('RGB', (size, size), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    pixel_size = size // 10
    for y in range(0, size, pixel_size):
        for x in range(0, size, pixel_size):
            # 中心区域更可能有颜色（形成图案感）
            cx, cy = abs(x - size//2), abs(y - size//2)
            dist = (cx*cx + cy*cy) ** 0.5
            max_dist = (size//2) * 1.2
            
            if dist < max_dist:
                prob = 1 - (dist / max_dist) * 0.6
                if random.random() < prob:
                    color = random.choice(colors)
                    # 加点随机变化
                    color = tuple(max(0, min(255, c + random.randint(-30, 30))) for c in color)
                    draw.rectangle([x, y, x+pixel_size-1, y+pixel_size-1], fill=color)
    
    return img

def image_generate_fallback(prompt, output_path=None):
    """
    image_generate的降级替代
    返回生成图片的路径列表（与image_generate接口一致）
    """
    img = generate_pixel_art(prompt)
    
    if output_path is None:
        import tempfile
        output_path = tempfile.mktemp(suffix='.png')
    
    img.save(output_path)
    return [output_path]
