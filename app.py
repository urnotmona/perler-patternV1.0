# 拼豆AI图纸生成器 - Flask主程序

import os
import io
import uuid
import base64
import time
from flask import Flask, render_template, request, jsonify, send_file, Response, g
from pattern_engine import PatternEngine
from export_utils import export_to_png, export_to_pdf, export_to_json, create_grid_image
from bead_colors import get_all_colors, get_colors_by_set, get_available_sets, COLOR_INDEX, rgb_to_hex
from analytics import (
    Analytics, track, get_funnel_stats, get_param_adjust_stats,
    get_popular_configs, get_drop_off_points, get_avg_generate_time, 
    get_overview_stats, get_comparison_stats
)
from auth import (
    get_current_user, is_guest, get_visitor_id, get_user_id,
    wx_login, create_visitor_token, check_permission, record_usage,
    require_login, require_guest_or_login, merge_guest_data
)
import config

app = Flask(__name__)
app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB上限，compress_image自动压缩
app.config['UPLOAD_FOLDER'] = '/tmp/perler_uploads'

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def compress_image(image_data, max_size_kb=2048, max_dimension=1200):
    """
    自动压缩大图
    - 超过 max_size_kb (KB) 时压缩质量
    - 超过 max_dimension (px) 时缩小尺寸
    拼豆图纸最大才104×104像素，输入图超过1200px纯属浪费
    """
    from PIL import Image as PILImage
    
    try:
        # 判断是bytes还是base64字符串
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                raw = base64.b64decode(image_data.split(',')[1])
            else:
                raw = base64.b64decode(image_data)
        else:
            raw = image_data
        
        # 当前大小
        current_size_kb = len(raw) / 1024
        
        # 不需要压缩
        if current_size_kb <= max_size_kb:
            return image_data
        
        img = PILImage.open(io.BytesIO(raw)).convert('RGB')
        w, h = img.size
        
        # 尺寸过大 → 缩小
        if max(w, h) > max_dimension:
            ratio = max_dimension / max(w, h)
            new_w = int(w * ratio)
            new_h = int(h * ratio)
            img = img.resize((new_w, new_h), PILImage.Resampling.LANCZOS)
        
        # 压缩为JPEG，逐步降质量直到体积达标
        quality = 85
        for q in [85, 75, 65, 55, 45]:
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=q)
            result_bytes = buf.getvalue()
            if len(result_bytes) / 1024 <= max_size_kb:
                break
        
        # 返回和输入同格式（bytes或base64字符串）
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                return f"data:image/jpeg;base64,{base64.b64encode(result_bytes).decode()}"
            else:
                return base64.b64encode(result_bytes).decode()
        else:
            return result_bytes
            
    except Exception:
        # 压缩失败就原样返回，不影响主流程
        return image_data

# 存储当前会话的图纸数据
pattern_sessions = {}

# 埋点会话管理
analytics_sessions = {}

# 请求钩子：每个请求初始化用户信息
@app.before_request
def before_request():
    """每个请求前执行"""
    g.current_user = get_current_user()


def get_or_create_analytics():
    """获取埋点实例"""
    user = g.get('current_user')
    
    if user:
        user_type = 'guest' if user.is_guest() else 'logged_in'
        user_id = user.user_id
    else:
        user_type = 'guest'
        user_id = get_visitor_id() or f"anon_{request.remote_addr}"
    
    session_id = get_visitor_id() or get_user_id()
    
    analytics = Analytics(user_type, user_id)
    if session_id:
        analytics.session_id = session_id
    
    return analytics


@app.route('/')
def index():
    """主页"""
    # 埋点
    analytics = get_or_create_analytics()
    analytics.track_event('page_enter', {
        'source': request.referrer or 'direct',
        'is_logged_in': not is_guest()
    })
    
    return render_template('index.html')


# ==================== 认证 API ====================

@app.route('/api/auth/wx-login', methods=['POST'])
def api_wx_login():
    """微信登录"""
    data = request.get_json() or {}
    code = data.get('code', '')
    visitor_id = data.get('visitor_id')  # 游客ID，用于数据迁移
    
    if not code:
        return jsonify({'success': False, 'error': '缺少code参数'})
    
    token, result = wx_login(code)
    
    if not token:
        return jsonify({'success': False, 'error': result})
    
    # 如果有游客ID，合并数据
    if visitor_id and isinstance(result, type(lambda:None).__class__.__bases__[0]):
        try:
            merge_guest_data(visitor_id, result.user_id)
        except:
            pass
    
    return jsonify({
        'success': True,
        'token': token,
        'user': result.to_dict() if hasattr(result, 'to_dict') else {
            'user_id': result.user_id,
            'nickname': result.nickname,
            'role': result.role
        }
    })


@app.route('/api/auth/visitor-token', methods=['POST'])
def api_visitor_token():
    """获取游客token"""
    data = request.get_json() or {}
    visitor_id = data.get('visitor_id')
    
    if not visitor_id:
        visitor_id = f"visitor_{uuid.uuid4().hex[:16]}"
    
    token = create_visitor_token(visitor_id)
    
    return jsonify({
        'success': True,
        'token': token,
        'visitor_id': visitor_id
    })


@app.route('/api/auth/user-info', methods=['GET'])
def api_user_info():
    """获取当前用户信息"""
    user = get_current_user()
    
    if user:
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'is_guest': user.is_guest(),
            'daily_count': user.daily_count,
            'daily_limit': config.GUEST_DAILY_LIMIT if user.is_guest() else config.USER_DAILY_LIMIT
        })
    
    return jsonify({
        'success': True,
        'user': None,
        'is_guest': True
    })


@app.route('/api/auth/login-status', methods=['GET'])
def api_login_status():
    """获取登录状态（简化版）"""
    user = get_current_user()
    
    if user and not user.is_guest():
        return jsonify({
            'logged_in': True,
            'user': {
                'nickname': user.nickname,
                'avatar_url': user.avatar_url
            }
        })
    
    return jsonify({
        'logged_in': False
    })


# ==================== 色号和板型 API ====================

@app.route('/api/colors', methods=['GET'])
def get_colors():
    """获取色号列表"""
    set_name = request.args.get('set_name', '221')
    
    colors = get_colors_by_set(set_name)
    
    return jsonify({
        "success": True,
        "colors": colors,
        "count": len(colors),
        "set_name": set_name
    })


@app.route('/api/color-sets', methods=['GET'])
def get_color_sets():
    """获取所有可用色系套装"""
    sets = get_available_sets()
    
    # 游客限制色系
    if is_guest():
        for set_id in list(sets.keys()):
            if set_id not in config.GUEST_ALLOWED_COLOR_SETS and set_id != '221':
                # 不删除，只标记
                sets[set_id]['restricted'] = True
            else:
                sets[set_id]['restricted'] = False
    
    return jsonify({
        "success": True,
        "sets": sets,
        "default": "221",
        "guest_restricted": is_guest()
    })


@app.route('/api/board-sizes', methods=['GET'])
def get_board_sizes():
    """获取所有可用拼豆板尺寸"""
    boards = PatternEngine.BOARD_SIZES
    
    # 游客限制板型
    if is_guest():
        for board_id in boards:
            boards[board_id]['restricted'] = board_id != config.GUEST_MAX_BOARD
    
    return jsonify({
        "success": True,
        "boards": boards,
        "default": config.GUEST_MAX_BOARD,
        "guest_max_board": config.GUEST_MAX_BOARD,
        "guest_restricted": is_guest()
    })


# ==================== 埋点 API ====================

@app.route('/api/track', methods=['POST'])
def track_event_api():
    """接收前端埋点事件"""
    try:
        data = request.get_json()
        
        event_name = data.get('event')
        session_id = data.get('session_id')
        properties = data.get('properties', {})
        
        if not event_name:
            return jsonify({"success": False, "error": "缺少event参数"})
        
        analytics = get_or_create_analytics()
        if session_id:
            analytics.session_id = session_id
        
        result = analytics.track_event(event_name, properties, session_id)
        
        return jsonify({"success": True, "tracked": result})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/analytics/funnel', methods=['GET'])
def api_funnel():
    """获取漏斗统计数据"""
    date_str = request.args.get('date')
    user_type = request.args.get('user_type')  # 'guest' or 'logged_in'
    stats = get_funnel_stats(date_str, user_type)
    return jsonify({"success": True, "data": stats})


@app.route('/api/analytics/params', methods=['GET'])
def api_params():
    """获取参数调整统计"""
    date_str = request.args.get('date')
    user_type = request.args.get('user_type')
    stats = get_param_adjust_stats(date_str, user_type)
    return jsonify({"success": True, "data": stats})


@app.route('/api/analytics/popular', methods=['GET'])
def api_popular():
    """获取热门配置统计"""
    date_str = request.args.get('date')
    user_type = request.args.get('user_type')
    stats = get_popular_configs(date_str, user_type)
    return jsonify({"success": True, "data": stats})


@app.route('/api/analytics/dropoff', methods=['GET'])
def api_dropoff():
    """获取流失点分析"""
    date_str = request.args.get('date')
    user_type = request.args.get('user_type')
    stats = get_drop_off_points(date_str, user_type)
    return jsonify({"success": True, "data": stats})


@app.route('/api/analytics/generate-time', methods=['GET'])
def api_generate_time():
    """获取平均生成耗时"""
    date_str = request.args.get('date')
    user_type = request.args.get('user_type')
    stats = get_avg_generate_time(date_str, user_type)
    return jsonify({"success": True, "data": stats})


@app.route('/api/analytics/overview', methods=['GET'])
def api_overview():
    """获取总览统计数据"""
    date_str = request.args.get('date')
    user_type = request.args.get('user_type')
    stats = get_overview_stats(date_str, user_type)
    return jsonify({"success": True, "data": stats})


@app.route('/api/analytics/comparison', methods=['GET'])
def api_comparison():
    """获取游客vs登录用户对比"""
    date_str = request.args.get('date')
    stats = get_comparison_stats(date_str)
    return jsonify({"success": True, "data": stats})


# ==================== 生成图纸 API ====================

@app.route('/api/generate-from-image', methods=['POST'])
@require_guest_or_login
def generate_from_image():
    """从上传的图片生成图纸"""
    start_time = time.time()
    analytics = get_or_create_analytics()
    
    try:
        # 检查权限
        allowed, reason, limit_info = check_permission('generate_image')
        if not allowed:
            return jsonify({
                "success": False, 
                "error": reason,
                "code": "LIMITED_ACCESS",
                "limit_info": limit_info
            })
        
        # 获取参数
        board_type = request.form.get('board_type', config.GUEST_MAX_BOARD)
        color_set = request.form.get('color_set', '221')
        enhance_mode = request.form.get('enhance_mode', 'none')  # "none" | "vivid"
        margin = request.form.get('margin', '0')  # 边距格数 0-4
        session_id = request.form.get('session_id')
        show_grid = request.form.get('show_grid', 'true').lower() == 'true'
        show_numbers = request.form.get('show_numbers', 'true').lower() == 'true'
        
        # 验证增强模式
        if enhance_mode not in ('none', 'vivid'):
            enhance_mode = 'none'
        
        # 验证边距
        try:
            margin = max(0, min(4, int(margin)))
        except (ValueError, TypeError):
            margin = 0
        
        # 游客板型限制
        if is_guest() and board_type != config.GUEST_MAX_BOARD:
            board_type = config.GUEST_MAX_BOARD
        
        # 验证板型
        if board_type not in PatternEngine.BOARD_SIZES:
            board_type = config.GUEST_MAX_BOARD
        
        # 游客色系限制
        if is_guest() and color_set not in config.GUEST_ALLOWED_COLOR_SETS:
            color_set = config.GUEST_ALLOWED_COLOR_SETS[0]
        
        # 验证色系套装
        available_sets = get_available_sets()
        if color_set not in available_sets:
            color_set = '221'
        
        # 埋点：生成点击
        analytics.track_event('generate_click', {
            'board_size': board_type,
            'color_set': color_set,
            'mode': 'image',
            'is_guest': is_guest()
        })
        
        # 获取图片数据
        if 'image' not in request.files and 'image_data' not in request.form:
            # 埋点：生成失败
            analytics.track_event('generate_fail', {
                'error_type': 'no_image',
                'duration_ms': int((time.time() - start_time) * 1000),
                'board_size': board_type,
                'color_set': color_set
            })
            
            return jsonify({"success": False, "error": "未提供图片"})
        
        image_data = None
        
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({"success": False, "error": "未选择文件"})
            image_data = file.read()
        else:
            image_data = request.form['image_data']
        
        # 自动压缩大图：超过2MB或尺寸超过1200px时压缩
        image_data = compress_image(image_data)
        
        # 创建引擎并生成图纸
        engine = PatternEngine(board_type=board_type, color_set=color_set, margin=margin)
        result = engine.generate_pattern(image_data, show_grid=show_grid, show_numbers=show_numbers, enhance_mode=enhance_mode)
        
        # 保存会话
        new_session_id = str(uuid.uuid4())
        pattern_sessions[new_session_id] = result
        
        # 记录使用次数
        record_usage()
        
        # 埋点：生成成功
        analytics.track_event('generate_success', {
            'board_size': board_type,
            'color_set': color_set,
            'mode': 'image',
            'duration_ms': int((time.time() - start_time) * 1000),
            'color_count': len(result['color_stats']),
            'total_beads': result['total_beads'],
            'enhance_mode': enhance_mode,
            'margin': margin
        })
        
        return jsonify({
            "success": True,
            "session_id": new_session_id,
            "preview": result["preview_base64"],
            "color_stats": result["color_stats"],
            "total_beads": result["total_beads"],
            "board_size": result["board_size"],
            "board_type": result["board_type"],
            "board_name": result["board_name"],
            "original_size": result["original_size"],
            "color_count": len(result["color_stats"]),
            "color_set": result["color_set"],
            "color_set_name": result["color_set_name"],
            "available_colors": result["available_colors"],
            "enhance_mode": result["enhance_mode"],
            "margin": margin,
            "color_grid": result["color_grid"],
            "is_guest": is_guest(),
            "add_watermark": is_guest()
        })
        
    except Exception as e:
        import traceback
        
        # 埋点：生成失败
        analytics.track_event('generate_fail', {
            'error_type': type(e).__name__,
            'duration_ms': int((time.time() - start_time) * 1000)
        })
        
        return jsonify({
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc()
        })


@app.route('/api/generate-from-text', methods=['POST'])
@require_guest_or_login  # 模拟模式下游客也可使用AI生成
def generate_from_text():
    """从文字描述生成图纸（需要先生成图片）"""
    start_time = time.time()
    analytics = get_or_create_analytics()
    
    try:
        data = request.get_json()
        text_prompt = data.get('prompt', '')
        board_type = data.get('board_type', '104')
        color_set = data.get('color_set', '221')
        enhance_mode = data.get('enhance_mode', 'none')
        margin = data.get('margin', 0)
        
        if enhance_mode not in ('none', 'vivid'):
            enhance_mode = 'none'
        
        try:
            margin = max(0, min(4, int(margin)))
        except (ValueError, TypeError):
            margin = 0
        
        if not text_prompt:
            return jsonify({"success": False, "error": "请输入文字描述"})
        
        # 验证板型
        if board_type not in PatternEngine.BOARD_SIZES:
            board_type = '104'
        
        # 验证色系套装
        available_sets = get_available_sets()
        if color_set not in available_sets:
            color_set = '221'
        
        # 埋点：生成点击
        analytics.track_event('generate_click', {
            'board_size': board_type,
            'color_set': color_set,
            'mode': 'text',
            'prompt_len': len(text_prompt)
        })
        
        # 生成图片：优先使用image_generate，不可用时降级为像素画
        try:
            from image_generate import image_generate
            gen_result = image_generate(
                count=1,
                prompt=f"Pixel art pattern of {text_prompt}, colorful perler bead design, grid based, clean lines, vibrant colors",
                file_prefix="perler_input"
            )
        except ImportError:
            from ai_fallback import image_generate_fallback
            gen_result = image_generate_fallback(text_prompt)
        
        if not gen_result or len(gen_result) == 0:
            analytics.track_event('generate_fail', {
                'error_type': 'image_generate_failed',
                'duration_ms': int((time.time() - start_time) * 1000)
            })
            
            return jsonify({"success": False, "error": "图片生成失败"})
        
        # 读取生成的图片
        image_path = gen_result[0]
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        image_base64 = base64.b64encode(image_data).decode()
        image_data_full = f"data:image/png;base64,{image_base64}"
        
        # 生成图纸
        engine = PatternEngine(board_type=board_type, color_set=color_set, margin=margin)
        result = engine.generate_pattern(image_data_full, show_grid=True, show_numbers=False, enhance_mode=enhance_mode)
        
        # 保存会话
        new_session_id = str(uuid.uuid4())
        pattern_sessions[new_session_id] = result
        
        # 记录使用次数
        record_usage()
        
        # 埋点：生成成功
        analytics.track_event('generate_success', {
            'board_size': board_type,
            'color_set': color_set,
            'mode': 'text',
            'duration_ms': int((time.time() - start_time) * 1000),
            'color_count': len(result['color_stats']),
            'total_beads': result['total_beads'],
            'ai_generated': True
        })
        
        return jsonify({
            "success": True,
            "session_id": new_session_id,
            "preview": result["preview_base64"],
            "color_stats": result["color_stats"],
            "total_beads": result["total_beads"],
            "board_size": result["board_size"],
            "board_type": result["board_type"],
            "board_name": result["board_name"],
            "original_size": result["original_size"],
            "color_count": len(result["color_stats"]),
            "color_set": result["color_set"],
            "color_set_name": result["color_set_name"],
            "available_colors": result["available_colors"],
            "color_grid": result["color_grid"],
            "ai_generated": True
        })
        
    except Exception as e:
        import traceback
        
        analytics.track_event('generate_fail', {
            'error_type': type(e).__name__,
            'duration_ms': int((time.time() - start_time) * 1000)
        })
        
        return jsonify({
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc()
        })


# ==================== V2 新增功能 API ====================

@app.route('/api/flip-pattern/<session_id>', methods=['POST'])
@require_guest_or_login
def flip_pattern(session_id):
    """镜像翻转图纸（烫豆刚需）"""
    if session_id not in pattern_sessions:
        return jsonify({"success": False, "error": "会话不存在或已过期"})
    
    result = pattern_sessions[session_id]
    flipped_grid = PatternEngine.flip_horizontal(result["color_grid"])
    
    # 更新会话数据
    result["color_grid"] = flipped_grid
    result["flipped"] = not result.get("flipped", False)
    
    # 从grid重建图像并生成新预览
    img = PatternEngine.grid_to_image(flipped_grid)
    engine = PatternEngine(result["board_type"], result["color_set"])
    preview = engine.create_preview_image(img)
    result["preview_base64"] = preview
    
    # 重新统计颜色（翻转不改变统计，但为一致性重新计算）
    
    return jsonify({
        "success": True,
        "preview": preview,
        "color_grid": flipped_grid,
        "flipped": result["flipped"]
    })


@app.route('/api/remove-noise/<session_id>', methods=['POST'])
@require_guest_or_login
def remove_noise(session_id):
    """去杂色：合并孤立点"""
    if session_id not in pattern_sessions:
        return jsonify({"success": False, "error": "会话不存在或已过期"})
    
    data = request.get_json() or {}
    level = data.get('level', 'light')
    if level not in ('light', 'medium', 'heavy'):
        level = 'light'
    
    result = pattern_sessions[session_id]
    cleaned_grid = PatternEngine.remove_noise(result["color_grid"], level=level)
    
    # 更新会话
    result["color_grid"] = cleaned_grid
    
    # 重新统计
    new_stats = {}
    for row in cleaned_grid:
        for color_id in row:
            if color_id not in new_stats:
                info = COLOR_INDEX.get(color_id, {"rgb": (128, 128, 128), "name": "未知"})
                hex_color = rgb_to_hex(info["rgb"]) if "rgb" in info else "#808080"
                new_stats[color_id] = {
                    "id": color_id,
                    "name": info.get("name", "未知"),
                    "rgb": info["rgb"],
                    "hex": hex_color,
                    "count": 0
                }
            new_stats[color_id]["count"] += 1
    
    sorted_stats = sorted(new_stats.values(), key=lambda x: x["count"], reverse=True)
    result["color_stats"] = sorted_stats
    result["total_beads"] = sum(s["count"] for s in sorted_stats)
    
    # 重建预览
    img = PatternEngine.grid_to_image(cleaned_grid)
    engine = PatternEngine(result["board_type"], result["color_set"])
    preview = engine.create_preview_image(img)
    result["preview_base64"] = preview
    
    return jsonify({
        "success": True,
        "preview": preview,
        "color_grid": cleaned_grid,
        "color_stats": sorted_stats,
        "total_beads": result["total_beads"],
        "color_count": len(sorted_stats),
        "noise_level": level
    })


@app.route('/api/convert-color-set/<session_id>', methods=['POST'])
@require_guest_or_login
def convert_color_set(session_id):
    """一键品牌转换：用新色系重新匹配颜色"""
    if session_id not in pattern_sessions:
        return jsonify({"success": False, "error": "会话不存在或已过期"})
    
    data = request.get_json() or {}
    new_color_set = data.get('color_set', '221')
    
    # 验证色系
    available_sets = get_available_sets()
    if new_color_set not in available_sets:
        return jsonify({"success": False, "error": "不支持的色系套装"})
    
    result = pattern_sessions[session_id]
    new_grid, new_stats = PatternEngine.re_match_colors(result["color_grid"], new_color_set)
    
    # 更新会话
    result["color_grid"] = new_grid
    result["color_stats"] = new_stats
    result["color_set"] = new_color_set
    result["color_set_name"] = available_sets[new_color_set].get("name", new_color_set + "色套装")
    result["available_colors"] = available_sets[new_color_set].get("color_count", int(new_color_set))
    result["total_beads"] = sum(s["count"] for s in new_stats)
    
    # 重建预览
    img = PatternEngine.grid_to_image(new_grid)
    engine = PatternEngine(result["board_type"], new_color_set)
    preview = engine.create_preview_image(img)
    result["preview_base64"] = preview
    
    return jsonify({
        "success": True,
        "preview": preview,
        "color_grid": new_grid,
        "color_stats": new_stats,
        "total_beads": result["total_beads"],
        "color_count": len(new_stats),
        "color_set": new_color_set,
        "color_set_name": result["color_set_name"],
        "available_colors": result["available_colors"]
    })


# ==================== 导出 API ====================

@app.route('/api/export/<session_id>/<format_type>', methods=['GET'])
@require_guest_or_login  # 模拟模式下游客也可导出
def export_pattern(session_id, format_type):
    """导出图纸"""
    start_time = time.time()
    analytics = get_or_create_analytics()
    
    if session_id not in pattern_sessions:
        return jsonify({"success": False, "error": "会话不存在或已过期"})
    
    result = pattern_sessions[session_id]
    color_grid = result["color_grid"]
    color_stats = result["color_stats"]
    total_beads = result["total_beads"]
    board_size = result["board_size"]
    board_name = result.get("board_name", "未知板型")
    color_set_name = result.get("color_set_name", "未知套装")
    
    # 埋点：导出点击
    analytics.track_event('export_click', {
        'format': format_type,
        'board_size': result.get('board_type', 'unknown'),
        'color_set': result.get('color_set', 'unknown')
    })
    
    temp_dir = app.config['UPLOAD_FOLDER']
    filename_base = f"perler_pattern_{session_id[:8]}"
    
    try:
        if format_type == 'png':
            filename = os.path.join(temp_dir, f"{filename_base}.png")
            export_to_png(color_grid, color_stats, total_beads, filename, cell_size=25, 
                         board_name=board_name, color_set_name=color_set_name)
            mimetype = 'image/png'
            
        elif format_type == 'pdf':
            filename = os.path.join(temp_dir, f"{filename_base}.pdf")
            export_to_pdf(color_grid, color_stats, total_beads, board_size, filename,
                         board_name=board_name, color_set_name=color_set_name)
            mimetype = 'application/pdf'
            
        elif format_type == 'json':
            filename = os.path.join(temp_dir, f"{filename_base}.json")
            export_to_json(color_grid, color_stats, total_beads, board_size, filename,
                          board_name=board_name, color_set_name=color_set_name)
            mimetype = 'application/json'
            
        else:
            analytics.track_event('export_fail', {
                'format': format_type,
                'error_type': 'unsupported_format'
            })
            
            return jsonify({"success": False, "error": "不支持的格式"})
        
        file_size_kb = os.path.getsize(filename) / 1024
        export_duration_ms = int((time.time() - start_time) * 1000)
        
        # 埋点：导出成功
        analytics.track_event('export_success', {
            'format': format_type,
            'file_size_kb': round(file_size_kb, 2),
            'export_duration_ms': export_duration_ms
        })
        
        return send_file(filename, mimetype=mimetype, as_attachment=True, 
                        download_name=os.path.basename(filename))
        
    except Exception as e:
        import traceback
        
        analytics.track_event('export_fail', {
            'format': format_type,
            'error_type': type(e).__name__
        })
        
        return jsonify({
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc()
        })


@app.route('/api/export-base64/<session_id>/<format_type>', methods=['GET'])
@require_guest_or_login
def export_pattern_base64(session_id, format_type):
    """导出图纸（返回base64）"""
    start_time = time.time()
    analytics = get_or_create_analytics()
    
    if session_id not in pattern_sessions:
        return jsonify({"success": False, "error": "会话不存在或已过期"})
    
    result = pattern_sessions[session_id]
    color_grid = result["color_grid"]
    color_stats = result["color_stats"]
    total_beads = result["total_beads"]
    board_size = result["board_size"]
    board_name = result.get("board_name", "未知板型")
    color_set_name = result.get("color_set_name", "未知套装")
    
    analytics.track_event('export_click', {'format': format_type})
    
    temp_dir = app.config['UPLOAD_FOLDER']
    filename_base = f"perler_pattern_{session_id[:8]}"
    
    try:
        if format_type == 'png':
            filename = os.path.join(temp_dir, f"{filename_base}.png")
            export_to_png(color_grid, color_stats, total_beads, filename, cell_size=25,
                         board_name=board_name, color_set_name=color_set_name)
            
        elif format_type == 'pdf':
            filename = os.path.join(temp_dir, f"{filename_base}.pdf")
            export_to_pdf(color_grid, color_stats, total_beads, board_size, filename,
                         board_name=board_name, color_set_name=color_set_name)
            
        elif format_type == 'json':
            filename = os.path.join(temp_dir, f"{filename_base}.json")
            export_to_json(color_grid, color_stats, total_beads, board_size, filename,
                          board_name=board_name, color_set_name=color_set_name)
            
        else:
            return jsonify({"success": False, "error": "不支持的格式"})
        
        with open(filename, 'rb') as f:
            data = f.read()
        
        file_size_kb = len(data) / 1024
        export_duration_ms = int((time.time() - start_time) * 1000)
        
        analytics.track_event('export_success', {
            'format': format_type,
            'file_size_kb': round(file_size_kb, 2),
            'export_duration_ms': export_duration_ms
        })
        
        import mimetypes
        mime_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        base64_data = base64.b64encode(data).decode()
        
        return jsonify({
            "success": True,
            "data": f"data:{mime_type};base64,{base64_data}",
            "filename": os.path.basename(filename)
        })
        
    except Exception as e:
        import traceback
        
        analytics.track_event('export_fail', {
            'format': format_type,
            'error_type': type(e).__name__
        })
        
        return jsonify({
            "success": False, 
            "error": str(e),
            "traceback": traceback.format_exc()
        })


@app.route('/api/preview-hq/<session_id>', methods=['GET'])
def get_hq_preview(session_id):
    """获取高质量预览图"""
    if session_id not in pattern_sessions:
        return jsonify({"success": False, "error": "会话不存在"})
    
    result = pattern_sessions[session_id]
    color_grid = result["color_grid"]
    
    img = create_grid_image(color_grid, cell_size=20, show_numbers=True)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return Response(buffer.getvalue(), mimetype='image/png')


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok", 
        "service": "perler-pattern-generator",
        "wx_login_enabled": config.WX_LOGIN_ENABLED
    })


if __name__ == '__main__':
    print("🎨 拼豆AI图纸生成器启动中...")
    print("📐 支持的板型: 52钉板(小号) / 78钉板(中号) / 104钉板(大号)")
    print("🎯 内置色号: 221种MARD官方颜色")
    print("📦 支持套装: 72/96/120/144/221色")
    print("📊 埋点系统: 已启用")
    print(f"🔐 微信登录: {'已启用' if config.WX_LOGIN_ENABLED else '模拟模式'}")
    print("👤 用户分层: 游客限制 / 登录用户全功能")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=config.FLASK_DEBUG)
