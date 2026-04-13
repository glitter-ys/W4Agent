#!/usr/bin/env python3
"""
W4Agent 系统总体架构图生成脚本
使用 matplotlib 绘制高清架构图
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ── 中文字体配置 ──
import matplotlib.font_manager as fm

# 清理缓存, 强制重建
fm._load_fontmanager(try_read_cache=False)

# macOS 可用中文字体优先
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Heiti TC', 'PingFang HK', 'PingFang SC', 'STHeiti', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# ── 颜色方案 ──
C = {
    'bg':           '#FAFCFF',
    # 四大层背景
    'layer_present': '#E3F2FD',
    'layer_service': '#E8F5E9',
    'layer_engine':  '#FFF3E0',
    'layer_data':    '#F3E5F5',
    # 模块色
    'blue':     '#1565C0',
    'blue_l':   '#BBDEFB',
    'green':    '#2E7D32',
    'green_l':  '#C8E6C9',
    'orange':   '#E65100',
    'orange_l': '#FFE0B2',
    'purple':   '#6A1B9A',
    'purple_l': '#E1BEE7',
    'red':      '#C62828',
    'red_l':    '#FFCDD2',
    'teal':     '#00695C',
    'teal_l':   '#B2DFDB',
    'indigo':   '#283593',
    'indigo_l': '#C5CAE9',
    'amber':    '#FF8F00',
    'amber_l':  '#FFECB3',
    'grey':     '#455A64',
    'grey_l':   '#CFD8DC',
    'white':    '#FFFFFF',
    'text':     '#212121',
    'text_l':   '#616161',
    'arrow':    '#78909C',
    'arrow_dark': '#37474F',
}

fig, ax = plt.subplots(1, 1, figsize=(22, 28), dpi=180)
fig.patch.set_facecolor(C['bg'])
ax.set_xlim(0, 22)
ax.set_ylim(0, 28)
ax.set_aspect('equal')
ax.axis('off')

# ═══════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════

def draw_rounded_box(x, y, w, h, fc, ec='#BDBDBD', lw=1.2, alpha=1.0, zorder=1, radius=0.3):
    """绘制圆角矩形"""
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle=f"round,pad=0,rounding_size={radius}",
                         facecolor=fc, edgecolor=ec, linewidth=lw,
                         alpha=alpha, zorder=zorder,
                         transform=ax.transData)
    ax.add_patch(box)
    return box

def draw_module(x, y, w, h, title, items, title_color, bg_color, border_color, icon=None, zorder=5):
    """绘制一个模块卡片"""
    draw_rounded_box(x, y, w, h, bg_color, border_color, lw=1.5, zorder=zorder, radius=0.2)
    # 标题栏
    draw_rounded_box(x + 0.05, y + h - 0.55, w - 0.1, 0.5, title_color, title_color, lw=0, zorder=zorder+1, radius=0.15)
    label = f"{icon} {title}" if icon else title
    ax.text(x + w/2, y + h - 0.3, label, ha='center', va='center',
            fontsize=12.6, fontweight='bold', color='white', zorder=zorder+2)
    # 内容项
    for i, item in enumerate(items):
        ax.text(x + 0.25, y + h - 0.85 - i*0.34, f"• {item}",
                ha='left', va='center', fontsize=9.8, color=C['text_l'], zorder=zorder+2)

def draw_small_box(x, y, w, h, text, fc, tc='white', fs=11.2, zorder=5, ec=None, fw='bold'):
    """绘制小标签框"""
    draw_rounded_box(x, y, w, h, fc, ec or fc, lw=1 if ec else 0, zorder=zorder, radius=0.12)
    ax.text(x + w/2, y + h/2, text, ha='center', va='center',
            fontsize=fs, fontweight=fw, color=tc, zorder=zorder+1)

def draw_arrow(x1, y1, x2, y2, color=C['arrow'], lw=1.5, style='->', zorder=3, ls='-'):
    """绘制箭头"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color,
                                lw=lw, linestyle=ls,
                                connectionstyle='arc3,rad=0'),
                zorder=zorder)

def draw_arrow_curved(x1, y1, x2, y2, color=C['arrow'], lw=1.5, rad=0.2, zorder=3):
    """绘制弯曲箭头"""
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color,
                                lw=lw,
                                connectionstyle=f'arc3,rad={rad}'),
                zorder=zorder)

def draw_layer_label(y_center, text, color):
    """在左侧绘制层标签"""
    draw_rounded_box(0.15, y_center - 0.35, 1.4, 0.7, color, color, lw=0, zorder=10, radius=0.15)
    ax.text(0.85, y_center, text, ha='center', va='center',
            fontsize=14, fontweight='bold', color='white', zorder=11, rotation=0)


# ═══════════════════════════════════════════
#  标题
# ═══════════════════════════════════════════
ax.text(11, 27.4, 'W4Agent 系统总体架构图', ha='center', va='center',
        fontsize=30.8, fontweight='bold', color=C['blue'])
ax.text(11, 26.9, '基于智能体技术的Web无障碍智能检测系统', ha='center', va='center',
        fontsize=16.8, color=C['text_l'])


# ═══════════════════════════════════════════
#  Layer 1: 表现层 (y: 24.0 ~ 26.2)
# ═══════════════════════════════════════════
L1_Y = 24.0
L1_H = 2.2
draw_rounded_box(1.8, L1_Y, 19.0, L1_H, C['layer_present'], C['blue'], lw=2, alpha=0.5, zorder=0, radius=0.3)
draw_layer_label(L1_Y + L1_H/2, '表现层', C['blue'])

# 前端技术标签
techs = [('React 18', C['blue']), ('TypeScript', C['indigo']), ('Ant Design', C['teal']),
         ('Zustand', C['purple']), ('Vite', C['amber']), ('WebSocket', C['green'])]
for i, (t, c) in enumerate(techs):
    draw_small_box(2.2 + i * 2.1, L1_Y + L1_H - 0.55, 1.9, 0.4, t, c, fs=10.5, zorder=5)

# 六个页面
pages = [
    ('Dashboard',  '全局总览\n统计/趋势'),
    ('项目管理',    '项目CRUD\nURL配置'),
    ('任务创建',    '配置参数\nWCAG级别'),
    ('任务详情',    '实时监控\n4Tab视图'),
    ('检测报告',    '评分/统计\n导出报告'),
    ('系统设置',    'LLM配置\n检测参数'),
]
page_w = 2.7
page_h = 1.2
page_start_x = 2.2
for i, (name, desc) in enumerate(pages):
    px = page_start_x + i * 3.05
    py = L1_Y + 0.15
    draw_rounded_box(px, py, page_w, page_h, C['white'], C['blue'], lw=1, zorder=5, radius=0.15)
    ax.text(px + page_w/2, py + page_h - 0.25, name, ha='center', va='center',
            fontsize=11.9, fontweight='bold', color=C['blue'], zorder=6)
    ax.text(px + page_w/2, py + page_h/2 - 0.2, desc, ha='center', va='center',
            fontsize=9.1, color=C['text_l'], zorder=6, linespacing=1.4)


# ═══════════════════════════════════════════
#  通信层标签 (y: 23.2 ~ 24.0)
# ═══════════════════════════════════════════
COMM_Y = 23.2
draw_rounded_box(1.8, COMM_Y, 19.0, 0.7, '#ECEFF1', '#90A4AE', lw=1, alpha=0.6, zorder=0, radius=0.2)
ax.text(5.5, COMM_Y + 0.35, 'REST API (6组路由)', ha='center', va='center',
        fontsize=12.6, fontweight='bold', color=C['grey'], zorder=5)
ax.text(11, COMM_Y + 0.35, '|', ha='center', va='center', fontsize=16.8, color='#B0BEC5', zorder=5)
ax.text(16.5, COMM_Y + 0.35, 'WebSocket (7种实时消息)', ha='center', va='center',
        fontsize=12.6, fontweight='bold', color=C['grey'], zorder=5)

# 双向箭头
draw_arrow(7, L1_Y, 7, COMM_Y + 0.7, C['blue'], lw=2, style='<->')
draw_arrow(15, L1_Y, 15, COMM_Y + 0.7, C['green'], lw=2, style='<->')


# ═══════════════════════════════════════════
#  Layer 2: 服务层 (y: 20.0 ~ 23.0)
# ═══════════════════════════════════════════
L2_Y = 20.0
L2_H = 3.0
draw_rounded_box(1.8, L2_Y, 19.0, L2_H, C['layer_service'], C['green'], lw=2, alpha=0.4, zorder=0, radius=0.3)
draw_layer_label(L2_Y + L2_H/2, '服务层', C['green'])

# 路由层
ax.text(5.0, L2_Y + L2_H - 0.3, 'FastAPI 路由层 (api/v1/)', ha='center', va='center',
        fontsize=12.6, fontweight='bold', color=C['green'], zorder=5)
routes = ['projects', 'tasks', 'issues', 'reports', 'annotations', 'ws/monitor']
for i, r in enumerate(routes):
    draw_small_box(2.2 + i * 2.5, L2_Y + L2_H - 0.75, 2.3, 0.35, r, C['green_l'], tc=C['green'], fs=9.8, zorder=5, ec=C['green'], fw='normal')

# 服务层
ax.text(5.0, L2_Y + L2_H - 1.3, '业务逻辑层 (services/)', ha='center', va='center',
        fontsize=12.6, fontweight='bold', color=C['green'], zorder=5)
services = [
    ('TaskService', '任务生命周期'),
    ('ReportService', '报告生成导出'),
    ('NotificationService', 'WebSocket广播'),
    ('JiraService', 'Jira集成'),
]
for i, (name, desc) in enumerate(services):
    sx = 2.2 + i * 3.8
    draw_rounded_box(sx, L2_Y + L2_H - 2.0, 3.5, 0.55, C['white'], C['green'], lw=1, zorder=5, radius=0.12)
    ax.text(sx + 1.75, L2_Y + L2_H - 1.55, name, ha='center', va='center',
            fontsize=10.5, fontweight='bold', color=C['green'], zorder=6)
    ax.text(sx + 1.75, L2_Y + L2_H - 1.82, desc, ha='center', va='center',
            fontsize=9.1, color=C['text_l'], zorder=6)

# 数据模型层
ax.text(5.0, L2_Y + 0.55, '数据模型层 (models/ + schemas/)', ha='center', va='center',
        fontsize=12.6, fontweight='bold', color=C['green'], zorder=5)
models = ['Project', 'Task', 'Page', 'Issue', 'Report', 'Annotation', 'AgentMemory']
for i, m in enumerate(models):
    draw_small_box(2.2 + i * 2.3, L2_Y + 0.1, 2.1, 0.3, m, C['green_l'], tc=C['green'], fs=9.1, zorder=5, ec=C['green'], fw='normal')

# 下方通信标签
draw_arrow(11, L2_Y, 11, L2_Y - 0.25, C['arrow_dark'], lw=2.5, style='->')


# ═══════════════════════════════════════════
#  Layer 3: 引擎层 (y: 5.5 ~ 19.5)
# ═══════════════════════════════════════════
L3_Y = 5.5
L3_H = 14.2
draw_rounded_box(1.8, L3_Y, 19.0, L3_H, C['layer_engine'], C['orange'], lw=2, alpha=0.35, zorder=0, radius=0.3)
draw_layer_label(L3_Y + L3_H/2, '引擎层', C['orange'])

# ─── 3A: 多智能体编排引擎 (y: 15.0 ~ 19.5) ───
SEC_A_Y = 15.2
SEC_A_H = 4.3
draw_rounded_box(2.2, SEC_A_Y, 18.4, SEC_A_H, '#FFF8E1', C['orange'], lw=1.5, alpha=0.7, zorder=1, radius=0.25)
ax.text(11.4, SEC_A_Y + SEC_A_H - 0.3, '多智能体协同编排引擎 (LangGraph State Machine)',
        ha='center', va='center', fontsize=15.4, fontweight='bold', color=C['orange'], zorder=5)

# 状态机流程图
# START 节点
draw_small_box(2.8, SEC_A_Y + 2.3, 1.4, 0.6, 'START', C['grey'], fs=12.6, zorder=6)

# Plan 节点
draw_rounded_box(5.0, SEC_A_Y + 2.0, 2.8, 1.2, C['blue'], C['blue'], lw=2, zorder=6, radius=0.2)
ax.text(6.4, SEC_A_Y + 2.85, 'Plan', ha='center', va='center',
        fontsize=15.4, fontweight='bold', color='white', zorder=7)
ax.text(6.4, SEC_A_Y + 2.4, 'Master Agent', ha='center', va='center',
        fontsize=10.5, color='#BBDEFB', zorder=7)

# Explore 节点
draw_rounded_box(8.8, SEC_A_Y + 3.0, 2.8, 1.0, C['green'], C['green'], lw=2, zorder=6, radius=0.2)
ax.text(10.2, SEC_A_Y + 3.7, 'Explore', ha='center', va='center',
        fontsize=14, fontweight='bold', color='white', zorder=7)
ax.text(10.2, SEC_A_Y + 3.3, 'Crawler Agent', ha='center', va='center',
        fontsize=9.8, color='#C8E6C9', zorder=7)

# Test 节点
draw_rounded_box(8.8, SEC_A_Y + 1.5, 2.8, 1.0, C['red'], C['red'], lw=2, zorder=6, radius=0.2)
ax.text(10.2, SEC_A_Y + 2.2, 'Test', ha='center', va='center',
        fontsize=14, fontweight='bold', color='white', zorder=7)
ax.text(10.2, SEC_A_Y + 1.8, 'Detector Agent', ha='center', va='center',
        fontsize=9.8, color='#FFCDD2', zorder=7)

# Report 节点
draw_rounded_box(12.6, SEC_A_Y + 2.0, 2.8, 1.2, C['purple'], C['purple'], lw=2, zorder=6, radius=0.2)
ax.text(14.0, SEC_A_Y + 2.85, 'Report', ha='center', va='center',
        fontsize=14, fontweight='bold', color='white', zorder=7)
ax.text(14.0, SEC_A_Y + 2.4, 'Reporter Agent', ha='center', va='center',
        fontsize=9.8, color='#E1BEE7', zorder=7)

# END 节点
draw_small_box(16.2, SEC_A_Y + 2.3, 1.4, 0.6, 'END', C['grey'], fs=12.6, zorder=6)

# 箭头: START -> Plan
draw_arrow(4.2, SEC_A_Y + 2.6, 5.0, SEC_A_Y + 2.6, C['arrow_dark'], lw=2)
# Plan -> Explore
draw_arrow(7.8, SEC_A_Y + 3.1, 8.8, SEC_A_Y + 3.5, C['green'], lw=2)
# Plan -> Test
draw_arrow(7.8, SEC_A_Y + 2.3, 8.8, SEC_A_Y + 2.0, C['red'], lw=2)
# Plan -> Report
draw_arrow(7.8, SEC_A_Y + 2.6, 12.6, SEC_A_Y + 2.6, C['purple'], lw=2)
# Explore -> Plan (curved back)
draw_arrow_curved(8.8, SEC_A_Y + 3.3, 7.0, SEC_A_Y + 3.2, C['green'], lw=1.5, rad=-0.4)
# Test -> Plan (curved back)
draw_arrow_curved(8.8, SEC_A_Y + 1.8, 7.0, SEC_A_Y + 2.1, C['red'], lw=1.5, rad=0.4)
# Report -> END
draw_arrow(15.4, SEC_A_Y + 2.6, 16.2, SEC_A_Y + 2.6, C['arrow_dark'], lw=2)

# 条件路由标签
ax.text(8.3, SEC_A_Y + 3.55, 'EXPLORE', ha='center', va='center',
        fontsize=9.1, fontweight='bold', color=C['green'], zorder=7,
        bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor=C['green'], alpha=0.9))
ax.text(8.3, SEC_A_Y + 1.85, 'TEST', ha='center', va='center',
        fontsize=9.1, fontweight='bold', color=C['red'], zorder=7,
        bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor=C['red'], alpha=0.9))
ax.text(10.2, SEC_A_Y + 2.75, 'REPORT', ha='center', va='center',
        fontsize=9.1, fontweight='bold', color=C['purple'], zorder=7,
        bbox=dict(boxstyle='round,pad=0.15', facecolor='white', edgecolor=C['purple'], alpha=0.9))

# 记忆系统
draw_rounded_box(16.8, SEC_A_Y + 0.8, 3.5, 3.0, '#FFF9C4', C['amber'], lw=1.5, zorder=5, radius=0.2)
ax.text(18.55, SEC_A_Y + 3.5, '记忆系统', ha='center', va='center',
        fontsize=12.6, fontweight='bold', color=C['amber'], zorder=6)
# 短期
draw_rounded_box(17.0, SEC_A_Y + 2.2, 3.1, 0.7, C['amber_l'], C['amber'], lw=1, zorder=6, radius=0.12)
ax.text(18.55, SEC_A_Y + 2.7, '短期记忆', ha='center', va='center',
        fontsize=11.2, fontweight='bold', color=C['amber'], zorder=7)
ax.text(18.55, SEC_A_Y + 2.4, 'deque(100) 会话内上下文', ha='center', va='center',
        fontsize=8.4, color=C['text_l'], zorder=7)
# 长期
draw_rounded_box(17.0, SEC_A_Y + 1.0, 3.1, 1.0, C['amber_l'], C['amber'], lw=1, zorder=6, radius=0.12)
ax.text(18.55, SEC_A_Y + 1.7, '长期记忆', ha='center', va='center',
        fontsize=11.2, fontweight='bold', color=C['amber'], zorder=7)
mem_types = ['情景记忆', '语义记忆', '程序性记忆']
for i, mt in enumerate(mem_types):
    ax.text(17.3 + i * 1.05, SEC_A_Y + 1.2, mt, ha='center', va='center',
            fontsize=7.7, color=C['amber'], zorder=7,
            bbox=dict(boxstyle='round,pad=0.1', facecolor='white', edgecolor=C['amber'], alpha=0.8))

# 连接线: Agent -> 记忆
draw_arrow(15.4, SEC_A_Y + 3.0, 16.8, SEC_A_Y + 2.8, C['amber'], lw=1, style='<->', ls='--')


# PipelineState 标签
draw_rounded_box(2.5, SEC_A_Y + 0.3, 14.0, 0.55, '#FFF3E0', C['orange'], lw=1, zorder=5, radius=0.12)
ax.text(9.5, SEC_A_Y + 0.57, 'PipelineState: target_url | explored_urls | pending_urls | pending_test_urls | all_issues | iteration | report_data',
        ha='center', va='center', fontsize=9.1, color=C['orange'], zorder=6, fontweight='bold')


# ─── 3B: 自适应遍历器 (y: 10.6 ~ 14.8) ───
SEC_B_Y = 10.6
SEC_B_H = 4.2
draw_rounded_box(2.2, SEC_B_Y, 18.4, SEC_B_H, '#E8F5E9', C['green'], lw=1.5, alpha=0.5, zorder=1, radius=0.25)
ax.text(11.4, SEC_B_Y + SEC_B_H - 0.3, '自适应智能遍历器 (Adaptive Crawler)',
        ha='center', va='center', fontsize=15.4, fontweight='bold', color=C['green'], zorder=5)

# 子模块
modules_b = [
    (2.5,  SEC_B_Y + 1.8, 3.2, 1.7, 'Playwright 浏览器池', ['BrowserPool 单例', '异步页面池 (Queue)', 'Chromium 无头浏览器', '导航/点击/截图/滚动'], C['green'], C['green_l']),
    (6.0,  SEC_B_Y + 1.8, 3.2, 1.7, '页面分析器',          ['A11y树 快照', 'DOM结构提取', 'BoundingBox坐标', '内容哈希 (SHA-256)'], C['teal'], C['teal_l']),
    (9.5,  SEC_B_Y + 1.8, 3.2, 1.7, '启发式评分策略',      ['基础分50 (0-100)', 'URL模式匹配 ±30/15/20', '深度惩罚 线性递减', '父页面加成 +15/+10'], C['indigo'], C['indigo_l']),
    (13.0, SEC_B_Y + 1.8, 3.2, 1.7, '语义去重器',          ['SHA-256 精确匹配', 'DOM结构签名 (MD5)', '模板组 ≥3 自动跳过', '电商/博客模板检测'], C['purple'], C['purple_l']),
    (16.5, SEC_B_Y + 1.8, 3.2, 1.7, '突发事件响应器',      ['Cookie同意 (5选择器)', '弹窗/模态框 (6选择器)', '广告遮罩 (JS检测)', '三级降级处理策略'], C['red'], C['red_l']),
]
for (mx, my, mw, mh, title, items, tc, bc) in modules_b:
    draw_rounded_box(mx, my, mw, mh, bc, tc, lw=1.2, zorder=5, radius=0.15)
    ax.text(mx + mw/2, my + mh - 0.25, title, ha='center', va='center',
            fontsize=10.5, fontweight='bold', color=tc, zorder=6)
    for i, item in enumerate(items):
        ax.text(mx + 0.15, my + mh - 0.6 - i * 0.28, f"• {item}",
                ha='left', va='center', fontsize=8.4, color=C['text_l'], zorder=6)

# 流程箭头
for i in range(4):
    x1 = modules_b[i][0] + modules_b[i][2]
    x2 = modules_b[i+1][0]
    yy = SEC_B_Y + 2.65
    draw_arrow(x1, yy, x2, yy, C['green'], lw=1.5)

# 状态图标签
draw_rounded_box(2.5, SEC_B_Y + 0.2, 7.0, 0.5, C['green_l'], C['green'], lw=1, zorder=5, radius=0.12)
ax.text(6.0, SEC_B_Y + 0.45, 'ApplicationStateGraph: DISCOVERED → EXPLORING → EXPLORED → TESTING → TESTED',
        ha='center', va='center', fontsize=9.1, color=C['green'], zorder=6, fontweight='bold')

# 缓存标签
draw_rounded_box(10.0, SEC_B_Y + 0.2, 5.0, 0.5, C['green_l'], C['green'], lw=1, zorder=5, radius=0.12)
ax.text(12.5, SEC_B_Y + 0.45, '_page_data_cache: Explore↔Test 共享缓存',
        ha='center', va='center', fontsize=9.1, color=C['green'], zorder=6, fontweight='bold')

# WebSocket通知标签
draw_rounded_box(15.5, SEC_B_Y + 0.2, 4.8, 0.5, C['teal_l'], C['teal'], lw=1, zorder=5, radius=0.12)
ax.text(17.9, SEC_B_Y + 0.45, 'WebSocket 实时通知 → 前端',
        ha='center', va='center', fontsize=9.1, color=C['teal'], zorder=6, fontweight='bold')


# ─── 3C: 检测引擎 (y: 5.8 ~ 10.2) ───
SEC_C_Y = 5.8
SEC_C_H = 4.5
draw_rounded_box(2.2, SEC_C_Y, 18.4, SEC_C_H, '#FFEBEE', C['red'], lw=1.5, alpha=0.35, zorder=1, radius=0.25)
ax.text(11.4, SEC_C_Y + SEC_C_H - 0.3, '多层次无障碍检测引擎 (Detection Engine)',
        ha='center', va='center', fontsize=15.4, fontweight='bold', color=C['red'], zorder=5)

# Layer 1: 规则检测
draw_rounded_box(2.5, SEC_C_Y + 0.8, 5.5, 3.1, '#E3F2FD', C['blue'], lw=1.5, zorder=5, radius=0.2)
draw_small_box(2.7, SEC_C_Y + 3.5, 2.0, 0.3, 'Layer 1', C['blue'], fs=10.5, zorder=6)
ax.text(5.25, SEC_C_Y + 3.55, '规则检测 (7条WCAG规则)', ha='center', va='center',
        fontsize=11.9, fontweight='bold', color=C['blue'], zorder=6)

rules_text = [
    'img-alt (1.1.1)      图片替代文本缺失',
    'img-alt-quality (1.1.1)  无意义alt文本',
    'form-label (1.3.1)   表单标签关联',
    'heading-order (1.3.1) 标题层级跳跃',
    'html-lang (3.1.1)    页面语言声明',
    'landmark (1.3.1)     地标结构完整性',
    'link-text (2.4.4)    链接文本可理解性',
]
for i, r in enumerate(rules_text):
    ax.text(2.7, SEC_C_Y + 3.05 - i * 0.3, r, ha='left', va='center',
            fontsize=8.1, color=C['text_l'], zorder=6)

ax.text(5.25, SEC_C_Y + 0.95, 'RuleRegistry 可扩展注册架构', ha='center', va='center',
        fontsize=8.4, color=C['blue'], zorder=6, style='italic')

# Layer 2: AI语义分析
draw_rounded_box(8.3, SEC_C_Y + 0.8, 5.5, 3.1, '#E8F5E9', C['green'], lw=1.5, zorder=5, radius=0.2)
draw_small_box(8.5, SEC_C_Y + 3.5, 2.0, 0.3, 'Layer 2', C['green'], fs=10.5, zorder=6)
ax.text(11.05, SEC_C_Y + 3.55, 'AI语义分析 (LLM)', ha='center', va='center',
        fontsize=11.9, fontweight='bold', color=C['green'], zorder=6)

ai_items = [
    '输入: A11y树 + HTML + 规则结果',
    '覆盖 WCAG 四大原则:',
    '  可感知 / 可操作 / 可理解 / 鲁棒',
    '重点: alt语义质量、ARIA正确性',
    '  表单标签清晰度、结构逻辑性',
    'detected_by: "ai"',
    'JSON解析 + 代码块格式兼容',
]
for i, item in enumerate(ai_items):
    ax.text(8.5, SEC_C_Y + 3.05 - i * 0.3, item, ha='left', va='center',
            fontsize=8.1, color=C['text_l'], zorder=6)

# Layer 3: 视觉分析
draw_rounded_box(14.1, SEC_C_Y + 0.8, 6.2, 3.1, '#FFF3E0', C['orange'], lw=1.5, zorder=5, radius=0.2)
draw_small_box(14.3, SEC_C_Y + 3.5, 2.0, 0.3, 'Layer 3', C['orange'], fs=10.5, zorder=6)
ax.text(17.2, SEC_C_Y + 3.55, '多模态视觉分析 (Vision LLM)', ha='center', va='center',
        fontsize=11.9, fontweight='bold', color=C['orange'], zorder=6)

vision_items = [
    '截图 Base64 + BBox (≤80元素)',
    '核心: "元素看起来像什么"',
    '    vs "标签说的是什么"',
    '→ 捕获语义不一致问题',
    'detected_by: "vision_ai"',
    'element_selector 三层去重',
]
for i, item in enumerate(vision_items):
    ax.text(14.3, SEC_C_Y + 3.05 - i * 0.3, item, ha='left', va='center',
            fontsize=8.1, color=C['text_l'], zorder=6)

# VisualAnnotator
draw_rounded_box(14.3, SEC_C_Y + 0.9, 5.8, 0.6, C['amber_l'], C['amber'], lw=1, zorder=6, radius=0.12)
ax.text(17.2, SEC_C_Y + 1.2, 'VisualAnnotator: 四策略BBox匹配 + 严重度色彩标注 + 图例',
        ha='center', va='center', fontsize=8.1, fontweight='bold', color=C['amber'], zorder=7)

# 层间箭头
draw_arrow(8.0, SEC_C_Y + 2.3, 8.3, SEC_C_Y + 2.3, C['arrow_dark'], lw=2)
draw_arrow(13.8, SEC_C_Y + 2.3, 14.1, SEC_C_Y + 2.3, C['arrow_dark'], lw=2)

# 层间标签
ax.text(8.15, SEC_C_Y + 2.6, '→', ha='center', va='center', fontsize=19.6, fontweight='bold', color=C['arrow_dark'], zorder=7)
ax.text(13.95, SEC_C_Y + 2.6, '→', ha='center', va='center', fontsize=19.6, fontweight='bold', color=C['arrow_dark'], zorder=7)


# 引擎层内部垂直箭头
draw_arrow(6.0, SEC_A_Y, 6.0, SEC_B_Y + SEC_B_H + 0.1, C['green'], lw=2, style='->')
draw_arrow(16.0, SEC_A_Y, 16.0, SEC_B_Y + SEC_B_H + 0.1, C['red'], lw=2, style='->', ls='--')
ax.text(5.4, SEC_B_Y + SEC_B_H + 0.2, 'Explore', ha='center', va='center',
        fontsize=9.8, color=C['green'], fontweight='bold', zorder=7)
ax.text(16.6, SEC_B_Y + SEC_B_H + 0.2, 'Test', ha='center', va='center',
        fontsize=9.8, color=C['red'], fontweight='bold', zorder=7)

draw_arrow(11, SEC_B_Y, 11, SEC_C_Y + SEC_C_H + 0.1, C['red'], lw=2, style='->')
ax.text(11.6, SEC_C_Y + SEC_C_H + 0.2, '页面数据', ha='center', va='center',
        fontsize=9.8, color=C['text_l'], fontweight='bold', zorder=7)


# ═══════════════════════════════════════════
#  Layer 4: 数据层 (y: 1.5 ~ 5.0)
# ═══════════════════════════════════════════
L4_Y = 1.5
L4_H = 3.8
draw_rounded_box(1.8, L4_Y, 19.0, L4_H, C['layer_data'], C['purple'], lw=2, alpha=0.4, zorder=0, radius=0.3)
draw_layer_label(L4_Y + L4_H/2, '数据层', C['purple'])

# PostgreSQL
draw_rounded_box(2.5, L4_Y + 0.3, 7.5, 3.1, C['white'], C['indigo'], lw=1.5, zorder=5, radius=0.2)
draw_small_box(2.7, L4_Y + 3.0, 5.5, 0.3, 'PostgreSQL 16 + pgvector', C['indigo'], fs=11.2, zorder=6)

tables = [
    ('projects',  'Project'),
    ('tasks',     'Task (6态生命周期)'),
    ('pages',     'Page (A11y树/截图)'),
    ('issues',    'Issue (rule/ai/vision)'),
    ('reports',   'Report (评分/摘要)'),
    ('annotations', 'Annotation (人工标注)'),
    ('agent_memories', 'Memory (三类记忆)'),
]
for i, (tname, desc) in enumerate(tables):
    col = i % 2
    row = i // 2
    tx = 2.8 + col * 3.6
    ty = L4_Y + 2.4 - row * 0.55
    draw_small_box(tx, ty, 3.3, 0.4, f"{tname}: {desc}", C['indigo_l'], tc=C['indigo'], fs=8.4, zorder=6, ec=C['indigo'], fw='normal')

# Redis
draw_rounded_box(10.5, L4_Y + 0.3, 4.5, 3.1, C['white'], C['red'], lw=1.5, zorder=5, radius=0.2)
draw_small_box(10.7, L4_Y + 3.0, 3.0, 0.3, 'Redis 7', C['red'], fs=11.2, zorder=6)
redis_items = ['任务状态缓存', '会话管理', 'WebSocket消息队列', '热数据临时存储']
for i, item in enumerate(redis_items):
    ax.text(12.75, L4_Y + 2.5 - i * 0.4, f"• {item}", ha='center', va='center',
            fontsize=9.8, color=C['text_l'], zorder=6)

# 文件存储
draw_rounded_box(15.5, L4_Y + 0.3, 5.0, 3.1, C['white'], C['teal'], lw=1.5, zorder=5, radius=0.2)
draw_small_box(15.7, L4_Y + 3.0, 3.0, 0.3, '文件存储', C['teal'], fs=11.2, zorder=6)
file_items = ['原始截图 (UUID命名)', '标注截图 (annotated_*)', '导出报告 (HTML/PDF/JSON)', 'Alembic 数据库迁移']
for i, item in enumerate(file_items):
    ax.text(18.0, L4_Y + 2.5 - i * 0.4, f"• {item}", ha='center', va='center',
            fontsize=9.8, color=C['text_l'], zorder=6)

# 数据层连接箭头
draw_arrow(8, L3_Y, 8, L4_Y + L4_H, C['indigo'], lw=2, style='<->')
draw_arrow(13, L3_Y, 13, L4_Y + L4_H, C['red'], lw=2, style='<->')
draw_arrow(17, L3_Y, 17, L4_Y + L4_H, C['teal'], lw=2, style='<->')


# ═══════════════════════════════════════════
#  底部: 技术栈标签
# ═══════════════════════════════════════════
ax.text(11, 0.8, 'Docker Compose 容器化编排  |  Nginx 反向代理  |  Alembic 数据库迁移  |  JWT 认证',
        ha='center', va='center', fontsize=12.6, color=C['grey'], zorder=5,
        bbox=dict(boxstyle='round,pad=0.3', facecolor='#ECEFF1', edgecolor='#B0BEC5'))


# ── 保存 ──
output_path = '/Users/guangzhi/Desktop/W4Agent/docs/W4Agent系统架构图.png'
plt.tight_layout(pad=0.5)
plt.savefig(output_path, dpi=180, bbox_inches='tight', facecolor=fig.get_facecolor())
plt.close()
print(f"架构图已生成: {output_path}")
