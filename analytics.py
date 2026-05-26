# 用户行为埋点模块
# 轻量级埋点系统，支持本地JSON存储和统计分析

import os
import json
import uuid
from datetime import datetime, timedelta
from collections import defaultdict

# 埋点数据存储目录
ANALYTICS_DIR = '/tmp/perler_analytics'

# 漏斗事件定义（按顺序）
FUNNEL_EVENTS = [
    'page_enter',
    'mode_select',
    'input_complete',
    'param_adjust',
    'generate_click',
    'generate_success',
    'preview_interact',
    'regenerate',
    'export_click',
    'export_success',
    'share_click',
    'page_leave'
]

# 漏斗事件中文名称
FUNNEL_NAMES = {
    'page_enter': '进入页面',
    'mode_select': '选择模式',
    'input_complete': '完成输入',
    'param_adjust': '调整参数',
    'generate_click': '点击生成',
    'generate_success': '生成成功',
    'preview_interact': '预览交互',
    'regenerate': '重新生成',
    'export_click': '点击导出',
    'export_success': '导出成功',
    'share_click': '点击分享',
    'page_leave': '离开页面'
}


class Analytics:
    """埋点分析类"""
    
    def __init__(self, user_type='guest', user_id=None):
        """初始化埋点模块"""
        self.user_type = user_type  # 'guest' or 'logged_in'
        self.user_id = user_id      # 游客visitor_id 或 用户openid
        self.session_id = str(uuid.uuid4())
        self.adjust_count = defaultdict(int)  # 记录参数调整次数
        self.events = []  # 当前会话的事件列表
        
        # 确保目录存在
        os.makedirs(ANALYTICS_DIR, exist_ok=True)
    
    def _get_date_file(self, date_str=None):
        """获取指定日期的数据文件路径"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        return os.path.join(ANALYTICS_DIR, f'events_{date_str}.jsonl')
    
    def _write_event(self, event_data):
        """写入事件到文件"""
        date_str = datetime.now().strftime('%Y-%m-%d')
        filepath = self._get_date_file(date_str)
        
        with open(filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event_data, ensure_ascii=False) + '\n')
    
    def track_event(self, event_name, properties=None, session_id=None):
        """
        记录埋点事件
        
        Args:
            event_name: 事件名称
            properties: 事件属性字典
            session_id: 会话ID（可选）
        
        Returns:
            事件数据字典
        """
        if properties is None:
            properties = {}
        
        # 记录调整次数
        if event_name == 'param_adjust':
            param_name = properties.get('param_name', 'unknown')
            self.adjust_count[param_name] += 1
            properties['adjust_count'] = self.adjust_count[param_name]
        
        # 构建事件数据
        event_data = {
            'event': event_name,
            'session_id': session_id or self.session_id,
            'timestamp': datetime.now().isoformat() + '+08:00',
            'properties': properties,
            'user_type': self.user_type,
            'user_id': self.user_id or 'anonymous'
        }
        
        # 记录到当前会话
        self.events.append(event_data)
        
        # 异步写入文件（不阻塞主流程）
        try:
            self._write_event(event_data)
        except Exception as e:
            print(f"埋点写入失败: {e}")
        
        return event_data
    
    def reset_session(self):
        """重置会话ID"""
        self.session_id = str(uuid.uuid4())
        self.adjust_count = defaultdict(int)
        self.events = []
    
    def set_user(self, user_type, user_id):
        """设置用户信息"""
        self.user_type = user_type
        self.user_id = user_id


def get_analytics(user_type='guest', user_id=None):
    """获取埋点分析实例"""
    return Analytics(user_type, user_id)


def read_events(date_str=None):
    """读取指定日期的所有事件"""
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    filepath = os.path.join(ANALYTICS_DIR, f'events_{date_str}.jsonl')
    
    if not os.path.exists(filepath):
        return []
    
    events = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except:
                    continue
    
    return events


def filter_events(events, user_type=None, user_id=None):
    """过滤事件"""
    if user_type is None and user_id is None:
        return events
    
    filtered = []
    for event in events:
        if user_type and event.get('user_type') != user_type:
            continue
        if user_id and event.get('user_id') != user_id:
            continue
        filtered.append(event)
    
    return filtered


def get_funnel_stats(date_str=None, user_type=None):
    """
    获取漏斗各步骤的转化率统计
    
    Args:
        date_str: 日期字符串，格式 YYYY-MM-DD
        user_type: 过滤用户类型 'guest' 或 'logged_in'
    
    Returns:
        {
            'events': {event_name: count},
            'funnel': [{'name': ..., 'count': ..., 'rate': ...}],
            'total_sessions': int,
            'conversion_rates': {next_event: rate},
            'user_type': str
        }
    """
    events = read_events(date_str)
    events = filter_events(events, user_type)
    
    if not events:
        return {
            'events': {},
            'funnel': [],
            'total_sessions': 0,
            'conversion_rates': {},
            'user_type': user_type or 'all'
        }
    
    # 统计各事件数量
    event_counts = defaultdict(int)
    sessions = set()
    
    for event in events:
        event_name = event['event']
        event_counts[event_name] += 1
        sessions.add(event['session_id'])
    
    # 构建漏斗数据
    funnel = []
    prev_count = None
    
    for event_name in FUNNEL_EVENTS:
        count = event_counts.get(event_name, 0)
        name = FUNNEL_NAMES.get(event_name, event_name)
        
        if prev_count is not None and prev_count > 0:
            rate = (count / prev_count) * 100
        elif count > 0:
            rate = 100.0
        else:
            rate = 0.0
        
        funnel.append({
            'event': event_name,
            'name': name,
            'count': count,
            'rate': round(rate, 2)
        })
        
        prev_count = count
    
    return {
        'events': dict(event_counts),
        'funnel': funnel,
        'total_sessions': len(sessions),
        'conversion_rates': _calculate_conversion_rates(event_counts),
        'user_type': user_type or 'all'
    }


def _calculate_conversion_rates(event_counts):
    """计算相邻步骤的转化率"""
    rates = {}
    
    for i in range(len(FUNNEL_EVENTS) - 1):
        current_event = FUNNEL_EVENTS[i]
        next_event = FUNNEL_EVENTS[i + 1]
        
        current_count = event_counts.get(current_event, 0)
        next_count = event_counts.get(next_event, 0)
        
        if current_count > 0:
            rate = (next_count / current_count) * 100
            rates[f'{current_event}_to_{next_event}'] = round(rate, 2)
    
    return rates


def get_param_adjust_stats(date_str=None, user_type=None):
    """
    获取参数调整统计
    
    Returns:
        {
            'total_adjusts': int,
            'by_param': {param_name: count},
            'by_value_change': [{from, to, count}]
        }
    """
    events = read_events(date_str)
    events = filter_events(events, user_type)
    
    total_adjusts = 0
    by_param = defaultdict(int)
    by_value_change = defaultdict(int)
    
    for event in events:
        if event['event'] == 'param_adjust':
            total_adjusts += 1
            props = event['properties']
            
            param_name = props.get('param_name', 'unknown')
            by_param[param_name] += 1
            
            old_val = props.get('old_value', 'N/A')
            new_val = props.get('new_value', 'N/A')
            by_value_change[f'{old_val} -> {new_val}'] += 1
    
    # 排序
    by_param_sorted = dict(sorted(by_param.items(), key=lambda x: x[1], reverse=True))
    by_value_change_sorted = dict(
        sorted(by_value_change.items(), key=lambda x: x[1], reverse=True)[:20]
    )
    
    return {
        'total_adjusts': total_adjusts,
        'by_param': by_param_sorted,
        'top_value_changes': by_value_change_sorted
    }


def get_popular_configs(date_str=None, user_type=None):
    """
    获取最受欢迎的板型+色系组合
    
    Returns:
        {
            'top_configs': [{board_size, color_set, count}],
            'top_boards': {board_size: count},
            'top_color_sets': {color_set: count}
        }
    """
    events = read_events(date_str)
    events = filter_events(events, user_type)
    
    configs = defaultdict(int)
    boards = defaultdict(int)
    color_sets = defaultdict(int)
    
    for event in events:
        if event['event'] == 'generate_click':
            props = event['properties']
            board_size = props.get('board_size', 'unknown')
            color_set = props.get('color_set', 'unknown')
            
            configs[f'{board_size}+{color_set}'] += 1
            boards[board_size] += 1
            color_sets[color_set] += 1
    
    # 排序并取Top10
    top_configs = sorted(configs.items(), key=lambda x: x[1], reverse=True)[:10]
    top_configs = [
        {'board_size': c.split('+')[0], 'color_set': c.split('+')[1], 'count': cnt}
        for c, cnt in top_configs
    ]
    
    return {
        'top_configs': top_configs,
        'top_boards': dict(sorted(boards.items(), key=lambda x: x[1], reverse=True)),
        'top_color_sets': dict(sorted(color_sets.items(), key=lambda x: x[1], reverse=True))
    }


def get_drop_off_points(date_str=None, user_type=None):
    """
    获取流失最严重的步骤
    
    Returns:
        {
            'drop_off_steps': [{event, drop_count, drop_rate}],
            'biggest_drop': {event, drop_count, drop_rate}
        }
    """
    stats = get_funnel_stats(date_str, user_type)
    
    drop_offs = []
    
    for i in range(len(stats['funnel']) - 1):
        current = stats['funnel'][i]
        next_step = stats['funnel'][i + 1]
        
        if current['count'] > 0:
            drop_count = current['count'] - next_step['count']
            drop_rate = (drop_count / current['count']) * 100
            
            drop_offs.append({
                'from_event': current['event'],
                'from_name': current['name'],
                'to_event': next_step['event'],
                'to_name': next_step['name'],
                'drop_count': drop_count,
                'drop_rate': round(drop_rate, 2)
            })
    
    # 按流失率排序
    drop_offs_sorted = sorted(drop_offs, key=lambda x: x['drop_rate'], reverse=True)
    
    biggest = drop_offs_sorted[0] if drop_offs_sorted else None
    
    return {
        'drop_off_steps': drop_offs_sorted[:5],
        'biggest_drop': biggest
    }


def get_avg_generate_time(date_str=None, user_type=None):
    """
    获取平均生成耗时
    
    Returns:
        {
            'avg_duration_ms': float,
            'min_duration_ms': int,
            'max_duration_ms': int,
            'count': int,
            'by_board_size': {board_size: avg_ms}
        }
    """
    events = read_events(date_str)
    events = filter_events(events, user_type)
    
    durations = []
    by_board = defaultdict(list)
    
    for event in events:
        if event['event'] == 'generate_success':
            props = event['properties']
            duration = props.get('duration_ms', 0)
            
            if duration > 0:
                durations.append(duration)
                
                board_size = props.get('board_size', 'unknown')
                by_board[board_size].append(duration)
    
    if not durations:
        return {
            'avg_duration_ms': 0,
            'min_duration_ms': 0,
            'max_duration_ms': 0,
            'count': 0,
            'by_board_size': {}
        }
    
    by_board_avg = {
        board: sum(durations) / len(durations)
        for board, durations in by_board.items()
    }
    
    return {
        'avg_duration_ms': round(sum(durations) / len(durations), 2),
        'min_duration_ms': min(durations),
        'max_duration_ms': max(durations),
        'count': len(durations),
        'by_board_size': {k: round(v, 2) for k, v in by_board_avg.items()}
    }


def get_overview_stats(date_str=None, user_type=None):
    """
    获取总览统计数据
    
    Returns:
        {
            'date': str,
            'total_sessions': int,
            'total_generates': int,
            'total_exports': int,
            'avg_colors_used': float,
            'avg_beads': float,
            'success_rate': float,
            'top_board': str,
            'top_color_set': str,
            'user_type': str
        }
    """
    events = read_events(date_str)
    events = filter_events(events, user_type)
    
    if not events:
        return {
            'date': date_str or datetime.now().strftime('%Y-%m-%d'),
            'total_sessions': 0,
            'total_generates': 0,
            'total_exports': 0,
            'avg_colors_used': 0,
            'avg_beads': 0,
            'success_rate': 0,
            'top_board': 'N/A',
            'top_color_set': 'N/A',
            'user_type': user_type or 'all'
        }
    
    sessions = set()
    generates = 0
    successes = 0
    exports = 0
    colors_list = []
    beads_list = []
    boards = defaultdict(int)
    color_sets = defaultdict(int)
    
    for event in events:
        sessions.add(event['session_id'])
        
        if event['event'] == 'generate_click':
            generates += 1
            props = event['properties']
            boards[props.get('board_size', 'unknown')] += 1
            color_sets[props.get('color_set', 'unknown')] += 1
        
        elif event['event'] == 'generate_success':
            successes += 1
            props = event['properties']
            colors_list.append(props.get('color_count', 0))
            beads_list.append(props.get('total_beads', 0))
        
        elif event['event'] == 'export_click':
            exports += 1
    
    # 计算平均值
    avg_colors = sum(colors_list) / len(colors_list) if colors_list else 0
    avg_beads = sum(beads_list) / len(beads_list) if beads_list else 0
    success_rate = (successes / generates * 100) if generates > 0 else 0
    
    # 获取最热门
    top_board = max(boards.items(), key=lambda x: x[1])[0] if boards else 'N/A'
    top_color_set = max(color_sets.items(), key=lambda x: x[1])[0] if color_sets else 'N/A'
    
    return {
        'date': date_str or datetime.now().strftime('%Y-%m-%d'),
        'total_sessions': len(sessions),
        'total_generates': generates,
        'total_exports': exports,
        'avg_colors_used': round(avg_colors, 1),
        'avg_beads': round(avg_beads, 0),
        'success_rate': round(success_rate, 2),
        'top_board': top_board,
        'top_color_set': top_color_set,
        'user_type': user_type or 'all'
    }


def merge_visitor_analytics(visitor_id, user_id):
    """
    合并游客埋点数据到登录用户
    
    Args:
        visitor_id: 游客ID
        user_id: 登录用户ID
    """
    # 更新历史埋点文件中的user_id
    import glob
    
    pattern = os.path.join(ANALYTICS_DIR, 'events_*.jsonl')
    
    for filepath in glob.glob(pattern):
        try:
            # 读取所有事件
            events = []
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        event = json.loads(line)
                        if event.get('user_id') == visitor_id:
                            event['user_id'] = user_id
                            event['user_type'] = 'logged_in'
                            event['merged_from'] = visitor_id
                        events.append(event)
            
            # 写回文件
            with open(filepath, 'w', encoding='utf-8') as f:
                for event in events:
                    f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        except Exception as e:
            print(f"合并埋点数据失败: {e}")


def get_comparison_stats(date_str=None):
    """
    获取游客vs登录用户的对比统计
    
    Returns:
        {
            'guest': {...overview},
            'logged_in': {...overview},
            'comparison': {
                'sessions_ratio': float,
                'generates_ratio': float,
                'export_ratio': float
            }
        }
    """
    guest_stats = get_overview_stats(date_str, 'guest')
    logged_in_stats = get_overview_stats(date_str, 'logged_in')
    
    guest_sessions = guest_stats.get('total_sessions', 0) or 1
    logged_sessions = logged_in_stats.get('total_sessions', 0) or 1
    guest_generates = guest_stats.get('total_generates', 0) or 0
    logged_generates = logged_in_stats.get('total_generates', 0) or 1
    guest_exports = guest_stats.get('total_exports', 0) or 0
    logged_exports = logged_in_stats.get('total_exports', 0) or 1
    
    return {
        'guest': guest_stats,
        'logged_in': logged_in_stats,
        'comparison': {
            'sessions_ratio': round(logged_sessions / guest_sessions * 100, 2) if guest_sessions > 0 else 0,
            'generates_ratio': round(logged_generates / guest_generates * 100, 2) if guest_generates > 0 else 0,
            'export_ratio': round(logged_exports / guest_exports * 100, 2) if guest_exports > 0 else 0,
            'guest_to_user_conversion': 'N/A'  # 需要追踪登录事件
        }
    }


# 便捷函数
def track(event_name, properties=None, user_type='guest', user_id=None):
    """快速埋点函数"""
    analytics = Analytics(user_type, user_id)
    return analytics.track_event(event_name, properties)
