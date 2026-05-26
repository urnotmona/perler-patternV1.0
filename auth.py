# 用户认证模块
# 支持微信小程序登录和游客模式

import os
import json
import time
import uuid
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
import config

# ==================== 数据存储 ====================

def _load_users():
    """加载用户数据"""
    if os.path.exists(config.USERS_FILE):
        with open(config.USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def _save_users(users):
    """保存用户数据"""
    with open(config.USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def _load_sessions():
    """加载会话数据"""
    if os.path.exists(config.SESSIONS_FILE):
        with open(config.SESSIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def _save_sessions(sessions):
    """保存会话数据"""
    with open(config.SESSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sessions, f, ensure_ascii=False, indent=2)

# ==================== JWT Token ====================

def generate_token(user_id, is_visitor=False, expiry_days=None):
    """
    生成JWT token
    
    Args:
        user_id: 用户ID
        is_visitor: 是否为游客
        expiry_days: 过期天数
    
    Returns:
        JWT token字符串
    """
    if expiry_days is None:
        expiry_days = config.VISITOR_TOKEN_EXPIRY_HOURS // 24 if is_visitor else config.JWT_EXPIRY_DAYS
    
    expiry_hours = expiry_days * 24
    
    payload = {
        'user_id': user_id,
        'is_visitor': is_visitor,
        'exp': datetime.utcnow() + timedelta(hours=expiry_hours),
        'iat': datetime.utcnow(),
        'token_id': str(uuid.uuid4())
    }
    
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm='HS256')

def decode_token(token):
    """
    解析JWT token
    
    Returns:
        payload字典或None
    """
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

# ==================== 用户管理 ====================

class User:
    """用户类"""
    
    def __init__(self, data):
        self.user_id = data.get('user_id')
        self.openid = data.get('openid')
        self.nickname = data.get('nickname', '微信用户')
        self.avatar_url = data.get('avatar_url', '')
        self.role = data.get('role', 'user')
        self.daily_count = data.get('daily_count', 0)
        self.daily_reset = data.get('daily_reset', '')
        self.created_at = data.get('created_at', '')
        self.last_login = data.get('last_login', '')
        self.visitor_id = data.get('visitor_id', '')  # 关联的游客ID
        self.data = data
    
    def to_dict(self):
        """转换为字典"""
        return {
            'user_id': self.user_id,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'role': self.role,
            'daily_count': self.daily_count,
            'daily_reset': self.daily_reset,
            'is_guest': False
        }
    
    def is_guest(self):
        """是否为游客"""
        return self.data.get('is_visitor', False)
    
    def check_daily_limit(self, limit):
        """检查每日限制"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 重置计数
        if self.daily_reset != today:
            self.daily_count = 0
            self.daily_reset = today
        
        return self.daily_count < limit
    
    def increment_daily_usage(self):
        """增加每日使用次数"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 重置计数
        if self.daily_reset != today:
            self.daily_count = 0
            self.daily_reset = today
        
        self.daily_count += 1
        
        # 保存
        users = _load_users()
        users[self.user_id] = self.data
        _save_users(users)
        
        return self.daily_count
    
    def save(self):
        """保存用户数据"""
        self.data['last_login'] = datetime.now().isoformat() + '+08:00'
        self.data['daily_count'] = self.daily_count
        self.data['daily_reset'] = self.daily_reset
        
        users = _load_users()
        users[self.user_id] = self.data
        _save_users(users)

# ==================== 认证函数 ====================

def get_current_user():
    """
    获取当前用户
    从请求的Authorization header中解析token
    
    Returns:
        User对象或None
    """
    # 先检查g中是否已有
    if hasattr(g, 'current_user'):
        return g.current_user
    
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header:
        g.current_user = None
        return None
    
    # 解析Bearer token
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        g.current_user = None
        return None
    
    token = parts[1]
    payload = decode_token(token)
    
    if not payload:
        g.current_user = None
        return None
    
    user_id = payload.get('user_id')
    is_visitor = payload.get('is_visitor', False)
    
    # 加载用户数据
    users = _load_users()
    
    if user_id in users:
        user = User(users[user_id])
    else:
        # 创建新用户（仅用于游客）
        if is_visitor:
            user_data = {
                'user_id': user_id,
                'is_visitor': True,
                'created_at': datetime.now().isoformat() + '+08:00',
                'daily_count': 0,
                'daily_reset': ''
            }
            users[user_id] = user_data
            _save_users(users)
            user = User(user_data)
        else:
            g.current_user = None
            return None
    
    g.current_user = user
    return user

def is_guest():
    """是否为游客模式"""
    user = get_current_user()
    if user is None:
        return True  # 无token视为游客
    return user.is_guest()

def get_visitor_id():
    """获取当前visitor_id"""
    user = get_current_user()
    if user and user.is_guest():
        return user.user_id
    return None

def get_user_id():
    """获取当前用户ID（登录用户）"""
    user = get_current_user()
    if user and not user.is_guest():
        return user.user_id
    return None

# ==================== 登录接口 ====================

def wx_login(code):
    """
    微信登录
    
    Args:
        code: 微信授权code
    
    Returns:
        (token, user) 或 (None, error_msg)
    """
    if not config.WX_LOGIN_ENABLED:
        # 模拟模式
        return _mock_wx_login(code)
    
    try:
        import requests
        
        # 调用微信接口换取openid
        url = 'https://api.weixin.qq.com/sns/jscode2session'
        params = {
            'appid': config.WX_APPID,
            'secret': config.WX_SECRET,
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'errcode' in data and data['errcode'] != 0:
            return None, f"微信登录失败: {data.get('errmsg', '未知错误')}"
        
        openid = data.get('openid')
        if not openid:
            return None, "获取openid失败"
        
        # 查询或创建用户
        user_id = f"wx_{openid}"
        users = _load_users()
        
        if user_id in users:
            user = User(users[user_id])
        else:
            # 创建新用户
            user_data = {
                'user_id': user_id,
                'openid': openid,
                'nickname': '微信用户',
                'avatar_url': '',
                'role': 'user',
                'daily_count': 0,
                'daily_reset': '',
                'created_at': datetime.now().isoformat() + '+08:00',
                'is_visitor': False
            }
            users[user_id] = user_data
            _save_users(users)
            user = User(user_data)
        
        # 生成token
        token = generate_token(user_id, is_visitor=False)
        
        return token, user
    
    except Exception as e:
        return None, f"登录失败: {str(e)}"

def _mock_wx_login(code):
    """模拟微信登录（开发环境用）"""
    # 生成模拟openid
    openid = f"mock_{code[:16]}"
    user_id = f"wx_{openid}"
    
    users = _load_users()
    
    if user_id in users:
        user = User(users[user_id])
    else:
        user_data = {
            'user_id': user_id,
            'openid': openid,
            'nickname': f'模拟用户{code[:4]}',
            'avatar_url': '',
            'role': 'user',
            'daily_count': 0,
            'daily_reset': '',
            'created_at': datetime.now().isoformat() + '+08:00',
            'is_visitor': False,
            'is_mock': True
        }
        users[user_id] = user_data
        _save_users(users)
        user = User(user_data)
    
    token = generate_token(user_id, is_visitor=False)
    return token, user

def create_visitor_token(visitor_id):
    """
    创建游客token
    
    Args:
        visitor_id: 游客ID
    
    Returns:
        token字符串
    """
    return generate_token(visitor_id, is_visitor=True, expiry_days=1)

# ==================== 权限检查 ====================

def check_permission(action):
    """
    检查权限
    
    Args:
        action: 操作名称
    
    Returns:
        (allowed, reason, limit_info)
    """
    user = get_current_user()
    
    # 公开操作
    public_actions = ['view_colors', 'view_boards', 'view_sets']
    if action in public_actions:
        return True, None, None
    
    # 预览操作（游客限制52板）
    if action in ['generate_preview', 'generate_image']:
        if user is None:
            return True, None, {'max_board': config.GUEST_MAX_BOARD, 'daily_limit': config.GUEST_DAILY_LIMIT}
        
        if user.is_guest():
            # 游客检查板型
            board_type = request.form.get('board_type') or request.args.get('board_type')
            if board_type and board_type != config.GUEST_MAX_BOARD:
                return False, f"登录后可使用{board_type}钉板", {'max_board': config.GUEST_MAX_BOARD}
            
            # 检查每日限制
            if not user.check_daily_limit(config.GUEST_DAILY_LIMIT):
                return False, f"今日生成次数已用完（{config.GUEST_DAILY_LIMIT}次/天）", {'daily_limit': config.GUEST_DAILY_LIMIT}
            
            return True, None, {'max_board': config.GUEST_MAX_BOARD, 'daily_limit': config.GUEST_DAILY_LIMIT}
        
        # 登录用户检查限制
        if not user.check_daily_limit(config.USER_DAILY_LIMIT):
            return False, f"今日生成次数已用完（{config.USER_DAILY_LIMIT}次/天）", {'daily_limit': config.USER_DAILY_LIMIT}
        
        return True, None, {'daily_limit': config.USER_DAILY_LIMIT}
    
    # AI生成（必须登录）
    if action == 'generate_ai':
        if user is None or user.is_guest():
            return False, "AI生成需要登录后使用", None
        return True, None, None
    
    # 导出（必须登录）
    if action == 'export':
        if user is None or user.is_guest():
            return False, "导出功能需要登录后使用", None
        return True, None, None
    
    return True, None, None

def record_usage():
    """记录使用次数"""
    user = get_current_user()
    if user:
        return user.increment_daily_usage()
    return None

# ==================== 数据迁移 ====================

def merge_guest_data(visitor_id, user_id):
    """
    合并游客数据到登录用户
    
    Args:
        visitor_id: 游客ID
        user_id: 登录用户ID
    """
    users = _load_users()
    
    # 标记游客数据已合并
    if visitor_id in users:
        users[visitor_id]['merged_to'] = user_id
        users[visitor_id]['merged_at'] = datetime.now().isoformat() + '+08:00'
        _save_users(users)
    
    # 合并埋点数据（在analytics模块中处理）
    try:
        from analytics import merge_visitor_analytics
        merge_visitor_analytics(visitor_id, user_id)
    except ImportError:
        pass

# ==================== 装饰器 ====================

def require_login(f):
    """必须登录装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if user is None or user.is_guest():
            return jsonify({
                'success': False,
                'error': '需要登录才能使用此功能',
                'code': 'LOGIN_REQUIRED'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

def require_guest_or_login(f):
    """游客或登录均可装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        allowed, reason, limit_info = check_permission('generate_image')
        if not allowed:
            return jsonify({
                'success': False,
                'error': reason,
                'code': 'LIMITED_ACCESS',
                'limit_info': limit_info
            }), 403
        return f(*args, **kwargs)
    return decorated_function
