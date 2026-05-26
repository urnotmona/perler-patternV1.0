# 拼豆图纸生成器配置文件

import os

# Flask配置
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'perler-bead-secret-key-change-in-production')
FLASK_DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

# 数据存储目录
DATA_DIR = '/tmp/perler_data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
SESSIONS_FILE = os.path.join(DATA_DIR, 'sessions.json')

# 确保目录存在
import os
os.makedirs(DATA_DIR, exist_ok=True)

# JWT配置
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
JWT_EXPIRY_DAYS = 7  # 登录token过期时间（天）
VISITOR_TOKEN_EXPIRY_HOURS = 24  # 游客token过期时间（小时）

# 微信小程序配置
WX_APPID = os.environ.get('WX_APPID', '')
WX_SECRET = os.environ.get('WX_SECRET', '')
WX_LOGIN_ENABLED = bool(WX_APPID and WX_SECRET)

# 用户权限配置
GUEST_DAILY_LIMIT = 3  # 游客每日生成次数限制
USER_DAILY_LIMIT = 50  # 登录用户每日生成次数限制

# 游客功能限制
GUEST_MAX_BOARD = '52'  # 游客最大可用板型
GUEST_ALLOWED_COLOR_SETS = ['72', '96']  # 游客可选色系
