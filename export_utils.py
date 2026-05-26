# 导出功能模块
# 支持导出PNG、PDF、JSON格式

import io
import json
import base64
import os
import sys
from PIL import Image, ImageDraw, ImageFont
from bead_colors import COLOR_INDEX, rgb_to_hex


def _get_font(size=12):
    """自适应获取中文字体，兼容Windows/Mac/Linux"""
    # 候选字体路径（按优先级）
    candidates = [
        # Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/wqy-microhei/wqy-microhei.ttc",
        # Windows
        "C:/Windows/Fonts/msyh.ttc",      # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",     # 黑体
        "C:/Windows/Fonts/simsun.ttc",     # 宋体
        # Mac
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()


def create_grid_image(color_grid, cell_size=30, show_numbers=True, show_border=True):
    """创建带网格的图纸图片"""
    height = len(color_grid)
    width = len(color_grid[0]) if height > 0 else 0
    
    # 边框区域
    border = 50 if show_border else 10
    
    img_width = width * cell_size + border * 2
    img_height = height * cell_size + border * 2
    
    img = Image.new('RGB', (img_width, img_height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # 加载字体
    try:
        title_font = _get_font(14)
        number_font = _get_font(9)
    except:
        title_font = ImageFont.load_default()
        number_font = ImageFont.load_default()
    
    # 绘制标题区域
    if show_border:
        draw.rectangle([0, 0, img_width - 1, border - 10], fill=(245, 245, 245))
        draw.text((border, 8), "拼豆图纸", fill=(60, 60, 60), font=title_font)
        draw.text((img_width - border - 80, 8), f"{width}x{height}", fill=(100, 100, 100), font=title_font)
    
    # 绘制每个格子
    for y in range(height):
        for x in range(width):
            color_id = color_grid[y][x]
            color_info = COLOR_INDEX.get(color_id, {"rgb": (128, 128, 128), "name": "未知"})
            
            x1 = border + x * cell_size
            y1 = border + y * cell_size
            x2 = x1 + cell_size
            y2 = y1 + cell_size
            
            # 填充颜色
            draw.rectangle([x1+1, y1+1, x2-1, y2-1], fill=color_info["rgb"])
            
            # 绘制编号
            if show_numbers:
                text = color_id
                bbox = draw.textbbox((0, 0), text, font=number_font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = x1 + (cell_size - text_width) // 2
                text_y = y1 + (cell_size - text_height) // 2
                
                # 根据背景亮度决定文字颜色
                r, g, b = color_info["rgb"]
                text_color = (0, 0, 0) if (r*0.299 + g*0.587 + b*0.114) > 150 else (255, 255, 255)
                
                draw.text((text_x, text_y), text, fill=text_color, font=number_font)
    
    # 绘制网格线
    for i in range(width + 1):
        x = border + i * cell_size
        draw.line([(x, border), (x, img_height - border)], fill=(180, 180, 180), width=1)
    
    for i in range(height + 1):
        y = border + i * cell_size
        draw.line([(border, y), (img_width - border, y)], fill=(180, 180, 180), width=1)
    
    # 绘制边框
    if show_border:
        draw.rectangle([border, border, img_width - border, img_height - border], outline=(100, 100, 100), width=2)
    
    return img


def add_watermark(img, text="拼豆图纸生成器"):
    """添加水印"""
    from PIL import ImageDraw, ImageFont
    
    draw = ImageDraw.Draw(img)
    
    try:
        font = _get_font(12)
    except:
        font = ImageFont.load_default()
    
    # 在右下角添加水印
    text_width = draw.textlength(text, font=font) if hasattr(draw, 'textlength') else len(text) * 6
    x = img.width - text_width - 20
    y = img.height - 25
    
    # 半透明背景
    overlay = Image.new('RGBA', img.size, (255, 255, 255, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([x - 5, y - 3, img.width, img.height], fill=(255, 255, 255, 180))
    
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    draw.text((x, y), text, fill=(150, 150, 150), font=font)
    
    return img


def export_to_png(color_grid, color_stats, total_beads, filename="pattern.png", cell_size=30, 
                  board_name="104钉板(大号)", color_set_name="221色全色板", add_watermark_flag=False):
    """导出为PNG图片"""
    img = create_grid_image(color_grid, cell_size=cell_size, show_numbers=True)
    
    # 游客模式添加水印
    if add_watermark_flag:
        img = add_watermark(img)
    
    # 添加色号统计区域
    height = len(color_grid)
    width = len(color_grid[0]) if height > 0 else 0
    border = 50
    
    # 在图片底部添加统计信息
    stats_height = min(200, 30 + len(color_stats) * 18)
    new_img = Image.new('RGB', (img.width, img.height + stats_height), (255, 255, 255))
    new_img.paste(img, (0, 0))
    
    draw = ImageDraw.Draw(new_img)
    
    try:
        font = _get_font(11)
        title_font = _get_font(12)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # 绘制统计标题
    title_text = f"{board_name} | {color_set_name} | 共{total_beads}颗"
    draw.text((border, img.height + 5), title_text, fill=(50, 50, 50), font=title_font)
    
    # 绘制每种颜色的统计
    for i, stat in enumerate(color_stats[:20]):  # 最多显示20种
        y = img.height + 28 + i * 16
        
        # 色块
        draw.rectangle([border, y, border + 15, y + 12], fill=stat["rgb"])
        
        # 编号、名称、数量
        text = f"{stat['id']} {stat['name']} × {stat['count']}"
        draw.text((border + 22, y), text, fill=(60, 60, 60), font=font)
    
    if len(color_stats) > 20:
        draw.text((border, img.height + 28 + 20 * 16), f"... 还有{len(color_stats) - 20}种颜色", fill=(100, 100, 100), font=font)
    
    new_img.save(filename, "PNG")
    return filename


def export_to_pdf(color_grid, color_stats, total_beads, board_size, filename="pattern.pdf",
                  board_name="104钉板(大号)", color_set_name="221色全色板",
                  add_watermark_flag=False):
    """导出为PDF文档"""
    try:
        # 尝试使用reportlab
        return export_to_pdf_reportlab(color_grid, color_stats, total_beads, board_size, filename, 
                                       board_name, color_set_name, add_watermark_flag)
    except ImportError:
        # 回退到weasyprint
        try:
            return export_to_pdf_weasyprint(color_grid, color_stats, total_beads, board_size, filename,
                                           board_name, color_set_name, add_watermark_flag)
        except:
            return export_to_pdf_pil(color_grid, color_stats, total_beads, filename,
                                    board_name, color_set_name, add_watermark_flag)


def export_to_pdf_reportlab(color_grid, color_stats, total_beads, board_size, filename,
                            board_name="104钉板(大号)", color_set_name="221色全色板",
                            add_watermark_flag=False):
    """使用reportlab生成PDF"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # 注册中文字体（兼容Windows/Mac/Linux）
    chinese_font = 'Helvetica'
    font_candidates = [
        ('WenQuanYi', '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc'),
        ('MSYaHei', 'C:/Windows/Fonts/msyh.ttc'),
        ('SimHei', 'C:/Windows/Fonts/simhei.ttf'),
        ('SimSun', 'C:/Windows/Fonts/simsun.ttc'),
    ]
    for font_name, font_path in font_candidates:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                chinese_font = font_name
                break
            except:
                continue
    
    width, height = A4
    c = canvas.Canvas(filename, pagesize=A4)
    
    # 第一页：图纸
    c.setFont(chinese_font, 16)
    c.drawString(20*mm, height - 20*mm, "拼豆图纸")
    
    c.setFont(chinese_font, 10)
    c.drawString(20*mm, height - 28*mm, f"板型: {board_name} | 尺寸: {board_size[0]}×{board_size[1]} | 色系: {color_set_name} | 总颗数: {total_beads}")
    
    # 绘制图纸
    img = create_grid_image(color_grid, cell_size=8, show_numbers=True, show_border=False)
    
    # 添加水印
    if add_watermark_flag:
        img = add_watermark(img)
    
    # 调整图片大小以适应页面
    img_width, img_height = img.size
    max_width = width - 40*mm
    max_height = height - 60*mm
    
    scale = min(max_width / img_width, max_height / img_height)
    new_width = img_width * scale
    new_height = img_height * scale
    
    x_offset = (width - new_width) / 2
    y_offset = height - 45*mm - new_height
    
    img = img.resize((int(new_width), int(new_height)), Image.Resampling.NEAREST)
    img_path = filename.replace('.pdf', '_temp.png')
    img.save(img_path)
    
    c.drawImage(img_path, x_offset, y_offset, width=new_width, height=new_height)
    
    # 第二页：色号统计
    c.showPage()
    c.setFont(chinese_font, 14)
    c.drawString(20*mm, height - 20*mm, "色号用量清单")
    
    c.setFont(chinese_font, 10)
    c.drawString(20*mm, height - 30*mm, f"板型: {board_name} | 色系: {color_set_name} | 总颗数: {total_beads} | 颜色种类: {len(color_stats)}")
    
    # 绘制统计表格
    y = height - 45*mm
    c.setFont(chinese_font, 9)
    
    # 表头
    c.drawString(20*mm, y, "序号")
    c.drawString(35*mm, y, "色号")
    c.drawString(55*mm, y, "名称")
    c.drawString(95*mm, y, "颜色")
    c.drawString(120*mm, y, "数量")
    y -= 8*mm
    
    c.line(18*mm, y + 3*mm, 190*mm, y + 3*mm)
    
    for i, stat in enumerate(color_stats):
        if y < 30*mm:
            c.showPage()
            y = height - 20*mm
            c.setFont(chinese_font, 9)
        
        c.drawString(20*mm, y, str(i + 1))
        c.drawString(35*mm, y, stat['id'])
        c.drawString(55*mm, y, stat['name'][:10])
        
        # 颜色色块
        c.setFillColorRGB(stat['rgb'][0]/255, stat['rgb'][1]/255, stat['rgb'][2]/255)
        c.rect(95*mm, y - 2, 10*mm, 6*mm, fill=1)
        c.setFillColorRGB(0, 0, 0)
        
        c.drawString(120*mm, y, str(stat['count']))
        y -= 8*mm
    
    c.save()
    
    # 清理临时文件
    import os
    try:
        os.remove(img_path)
    except:
        pass
    
    return filename


def export_to_pdf_weasyprint(color_grid, color_stats, total_beads, board_size, filename,
                            board_name="104钉板(大号)", color_set_name="221色全色板",
                            add_watermark_flag=False):
    """使用weasyprint生成PDF"""
    watermark_note = "<p style='color:#999;font-size:10px;'>* 游客预览版本</p>" if add_watermark_flag else ""
    
    # 生成HTML内容
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{ size: A4; margin: 20mm; }}
            body {{ font-family: "WenQuanYi Micro Hei", "DejaVu Sans", sans-serif; font-size: 12px; }}
            h1 {{ text-align: center; color: #333; }}
            .info {{ text-align: center; color: #666; margin-bottom: 20px; }}
            .stats-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            .stats-table th, .stats-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .stats-table th {{ background-color: #f5f5f5; }}
            .color-swatch {{ width: 30px; height: 20px; display: inline-block; border: 1px solid #ccc; }}
            .pattern-info {{ margin-top: 10px; color: #666; }}
        </style>
    </head>
    <body>
        <h1>🧩 拼豆图纸</h1>
        <div class="info">
            板型: {board_name} | 尺寸: {board_size[0]}×{board_size[1]} | 色系: {color_set_name} | 总颗数: {total_beads} | 颜色种类: {len(color_stats)}
            {watermark_note}
        </div>
        
        <h2>色号用量清单</h2>
        <table class="stats-table">
            <tr>
                <th>序号</th>
                <th>色号</th>
                <th>名称</th>
                <th>预览</th>
                <th>数量</th>
            </tr>
    """
    
    for i, stat in enumerate(color_stats):
        hex_color = stat.get('hex', rgb_to_hex(stat['rgb']))
        html_content += f"""
            <tr>
                <td>{i + 1}</td>
                <td>{stat['id']}</td>
                <td>{stat['name']}</td>
                <td><span class="color-swatch" style="background-color: {hex_color}"></span></td>
                <td>{stat['count']}</td>
            </tr>
        """
    
    html_content += f"""
        </table>
        <div class="pattern-info">
            <p>板型: {board_name}</p>
            <p>色系套装: {color_set_name}</p>
            <p>Generated by 拼豆AI图纸生成器</p>
        </div>
    </body>
    </html>
    """
    
    from weasyprint import HTML
    HTML(string=html_content).write_pdf(filename)
    
    return filename


def export_to_pdf_pil(color_grid, color_stats, total_beads, filename,
                      board_name="104钉板(大号)", color_set_name="221色全色板",
                      add_watermark_flag=False):
    """使用PIL生成简单PDF（最后备选方案）"""
    # 生成统计图
    img = create_grid_image(color_grid, cell_size=10, show_numbers=False)
    
    # 添加水印
    if add_watermark_flag:
        img = add_watermark(img)
    
    # 添加统计信息
    width, height = img.size
    stats_height = 50 + len(color_stats) * 15
    new_img = Image.new('RGB', (width, height + stats_height), (255, 255, 255))
    new_img.paste(img, (0, 0))
    
    draw = ImageDraw.Draw(new_img)
    
    try:
        font = _get_font(12)
        small_font = _get_font(10)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    draw.text((10, height + 5), f"拼豆图纸 ({board_name} | {color_set_name}) - 总颗数: {total_beads}", fill=(0, 0, 0), font=font)
    
    for i, stat in enumerate(color_stats[:30]):
        y = height + 25 + i * 15
        draw.rectangle([10, y, 25, y + 10], fill=stat["rgb"])
        text = f"{stat['id']} {stat['name']} × {stat['count']}"
        draw.text((30, y), text, fill=(0, 0, 0), font=small_font)
    
    # 保存为图片后返回（无法直接生成PDF时）
    png_filename = filename.replace('.pdf', '.png')
    new_img.save(png_filename)
    
    return png_filename


def export_to_json(color_grid, color_stats, total_beads, board_size, filename="pattern.json",
                   board_name="104钉板(大号)", color_set_name="221色全色板"):
    """导出为JSON数据"""
    data = {
        "version": "2.0",
        "board_type": board_name,
        "color_set": color_set_name,
        "board_size": {
            "width": board_size[0],
            "height": board_size[1]
        },
        "total_beads": total_beads,
        "color_count": len(color_stats),
        "color_stats": [
            {
                "id": stat["id"],
                "name": stat["name"],
                "rgb": list(stat["rgb"]),
                "hex": stat.get("hex", rgb_to_hex(stat["rgb"])),
                "count": stat["count"]
            }
            for stat in color_stats
        ],
        "pattern": [
            [cell for cell in row]
            for row in color_grid
        ]
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filename


def get_preview_base64(img):
    """将PIL图像转为base64"""
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
