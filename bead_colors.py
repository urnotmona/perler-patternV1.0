# MARD拼豆官方221色色号数据库
# 基于比特拼豆(bitbead.pomodiary.com)官方数据
# 支持72/96/120/144/221色套装

import math

def rgb_to_hex(rgb):
    """RGB转十六进制"""
    return "#{:02x}{:02x}{:02x}".format(*rgb)

def hex_to_rgb(hex_color):
    """十六进制转RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_brightness(rgb):
    """计算亮度（用于深浅判断）"""
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b

def get_hue(rgb):
    """计算色相角"""
    r, g, b = [x/255.0 for x in rgb]
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    
    if max_c == min_c:
        return 0
    
    delta = max_c - min_c
    
    if max_c == r:
        h = ((g - b) / delta) % 6
    elif max_c == g:
        h = (b - r) / delta + 2
    else:
        h = (r - g) / delta + 4
    
    return int(h * 60) % 360

def generate_color_name(color_id, rgb, series):
    """根据色号和RGB生成中文名称"""
    r, g, b = rgb
    brightness = get_brightness(rgb)
    
    # 系列名称映射
    series_names = {
        'A': '黄橙',
        'B': '绿色',
        'C': '蓝青',
        'D': '紫蓝',
        'E': '粉红',
        'F': '红橙',
        'G': '棕肤',
        'H': '灰黑白',
        'M': '莫兰迪'
    }
    
    base_name = series_names.get(series, '彩色')
    num = int(color_id[1:])
    
    # 深浅判断
    if brightness > 220:
        depth = '浅淡'
    elif brightness > 180:
        depth = '浅'
    elif brightness > 140:
        depth = ''
    elif brightness > 100:
        depth = '中等'
    elif brightness > 60:
        depth = '深'
    else:
        depth = '暗深'
    
    # 特殊色号名称
    special_names = {
        'A1': '极浅鹅黄', 'A2': '奶白', 'A3': '嫩黄', 'A4': '浅金黄', 'A5': '明黄',
        'A6': '橙黄', 'A7': '浅橙', 'A8': '亮黄', 'A9': '暖橙', 'A10': '深橙',
        'A11': '浅杏', 'A12': '蜜桃橙', 'A13': '橙红', 'A14': '珊瑚橙', 'A15': '淡黄',
        'A16': '浅黄绿', 'A17': '芥末黄', 'A18': '浅棕黄', 'A19': '浅珊瑚', 'A20': '金黄',
        'A21': '浅土黄', 'A22': '黄绿', 'A23': '裸杏', 'A24': '浅柠檬', 'A25': '杏黄', 'A26': '土黄',
        
        'B1': '浅黄绿', 'B2': '荧光绿', 'B3': '浅翠绿', 'B4': '草绿', 'B5': '翠绿',
        'B6': '薄荷绿', 'B7': '青绿', 'B8': '深绿', 'B9': '墨绿', 'B10': '浅青绿',
        'B11': '橄榄绿', 'B12': '森林绿', 'B13': '浅草绿', 'B14': '黄绿色', 'B15': '深苔绿',
        'B16': '淡黄绿', 'B17': '橄榄', 'B18': '明黄绿', 'B19': '青碧', 'B20': '薄荷',
        'B21': '深青', 'B22': '墨青', 'B23': '暗绿', 'B24': '浅黄绿', 'B25': '松石绿',
        'B26': '土黄绿', 'B27': '浅灰绿', 'B28': '粉绿', 'B29': '黄绿', 'B30': '淡绿',
        'B31': '嫩绿', 'B32': '灰绿',
        
        'C1': '浅薄荷', 'C2': '浅青', 'C3': '天蓝', 'C4': '品蓝', 'C5': '钴蓝',
        'C6': '蓝', 'C7': '宝蓝', 'C8': '藏蓝', 'C9': '靛蓝', 'C10': '浅青蓝',
        'C11': '青绿蓝', 'C12': '深蓝灰', 'C13': '淡蓝', 'C14': '极浅蓝', 'C15': '青蓝',
        'C16': '海蓝', 'C17': '亮青', 'C18': '灰蓝', 'C19': '蓝绿', 'C20': '海天蓝',
        'C21': '粉蓝', 'C22': '蓝灰', 'C23': '雾蓝', 'C24': '天青', 'C25': '浅青',
        'C26': '湖蓝', 'C27': '薰衣草蓝', 'C28': '灰蓝紫', 'C29': '深紫蓝',
        
        'D1': '浅紫', 'D2': '薰衣草', 'D3': '蓝紫', 'D4': '深紫', 'D5': '品红',
        'D6': '紫粉', 'D7': '深紫红', 'D8': '淡紫', 'D9': '浅粉紫', 'D10': '暗紫',
        'D11': '灰紫', 'D12': '藕粉紫', 'D13': '洋红', 'D14': '深洋红', 'D15': '蓝紫深',
        'D16': '浅灰紫', 'D17': '淡蓝紫', 'D18': '灰粉紫', 'D19': '淡紫灰', 'D20': '紫红',
        'D21': '玫红', 'D22': '深蓝紫', 'D23': '浅雪青', 'D24': '中紫', 'D25': '蓝紫',
        'D26': '浅藕荷',
        
        'E1': '浅粉', 'E2': '浅玫瑰', 'E3': '粉红', 'E4': '玫粉', 'E5': '亮粉红',
        'E6': '深粉红', 'E7': '深玫', 'E8': '浅桃粉', 'E9': '亮紫粉', 'E10': '深粉',
        'E11': '淡粉', 'E12': '桃粉', 'E13': '深玫瑰', 'E14': '浅杏粉', 'E15': '浅粉白',
        'E16': '极浅粉', 'E17': '淡粉', 'E18': '淡玫瑰', 'E19': '浅玫', 'E20': '灰粉',
        'E21': '灰褐粉', 'E22': '藕粉灰', 'E23': '深灰紫', 'E24': '淡紫粉',
        
        'F1': '浅珊瑚', 'F2': '正红', 'F3': '亮红', 'F4': '深红', 'F5': '鲜红',
        'F6': '深棕红', 'F7': '酒红', 'F8': '暗红', 'F9': '粉棕红', 'F10': '深棕',
        'F11': '深褐红', 'F12': '珊瑚红', 'F13': '砖红', 'F14': '浅粉红', 'F15': '朱红',
        'F16': '浅杏', 'F17': '浅棕橙', 'F18': '浅橙棕', 'F19': '棕红', 'F20': '浅褐粉',
        'F21': '淡粉', 'F22': '浅玫瑰粉', 'F23': '珊瑚粉', 'F24': '浅玫瑰', 'F25': '红',
        
        'G1': '浅肤', 'G2': '浅杏', 'G3': '浅棕', 'G4': '浅黄棕', 'G5': '金棕',
        'G6': '深金', 'G7': '深棕', 'G8': '棕红', 'G9': '浅黄肤', 'G10': '浅金棕',
        'G11': '浅驼', 'G12': '浅杏黄', 'G13': '中棕', 'G14': '深驼', 'G15': '米白',
        'G16': '浅米', 'G17': '深棕灰', 'G18': '浅粉肤', 'G19': '深橙棕', 'G20': '砖棕',
        'G21': '浅驼棕',
        
        'H1': '白', 'H2': '纯白', 'H3': '浅灰', 'H4': '中灰', 'H5': '深灰',
        'H6': '炭灰', 'H7': '黑', 'H8': '浅粉灰', 'H9': '浅灰白', 'H10': '极浅灰',
        'H11': '灰', 'H12': '暖白', 'H13': '米白', 'H14': '浅青灰', 'H15': '青灰',
        'H16': '深棕黑', 'H17': '浅灰', 'H18': '象牙白', 'H19': '浅米', 'H20': '蓝灰',
        'H21': '浅黄白', 'H22': '灰紫', 'H23': '绿灰',
        
        'M1': '灰绿', 'M2': '浅绿灰', 'M3': '青灰', 'M4': '浅米灰', 'M5': '黄灰',
        'M6': '深黄灰', 'M7': '浅驼灰', 'M8': '浅玫瑰灰', 'M9': '深驼灰', 'M10': '粉灰',
        'M11': '紫灰', 'M12': '深玫瑰灰', 'M13': '浅橙灰', 'M14': '浅红灰', 'M15': '绿灰'
    }
    
    if color_id in special_names:
        return special_names[color_id]
    
    return f"{depth}{base_name}" if depth else base_name


# A系列 (26色) - 黄/橙系
A_SERIES = [
    {"id": "A1", "hex": "#FAF4C8"},
    {"id": "A2", "hex": "#FFFFD5"},
    {"id": "A3", "hex": "#FEFF8B"},
    {"id": "A4", "hex": "#FBED56"},
    {"id": "A5", "hex": "#F4D738"},
    {"id": "A6", "hex": "#FEAC4C"},
    {"id": "A7", "hex": "#FE8B4C"},
    {"id": "A8", "hex": "#FFDA45"},
    {"id": "A9", "hex": "#FF995B"},
    {"id": "A10", "hex": "#F77C31"},
    {"id": "A11", "hex": "#FFDD99"},
    {"id": "A12", "hex": "#FE9F72"},
    {"id": "A13", "hex": "#FFC365"},
    {"id": "A14", "hex": "#FD543D"},
    {"id": "A15", "hex": "#FFF365"},
    {"id": "A16", "hex": "#FFFF9F"},
    {"id": "A17", "hex": "#FFE36E"},
    {"id": "A18", "hex": "#FEBE7D"},
    {"id": "A19", "hex": "#FD7C72"},
    {"id": "A20", "hex": "#FFD568"},
    {"id": "A21", "hex": "#FFE395"},
    {"id": "A22", "hex": "#F4F57D"},
    {"id": "A23", "hex": "#E6C9B7"},
    {"id": "A24", "hex": "#F7F8A2"},
    {"id": "A25", "hex": "#FFD67D"},
    {"id": "A26", "hex": "#FFC830"},
]

# B系列 (32色) - 绿色系
B_SERIES = [
    {"id": "B1", "hex": "#E6EE31"},
    {"id": "B2", "hex": "#63F347"},
    {"id": "B3", "hex": "#9EF780"},
    {"id": "B4", "hex": "#5DE035"},
    {"id": "B5", "hex": "#35E352"},
    {"id": "B6", "hex": "#65E2A6"},
    {"id": "B7", "hex": "#3DAF80"},
    {"id": "B8", "hex": "#1C9C4F"},
    {"id": "B9", "hex": "#27523A"},
    {"id": "B10", "hex": "#95D3C2"},
    {"id": "B11", "hex": "#5D722A"},
    {"id": "B12", "hex": "#166F41"},
    {"id": "B13", "hex": "#CAEB7B"},
    {"id": "B14", "hex": "#ADE946"},
    {"id": "B15", "hex": "#2E5132"},
    {"id": "B16", "hex": "#C5ED9C"},
    {"id": "B17", "hex": "#9BB13A"},
    {"id": "B18", "hex": "#E6EE49"},
    {"id": "B19", "hex": "#24B88C"},
    {"id": "B20", "hex": "#C2F0CC"},
    {"id": "B21", "hex": "#156A6B"},
    {"id": "B22", "hex": "#0B3C43"},
    {"id": "B23", "hex": "#303A21"},
    {"id": "B24", "hex": "#EEFCA5"},
    {"id": "B25", "hex": "#4E846D"},
    {"id": "B26", "hex": "#8D7A35"},
    {"id": "B27", "hex": "#CCE1AF"},
    {"id": "B28", "hex": "#9EE5B9"},
    {"id": "B29", "hex": "#C5E254"},
    {"id": "B30", "hex": "#E2FCB1"},
    {"id": "B31", "hex": "#B0E792"},
    {"id": "B32", "hex": "#9CAB5A"},
]

# C系列 (29色) - 蓝色系
C_SERIES = [
    {"id": "C1", "hex": "#E8FFE7"},
    {"id": "C2", "hex": "#A9F9FC"},
    {"id": "C3", "hex": "#A0E2FB"},
    {"id": "C4", "hex": "#41CCFF"},
    {"id": "C5", "hex": "#01ACEB"},
    {"id": "C6", "hex": "#50AAF0"},
    {"id": "C7", "hex": "#3677D2"},
    {"id": "C8", "hex": "#0F54C0"},
    {"id": "C9", "hex": "#324BCA"},
    {"id": "C10", "hex": "#3EBCE2"},
    {"id": "C11", "hex": "#28DDDE"},
    {"id": "C12", "hex": "#1C334D"},
    {"id": "C13", "hex": "#CDE8FF"},
    {"id": "C14", "hex": "#D5FDFF"},
    {"id": "C15", "hex": "#22C4C6"},
    {"id": "C16", "hex": "#1557A8"},
    {"id": "C17", "hex": "#04D1F6"},
    {"id": "C18", "hex": "#1D3344"},
    {"id": "C19", "hex": "#1887A2"},
    {"id": "C20", "hex": "#176DAF"},
    {"id": "C21", "hex": "#BEDDFF"},
    {"id": "C22", "hex": "#67B4BE"},
    {"id": "C23", "hex": "#C8E2FF"},
    {"id": "C24", "hex": "#7CC4FF"},
    {"id": "C25", "hex": "#A9E5E5"},
    {"id": "C26", "hex": "#3CAED8"},
    {"id": "C27", "hex": "#D3DFFA"},
    {"id": "C28", "hex": "#BBCFED"},
    {"id": "C29", "hex": "#34488E"},
]

# D系列 (26色) - 紫色系
D_SERIES = [
    {"id": "D1", "hex": "#AEB4F2"},
    {"id": "D2", "hex": "#858EDD"},
    {"id": "D3", "hex": "#2F54AF"},
    {"id": "D4", "hex": "#182A84"},
    {"id": "D5", "hex": "#B843C5"},
    {"id": "D6", "hex": "#AC7BDE"},
    {"id": "D7", "hex": "#8854B3"},
    {"id": "D8", "hex": "#E2D3FF"},
    {"id": "D9", "hex": "#D5B9F8"},
    {"id": "D10", "hex": "#361851"},
    {"id": "D11", "hex": "#B9BAE1"},
    {"id": "D12", "hex": "#DE9AD4"},
    {"id": "D13", "hex": "#B90095"},
    {"id": "D14", "hex": "#8B279B"},
    {"id": "D15", "hex": "#2F1F90"},
    {"id": "D16", "hex": "#E3E1EE"},
    {"id": "D17", "hex": "#C4D4F6"},
    {"id": "D18", "hex": "#A45EC7"},
    {"id": "D19", "hex": "#D8C3D7"},
    {"id": "D20", "hex": "#9C32B2"},
    {"id": "D21", "hex": "#9A009B"},
    {"id": "D22", "hex": "#333A95"},
    {"id": "D23", "hex": "#EBDAFC"},
    {"id": "D24", "hex": "#7786E5"},
    {"id": "D25", "hex": "#494FC7"},
    {"id": "D26", "hex": "#DFC2F8"},
]

# E系列 (24色) - 粉色系
E_SERIES = [
    {"id": "E1", "hex": "#FDD3CC"},
    {"id": "E2", "hex": "#FEC0DF"},
    {"id": "E3", "hex": "#FFB7E7"},
    {"id": "E4", "hex": "#E8649E"},
    {"id": "E5", "hex": "#F551A2"},
    {"id": "E6", "hex": "#F13D74"},
    {"id": "E7", "hex": "#C63478"},
    {"id": "E8", "hex": "#FFDBE9"},
    {"id": "E9", "hex": "#E970CC"},
    {"id": "E10", "hex": "#D33793"},
    {"id": "E11", "hex": "#FCDDD2"},
    {"id": "E12", "hex": "#F78FC3"},
    {"id": "E13", "hex": "#B5006D"},
    {"id": "E14", "hex": "#FFD1BA"},
    {"id": "E15", "hex": "#F8C7C9"},
    {"id": "E16", "hex": "#FFF3EB"},
    {"id": "E17", "hex": "#FFE2EA"},
    {"id": "E18", "hex": "#FFC7DB"},
    {"id": "E19", "hex": "#FEBAD5"},
    {"id": "E20", "hex": "#D8C7D1"},
    {"id": "E21", "hex": "#BD9DA1"},
    {"id": "E22", "hex": "#B785A1"},
    {"id": "E23", "hex": "#937A8D"},
    {"id": "E24", "hex": "#E1BCE8"},
]

# F系列 (25色) - 红色系
F_SERIES = [
    {"id": "F1", "hex": "#FD957B"},
    {"id": "F2", "hex": "#FC3D46"},
    {"id": "F3", "hex": "#F74941"},
    {"id": "F4", "hex": "#FC283C"},
    {"id": "F5", "hex": "#E7002F"},
    {"id": "F6", "hex": "#943630"},
    {"id": "F7", "hex": "#971937"},
    {"id": "F8", "hex": "#BC0028"},
    {"id": "F9", "hex": "#E2677A"},
    {"id": "F10", "hex": "#8A4526"},
    {"id": "F11", "hex": "#5A2121"},
    {"id": "F12", "hex": "#FD4E6A"},
    {"id": "F13", "hex": "#F35744"},
    {"id": "F14", "hex": "#FFA9AD"},
    {"id": "F15", "hex": "#D30022"},
    {"id": "F16", "hex": "#FEC2A6"},
    {"id": "F17", "hex": "#E69C79"},
    {"id": "F18", "hex": "#D37C46"},
    {"id": "F19", "hex": "#C1444A"},
    {"id": "F20", "hex": "#CD9391"},
    {"id": "F21", "hex": "#F7B4C6"},
    {"id": "F22", "hex": "#FDC0D0"},
    {"id": "F23", "hex": "#F67E66"},
    {"id": "F24", "hex": "#E698AA"},
    {"id": "F25", "hex": "#E54B4F"},
]

# G系列 (21色) - 棕/肤色系
G_SERIES = [
    {"id": "G1", "hex": "#FFE2CE"},
    {"id": "G2", "hex": "#FFC4AA"},
    {"id": "G3", "hex": "#F4C3A5"},
    {"id": "G4", "hex": "#E1B383"},
    {"id": "G5", "hex": "#EDB045"},
    {"id": "G6", "hex": "#E99C17"},
    {"id": "G7", "hex": "#9D5B3E"},
    {"id": "G8", "hex": "#753832"},
    {"id": "G9", "hex": "#E6B483"},
    {"id": "G10", "hex": "#D98C39"},
    {"id": "G11", "hex": "#E0C593"},
    {"id": "G12", "hex": "#FFC890"},
    {"id": "G13", "hex": "#B7714A"},
    {"id": "G14", "hex": "#8D614C"},
    {"id": "G15", "hex": "#FCF9E0"},
    {"id": "G16", "hex": "#F2D9BA"},
    {"id": "G17", "hex": "#78524B"},
    {"id": "G18", "hex": "#FFE4CC"},
    {"id": "G19", "hex": "#E07935"},
    {"id": "G20", "hex": "#A94023"},
    {"id": "G21", "hex": "#B88558"},
]

# H系列 (23色) - 黑/白/灰色系
H_SERIES = [
    {"id": "H1", "hex": "#FDFBFF"},
    {"id": "H2", "hex": "#FEFFFF"},
    {"id": "H3", "hex": "#B6B1BA"},
    {"id": "H4", "hex": "#89858C"},
    {"id": "H5", "hex": "#48464E"},
    {"id": "H6", "hex": "#2F2B2F"},
    {"id": "H7", "hex": "#000000"},
    {"id": "H8", "hex": "#E7D6DB"},
    {"id": "H9", "hex": "#EDEDED"},
    {"id": "H10", "hex": "#EEE9EA"},
    {"id": "H11", "hex": "#CECDD5"},
    {"id": "H12", "hex": "#FFF5ED"},
    {"id": "H13", "hex": "#F5ECD2"},
    {"id": "H14", "hex": "#CFD7D3"},
    {"id": "H15", "hex": "#98A6A8"},
    {"id": "H16", "hex": "#1D1414"},
    {"id": "H17", "hex": "#F1EDED"},
    {"id": "H18", "hex": "#FFFDF0"},
    {"id": "H19", "hex": "#F6EFE2"},
    {"id": "H20", "hex": "#949FA3"},
    {"id": "H21", "hex": "#FFFBE1"},
    {"id": "H22", "hex": "#CACAD4"},
    {"id": "H23", "hex": "#9A9D94"},
]

# M系列 (15色) - 莫兰迪/高级灰系
M_SERIES = [
    {"id": "M1", "hex": "#BCC6B8"},
    {"id": "M2", "hex": "#8AA386"},
    {"id": "M3", "hex": "#697D80"},
    {"id": "M4", "hex": "#E3D2BC"},
    {"id": "M5", "hex": "#D0CCAA"},
    {"id": "M6", "hex": "#B0A782"},
    {"id": "M7", "hex": "#B4A497"},
    {"id": "M8", "hex": "#B38281"},
    {"id": "M9", "hex": "#A58767"},
    {"id": "M10", "hex": "#C5B2BC"},
    {"id": "M11", "hex": "#9F7594"},
    {"id": "M12", "hex": "#644749"},
    {"id": "M13", "hex": "#D19066"},
    {"id": "M14", "hex": "#C77362"},
    {"id": "M15", "hex": "#757D78"},
]

# 构建完整221色数据库
ALL_SERIES = [
    ('A', A_SERIES),
    ('B', B_SERIES),
    ('C', C_SERIES),
    ('D', D_SERIES),
    ('E', E_SERIES),
    ('F', F_SERIES),
    ('G', G_SERIES),
    ('H', H_SERIES),
    ('M', M_SERIES),
]

MARD_COLORS_221 = []
COLOR_INDEX = {}

for series_letter, series_data in ALL_SERIES:
    for color in series_data:
        color_id = color["id"]
        hex_val = color["hex"]
        rgb = hex_to_rgb(hex_val)
        name = generate_color_name(color_id, rgb, series_letter)
        
        color_info = {
            "id": color_id,
            "name": name,
            "hex": hex_val.upper(),
            "rgb": rgb,
            "series": series_letter
        }
        MARD_COLORS_221.append(color_info)
        COLOR_INDEX[color_id] = color_info

# 色系套装定义
COLOR_SETS = {
    "72": {
        "name": "72色入门基础",
        "description": "入门级套装，包含各色系核心颜色",
        "colors": [
            # 黄橙 (8色)
            "A1","A2","A3","A4","A5","A6","A7","A8",
            # 绿色 (11色)
            "B1","B2","B3","B4","B5","B6","B7","B8","B9","B10","B11",
            # 蓝色 (10色)
            "C1","C2","C3","C4","C5","C6","C7","C8","C9","C10",
            # 紫色 (8色)
            "D1","D2","D3","D4","D5","D6","D7","D8",
            # 粉色 (8色)
            "E1","E2","E3","E4","E5","E6","E7","E8",
            # 红色 (8色)
            "F1","F2","F3","F4","F5","F6","F7","F8",
            # 棕色/肤色 (7色)
            "G1","G2","G3","G4","G5","G6","G7",
            # 黑白灰 (7色)
            "H1","H2","H3","H4","H5","H6","H7",
            # 莫兰迪 (5色)
            "M1","M2","M3","M4","M5"
        ]
    },
    "96": {
        "name": "96色进阶创作",
        "description": "进阶套装，在入门基础上增加更多色彩选择",
        "colors": [
            # 黄橙 (11色)
            "A1","A2","A3","A4","A5","A6","A7","A8","A9","A10","A11",
            # 绿色 (14色)
            "B1","B2","B3","B4","B5","B6","B7","B8","B9","B10","B11","B12","B13","B14",
            # 蓝色 (13色)
            "C1","C2","C3","C4","C5","C6","C7","C8","C9","C10","C11","C12","C13",
            # 紫色 (11色)
            "D1","D2","D3","D4","D5","D6","D7","D8","D9","D10","D11",
            # 粉色 (10色)
            "E1","E2","E3","E4","E5","E6","E7","E8","E9","E10",
            # 红色 (11色)
            "F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11",
            # 棕色/肤色 (9色)
            "G1","G2","G3","G4","G5","G6","G7","G8","G9",
            # 黑白灰 (10色)
            "H1","H2","H3","H4","H5","H6","H7","H8","H9","H10",
            # 莫兰迪 (7色)
            "M1","M2","M3","M4","M5","M6","M7"
        ]
    },
    "120": {
        "name": "120色专业创作",
        "description": "专业套装，适合复杂图案创作",
        "colors": [
            # 黄橙 (14色)
            "A1","A2","A3","A4","A5","A6","A7","A8","A9","A10","A11","A12","A13","A14",
            # 绿色 (18色)
            "B1","B2","B3","B4","B5","B6","B7","B8","B9","B10","B11","B12","B13","B14","B15","B16","B17","B18",
            # 蓝色 (16色)
            "C1","C2","C3","C4","C5","C6","C7","C8","C9","C10","C11","C12","C13","C14","C15","C16",
            # 紫色 (14色)
            "D1","D2","D3","D4","D5","D6","D7","D8","D9","D10","D11","D12","D13","D14",
            # 粉色 (13色)
            "E1","E2","E3","E4","E5","E6","E7","E8","E9","E10","E11","E12","E13",
            # 红色 (14色)
            "F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12","F13","F14",
            # 棕色/肤色 (11色)
            "G1","G2","G3","G4","G5","G6","G7","G8","G9","G10","G11",
            # 黑白灰 (12色)
            "H1","H2","H3","H4","H5","H6","H7","H8","H9","H10","H11","H12",
            # 莫兰迪 (8色)
            "M1","M2","M3","M4","M5","M6","M7","M8"
        ]
    },
    "144": {
        "name": "144色高级创作",
        "description": "高级套装，覆盖更多高级灰和莫兰迪色系",
        "colors": [
            # 黄橙 (17色)
            "A1","A2","A3","A4","A5","A6","A7","A8","A9","A10","A11","A12","A13","A14","A15","A16","A17",
            # 绿色 (20色)
            "B1","B2","B3","B4","B5","B6","B7","B8","B9","B10","B11","B12","B13","B14","B15","B16","B17","B18","B19","B20",
            # 蓝色 (19色)
            "C1","C2","C3","C4","C5","C6","C7","C8","C9","C10","C11","C12","C13","C14","C15","C16","C17","C18","C19",
            # 紫色 (17色)
            "D1","D2","D3","D4","D5","D6","D7","D8","D9","D10","D11","D12","D13","D14","D15","D16","D17",
            # 粉色 (16色)
            "E1","E2","E3","E4","E5","E6","E7","E8","E9","E10","E11","E12","E13","E14","E15","E16",
            # 红色 (16色)
            "F1","F2","F3","F4","F5","F6","F7","F8","F9","F10","F11","F12","F13","F14","F15","F16",
            # 棕色/肤色 (14色)
            "G1","G2","G3","G4","G5","G6","G7","G8","G9","G10","G11","G12","G13","G14",
            # 黑白灰 (15色)
            "H1","H2","H3","H4","H5","H6","H7","H8","H9","H10","H11","H12","H13","H14","H15",
            # 莫兰迪 (10色)
            "M1","M2","M3","M4","M5","M6","M7","M8","M9","M10"
        ]
    },
    "221": {
        "name": "221色全色板",
        "description": "MARD官方全部221色",
        "colors": None  # None表示全部221色
    }
}


def get_all_colors():
    """获取全部221色"""
    return MARD_COLORS_221


def get_colors_by_set(set_name):
    """
    获取指定套装的颜色列表
    set_name: "72", "96", "120", "144", "221"
    """
    if set_name not in COLOR_SETS:
        return MARD_COLORS_221
    
    set_info = COLOR_SETS[set_name]
    
    if set_info["colors"] is None:
        # 全色板
        return MARD_COLORS_221
    
    colors = []
    for color_id in set_info["colors"]:
        if color_id in COLOR_INDEX:
            colors.append(COLOR_INDEX[color_id])
    
    return colors


def get_color_by_id(color_id):
    """根据色号ID获取颜色信息"""
    return COLOR_INDEX.get(color_id)


def get_available_sets():
    """获取所有可用套装信息"""
    return {
        set_id: {
            "id": set_id,
            "name": info["name"],
            "description": info["description"],
            "color_count": len(set(info["colors"])) if info["colors"] else 221
        }
        for set_id, info in COLOR_SETS.items()
    }


def _color_saturation(rgb):
    """计算RGB颜色的饱和度 (0~1)"""
    r, g, b = rgb
    mx = max(r, g, b)
    mn = min(r, g, b)
    if mx == 0:
        return 0
    return (mx - mn) / mx


def _is_grayish_color(color_id, rgb):
    """判断一个拼豆颜色是否属于灰色系/低饱和度色"""
    # 白色系(背景色)和黑色不惩罚
    white_ids = ('H1', 'H2', 'H18', 'H19', 'H21', 'H9', 'H10')
    black_ids = ('H7', 'H16')
    if color_id in white_ids or color_id in black_ids:
        return False
    # M系列全是灰调混合色
    if color_id.startswith('M'):
        return True
    # H系列（排除白/黑后）都是灰
    if color_id.startswith('H'):
        return True
    # 饱和度低于0.15的也算灰色系
    if _color_saturation(rgb) < 0.15:
        return True
    return False


def find_closest_color(rgb, color_set="221", penalize_gray=True):
    """
    使用欧几里得距离在RGB色彩空间中查找最接近的颜色
    rgb: (r, g, b) 元组
    color_set: 限定匹配范围的套装 ("72", "96", "120", "144", "221")
    penalize_gray: 对灰色系颜色加惩罚，优先匹配纯净色
    返回: (色号ID, 颜色名称, RGB元组, HEX值, 距离)
    """
    available_colors = get_colors_by_set(color_set)
    
    r, g, b = rgb
    pixel_sat = _color_saturation(rgb)
    
    min_distance = float('inf')
    closest_color = None
    
    for color in available_colors:
        cr, cg, cb = color["rgb"]
        # 加权欧几里得距离（人眼对绿色更敏感）
        distance = math.sqrt(
            2 * (r - cr) ** 2 + 
            4 * (g - cg) ** 2 + 
            3 * (b - cb) ** 2
        )
        
        # 灰色惩罚：输入像素有一定饱和度时，避免匹配到灰色系
        if penalize_gray and pixel_sat > 0.15:
            if _is_grayish_color(color["id"], color["rgb"]):
                gray_penalty = 15 + pixel_sat * 60
                distance += gray_penalty
        
        if distance < min_distance:
            min_distance = distance
            closest_color = color
    
    return (
        closest_color["id"],
        closest_color["name"],
        closest_color["rgb"],
        closest_color["hex"],
        min_distance
    )


# 保持向后兼容的别名
BEAD_COLORS = MARD_COLORS_221
