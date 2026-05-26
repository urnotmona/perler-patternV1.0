# 拼豆图纸转换核心引擎
# 处理图片像素化、颜色匹配、图纸生成

import io
import math
import base64
from PIL import Image
from bead_colors import MARD_COLORS_221, find_closest_color, rgb_to_hex, COLOR_INDEX, get_colors_by_set


class PatternEngine:
    """拼豆图纸生成引擎"""
    
    # 拼豆板尺寸定义（三种主流板型）
    BOARD_SIZES = {
        "52": {"name": "52钉板(小号)", "size": (52, 52), "total": 2704, "dimension": "14×14cm"},
        "78": {"name": "78钉板(中号)", "size": (78, 78), "total": 6084, "dimension": "21×21cm"},
        "104": {"name": "104钉板(大号)", "size": (104, 104), "total": 10816, "dimension": "28×28cm"},
    }
    
    def __init__(self, board_type="104", color_set="221", margin=0):
        """
        初始化图纸引擎
        board_type: 板型 "52", "78", "104"
        color_set: 色系套装 ("72", "96", "120", "144", "221")
        margin: 边缘留白格数 (0-4)，图案区域四周各留出指定格数的空白
        """
        # 限制边距范围
        self.margin = max(0, min(4, int(margin)))
        # 根据板型获取尺寸
        if board_type in self.BOARD_SIZES:
            board_info = self.BOARD_SIZES[board_type]
            self.board_width = board_info["size"][0]
            self.board_height = board_info["size"][1]
            self.board_type = board_type
            self.board_name = board_info["name"]
        else:
            # 默认使用大板
            self.board_width = 104
            self.board_height = 104
            self.board_type = "104"
            self.board_name = self.BOARD_SIZES["104"]["name"]
        
        self.color_set = color_set
        self.available_colors = get_colors_by_set(color_set)
        self.color_ids = [c["id"] for c in self.available_colors]
        self.enhance_mode = "none"  # "none" | "vivid"
    
    def load_image(self, image_data):
        """加载图片（支持文件数据或base64）"""
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                # 去除base64前缀
                image_data = image_data.split(',')[1]
                image_data = base64.b64decode(image_data)
            
            return Image.open(io.BytesIO(image_data)).convert('RGB')
        else:
            return Image.open(io.BytesIO(image_data)).convert('RGB')
    
    def resize_image(self, img):
        """将图片缩放到目标尺寸，保持宽高比，考虑边缘留白"""
        # 可用区域 = 板尺寸 - 2倍边距
        available_w = self.board_width - 2 * self.margin
        available_h = self.board_height - 2 * self.margin
        
        # 确保可用区域有效
        available_w = max(4, available_w)
        available_h = max(4, available_h)
        
        # 计算缩放比例（基于可用区域）
        width_ratio = available_w / img.width
        height_ratio = available_h / img.height
        ratio = min(width_ratio, height_ratio)
        
        new_width = max(1, int(img.width * ratio))
        new_height = max(1, int(img.height * ratio))
        
        # 使用高质量缩放
        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 创建画布并居中放置（含边距偏移）
        canvas = Image.new('RGB', (self.board_width, self.board_height), (255, 255, 255))
        # 图案在可用区域内居中，再叠加上边距偏移
        offset_x = self.margin + (available_w - new_width) // 2
        offset_y = self.margin + (available_h - new_height) // 2
        canvas.paste(resized, (offset_x, offset_y))
        
        return canvas
    
    def pixelate_image(self, img):
        """像素化处理"""
        return img.resize(
            (self.board_width, self.board_height), 
            Image.Resampling.NEAREST
        )
    
    def enhance_for_beads(self, img):
        """针对拼豆优化的图片预处理：适度提饱和度+提亮度，让颜色干净明亮"""
        from PIL import ImageEnhance
        # 提亮度 1.15x，解决整体偏暗
        img = ImageEnhance.Brightness(img).enhance(1.15)
        # 适度提饱和度 1.2x，避免过度染色
        img = ImageEnhance.Color(img).enhance(1.2)
        # 轻微提对比度，让明暗分明但不过度
        img = ImageEnhance.Contrast(img).enhance(1.1)
        return img
    
    def match_colors(self, img, penalize_gray=False):
        """
        将图片中每个像素匹配到最接近的拼豆颜色
        penalize_gray: 是否对灰色系加惩罚（vivid模式下启用）
        返回: (2D数组-颜色ID, 颜色统计, 处理后的图像)
        """
        width, height = img.size
        pixels = img.load()
        
        # 颜色统计 {色号ID: {"name":名称,"rgb":RGB,"hex":HEX,"count":数量}}
        color_stats = {}
        
        # 2D数组存储颜色ID
        color_grid = [[None for _ in range(width)] for _ in range(height)]
        
        # 处理后的图像
        result_img = Image.new('RGB', (width, height))
        result_pixels = result_img.load()
        
        for y in range(height):
            for x in range(width):
                r, g, b = pixels[x, y]
                
                # 查找最接近的颜色（使用当前套装的颜色）
                color_id, color_name, color_rgb, color_hex, distance = find_closest_color(
                    (r, g, b), 
                    self.color_set,
                    penalize_gray=penalize_gray
                )
                
                color_grid[y][x] = color_id
                result_pixels[x, y] = color_rgb
                
                # 统计
                if color_id not in color_stats:
                    color_stats[color_id] = {
                        "id": color_id,
                        "name": color_name,
                        "rgb": color_rgb,
                        "hex": color_hex,
                        "count": 0
                    }
                color_stats[color_id]["count"] += 1
        
        return color_grid, color_stats, result_img
    
    def generate_pattern(self, image_data, show_grid=True, show_numbers=False, enhance_mode=None):
        """
        生成完整图纸
        enhance_mode: "none" 原始颜色 | "vivid" 自动颜色优化（提饱和度+去灰，推荐）
        返回: {
            "preview_base64": 预览图base64,
            "color_grid": 颜色网格,
            "color_stats": 颜色统计,
            "total_beads": 总颗数,
            "board_size": 尺寸,
            "board_type": 板型,
            "board_name": 板型名称,
            "color_set": 当前使用的色系套装,
            "color_set_name": 套装名称,
            "enhance_mode": 使用的增强模式
        }
        """
        from bead_colors import COLOR_SETS, find_closest_color
        
        # 设置增强模式
        if enhance_mode:
            self.enhance_mode = enhance_mode
        
        # 1. 加载图片
        img = self.load_image(image_data)
        
        # 2. 缩放图片
        resized = self.resize_image(img)
        
        # 2.5 vivid模式下做优化预处理
        if self.enhance_mode == "vivid":
            enhanced = self.enhance_for_beads(resized)
        else:
            enhanced = resized
        
        # 3. 像素化
        pixelated = self.pixelate_image(enhanced)
        
        # 4. 颜色匹配（vivid模式下启用灰色惩罚）
        penalize_gray = (self.enhance_mode == "vivid")
        color_grid, color_stats, matched_img = self.match_colors(pixelated, penalize_gray=penalize_gray)
        
        # 5. 生成预览图（带网格）
        preview = self.create_preview_image(matched_img, show_grid, show_numbers)
        
        # 6. 统计总颗数
        total_beads = sum(s["count"] for s in color_stats.values())
        
        # 7. 按用量排序
        sorted_stats = sorted(
            color_stats.values(), 
            key=lambda x: x["count"], 
            reverse=True
        )
        
        # 获取套装名称
        color_set_name = COLOR_SETS.get(self.color_set, {}).get("name", "未知套装")
        
        return {
            "preview_base64": preview,
            "color_grid": color_grid,
            "color_stats": sorted_stats,
            "total_beads": total_beads,
            "board_size": (self.board_width, self.board_height),
            "board_type": self.board_type,
            "board_name": self.board_name,
            "original_size": (img.width, img.height),
            "color_set": self.color_set,
            "color_set_name": color_set_name,
            "available_colors": len(self.available_colors),
            "enhance_mode": self.enhance_mode
        }
    
    def create_preview_image(self, img, show_grid=True, show_numbers=False):
        """创建带网格的预览图"""
        width, height = img.size
        
        # 根据图片尺寸调整缩放比例，保持预览大小合理
        max_preview_size = 600
        scale = max(8, min(15, int(max_preview_size / max(width, height))))
        
        # 创建放大图
        preview = Image.new('RGB', (width * scale, height * scale), (255, 255, 255))
        
        pixels = img.load()
        
        for y in range(height):
            for x in range(width):
                color = pixels[x, y]
                for dy in range(scale):
                    for dx in range(scale):
                        px = x * scale + dx
                        py = y * scale + dy
                        
                        # 如果是边界，留白
                        if show_grid and (dx == scale - 1 or dy == scale - 1):
                            preview.putpixel((px, py), (200, 200, 200))
                        else:
                            preview.putpixel((px, py), color)
        
        # 转为base64
        buffer = io.BytesIO()
        preview.save(buffer, format='PNG')
        buffer.seek(0)
        
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
    
    def create_grid_image_with_numbers(self, color_grid, cell_size=30):
        """创建带编号的网格图纸"""
        height = len(color_grid)
        width = len(color_grid[0]) if height > 0 else 0
        
        # 创建图像（带边框）
        border = 40
        img_width = width * cell_size + border * 2
        img_height = height * cell_size + border * 2
        
        from PIL import ImageDraw, ImageFont
        
        img = Image.new('RGB', (img_width, img_height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # 自适应加载中文字体（兼容Windows/Mac/Linux）
        from export_utils import _get_font
        try:
            font = _get_font(10)
            small_font = _get_font(8)
        except:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
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
                
                # 绘制色号
                text = color_id
                bbox = draw.textbbox((0, 0), text, font=small_font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                text_x = x1 + (cell_size - text_width) // 2
                text_y = y1 + (cell_size - text_height) // 2
                
                # 根据背景亮度决定文字颜色
                r, g, b = color_info["rgb"]
                text_color = (0, 0, 0) if (r*0.299 + g*0.587 + b*0.114) > 150 else (255, 255, 255)
                
                draw.text((text_x, text_y), text, fill=text_color, font=small_font)
        
        # 绘制网格线
        for i in range(width + 1):
            x = border + i * cell_size
            draw.line([(x, border), (x, img_height - border)], fill=(150, 150, 150), width=1)
        
        for i in range(height + 1):
            y = border + i * cell_size
            draw.line([(border, y), (img_width - border, y)], fill=(150, 150, 150), width=1)
        
        return img
    
    def create_high_quality_preview(self, color_grid, scale=15):
        """创建高质量预览图"""
        height = len(color_grid)
        width = len(color_grid[0]) if height > 0 else 0
        
        img = Image.new('RGB', (width * scale, height * scale), (255, 255, 255))
        
        for y in range(height):
            for x in range(width):
                color_id = color_grid[y][x]
                color_info = COLOR_INDEX.get(color_id, {"rgb": (128, 128, 128)})
                
                for dy in range(scale):
                    for dx in range(scale):
                        px = x * scale + dx
                        py = y * scale + dy
                        
                        # 边界处理
                        if dx == scale - 1 or dy == scale - 1:
                            img.putpixel((px, py), (220, 220, 220))
                        else:
                            img.putpixel((px, py), color_info["rgb"])
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()

    # ==================== V2 新增功能 ====================
    
    @staticmethod
    def flip_horizontal(color_grid):
        """水平翻转颜色网格（烫豆刚需：翻面后图案镜像）"""
        return [row[::-1] for row in color_grid]
    
    @staticmethod
    def grid_to_image(color_grid):
        """从颜色网格重建PIL图像（用于翻转/品牌转换后重新生成预览）"""
        height = len(color_grid)
        width = len(color_grid[0]) if height > 0 else 0
        img = Image.new('RGB', (width, height))
        for y in range(height):
            for x in range(width):
                color_id = color_grid[y][x]
                rgb = COLOR_INDEX.get(color_id, {"rgb": (128, 128, 128)})["rgb"]
                img.putpixel((x, y), rgb)
        return img
    
    @staticmethod
    def remove_noise(color_grid, level='light'):
        """
        去杂色：合并孤立点
        - light: 仅合并周围8格无同色的完全孤立点
        - medium: 合并同色连通区<=2格的小区域
        - heavy: 合并同色连通区<=3格的小区域
        """
        height = len(color_grid)
        width = len(color_grid[0]) if height > 0 else 0
        threshold = {'light': 1, 'medium': 2, 'heavy': 3}.get(level, 1)
        
        if level == 'light':
            # 简单方案：检查8邻域同色数量
            new_grid = [row[:] for row in color_grid]
            for y in range(height):
                for x in range(width):
                    color_id = color_grid[y][x]
                    neighbor_same = 0
                    neighbor_colors = {}
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < height and 0 <= nx < width:
                                n_color = color_grid[ny][nx]
                                if n_color == color_id:
                                    neighbor_same += 1
                                neighbor_colors[n_color] = neighbor_colors.get(n_color, 0) + 1
                    # 周围没有同色→孤立，合并到最多的相邻颜色
                    if neighbor_same == 0 and neighbor_colors:
                        if color_id in neighbor_colors:
                            del neighbor_colors[color_id]
                        if neighbor_colors:
                            most_color = max(neighbor_colors, key=neighbor_colors.get)
                            new_grid[y][x] = most_color
            return new_grid
        else:
            # 中度/重度：先BFS找连通区，再合并小区域
            visited = [[False]*width for _ in range(height)]
            regions = []  # [(color_id, [(y,x), ...])]
            
            for y in range(height):
                for x in range(width):
                    if visited[y][x]:
                        continue
                    color_id = color_grid[y][x]
                    # BFS找同色连通区
                    region = []
                    queue = [(y, x)]
                    visited[y][x] = True
                    while queue:
                        cy, cx = queue.pop(0)
                        region.append((cy, cx))
                        for dy in [-1, 0, 1]:
                            for dx in [-1, 0, 1]:
                                if dy == 0 and dx == 0:
                                    continue
                                ny, nx = cy + dy, cx + dx
                                if 0 <= ny < height and 0 <= nx < width and not visited[ny][nx] and color_grid[ny][nx] == color_id:
                                    visited[ny][nx] = True
                                    queue.append((ny, nx))
                    regions.append((color_id, region))
            
            # 合并小区域
            new_grid = [row[:] for row in color_grid]
            for color_id, region in regions:
                if len(region) > threshold:
                    continue
                # 找到该区域边界上最多的相邻颜色
                neighbor_colors = {}
                for ry, rx in region:
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            if dy == 0 and dx == 0:
                                continue
                            ny, nx = ry + dy, rx + dx
                            if 0 <= ny < height and 0 <= nx < width:
                                n_color = color_grid[ny][nx]
                                if n_color != color_id:
                                    neighbor_colors[n_color] = neighbor_colors.get(n_color, 0) + 1
                if neighbor_colors:
                    most_color = max(neighbor_colors, key=neighbor_colors.get)
                    for ry, rx in region:
                        new_grid[ry][rx] = most_color
            
            return new_grid
    
    @staticmethod
    def re_match_colors(color_grid, new_color_set):
        """
        一键品牌转换：保持图案形状，用新色系重新匹配颜色
        返回: (new_grid, sorted_stats)
        """
        new_colors = get_colors_by_set(new_color_set)
        
        height = len(color_grid)
        width = len(color_grid[0]) if height > 0 else 0
        
        new_grid = [[None for _ in range(width)] for _ in range(height)]
        new_stats = {}
        
        for y in range(height):
            for x in range(width):
                old_id = color_grid[y][x]
                old_rgb = COLOR_INDEX.get(old_id, {"rgb": (128, 128, 128)})["rgb"]
                
                new_id, new_name, new_rgb, new_hex, _ = find_closest_color(
                    old_rgb, new_color_set, penalize_gray=False
                )
                
                new_grid[y][x] = new_id
                
                if new_id not in new_stats:
                    new_stats[new_id] = {
                        "id": new_id,
                        "name": new_name,
                        "rgb": new_rgb,
                        "hex": new_hex,
                        "count": 0
                    }
                new_stats[new_id]["count"] += 1
        
        sorted_stats = sorted(new_stats.values(), key=lambda x: x["count"], reverse=True)
        return new_grid, sorted_stats
