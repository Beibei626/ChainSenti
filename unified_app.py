"""
统一AI助手应用
整合大模型对话和情绪识别功能

独立前端版本 - 无需后端，可直接部署到 Streamlit Cloud
"""

import streamlit as st
import os
import sys
import traceback
from PIL import Image
import base64
import io
import sqlite3
from datetime import datetime
import random

DB_PATH = os.path.join(os.path.dirname(__file__), "roles.db")

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

import warnings
warnings.filterwarnings("ignore")
os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = 'true'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'


def init_database():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            personality TEXT,
            prompt_template TEXT NOT NULL,
            avatar_name TEXT,
            avatar_data TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    ''')
    conn.commit()
    conn.close()


def get_custom_roles():
    """获取所有自定义角色"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('SELECT * FROM roles WHERE is_active = 1 ORDER BY created_at DESC')
    roles = [dict(row) for row in c.fetchall()]
    conn.close()
    return roles


def create_custom_role(name, description, personality, prompt_template, avatar_name=None, avatar_data=None):
    """创建自定义角色"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    c.execute('''
        INSERT INTO roles (name, description, personality, prompt_template, avatar_name, avatar_data, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (name, description, personality, prompt_template, avatar_name, avatar_data, now, now))
    conn.commit()
    conn.close()
    return True


def delete_custom_role(role_id):
    """删除自定义角色"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE roles SET is_active = 0 WHERE id = ?', (role_id,))
    conn.commit()
    conn.close()
    return True


st.set_page_config(
    page_title="🧠 ChainSenti情链心智",
    page_icon="🎭",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Noto Sans SC', 'Inter', sans-serif;
    }

    html, body, [class*="stApp"] {
        overflow: auto !important;
    }

    .stApp {
        background: linear-gradient(135deg, #f0f9ff 0%, #faf5ff 100%);
    }

    section.main > div {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }

    .main-header {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%);
        color: white;
        padding: 1.2rem 1.5rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 12px 40px rgba(59, 130, 246, 0.3);
        margin-bottom: 1.2rem;
        animation: slideDown 0.6s ease-out;
        width: 100%;
        box-sizing: border-box;
    }

    @keyframes slideDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .main-header h1 {
        font-size: 1.6rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.3px;
        text-shadow: 0 2px 10px rgba(0,0,0,0.1);
        white-space: normal;
        word-wrap: break-word;
    }

    .main-header p {
        font-size: 0.85rem;
        margin: 0.4rem 0 0 0;
        opacity: 0.95;
        font-weight: 400;
        white-space: normal;
        word-wrap: break-word;
    }
    
    /* 侧边栏内的主标题样式调整 */
    [data-testid="stSidebar"] .main-header {
        padding: 1rem;
        margin-bottom: 1.5rem;
    }
    
    [data-testid="stSidebar"] .main-header h1 {
        font-size: 1.3rem;
    }
    
    [data-testid="stSidebar"] .main-header p {
        font-size: 0.75rem;
    }

    .stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3);
        letter-spacing: 0.3px;
    }

    .stButton > button:hover {
        transform: translateY(-3px) scale(1.02);
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.45);
    }

    .stButton > button:active {
        transform: translateY(-1px);
    }

    /* 专门的图像情绪分析按钮样式 */
    .emotion-analyze-btn button {
        background: linear-gradient(135deg, #ec4899 0%, #8b5cf6 50%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 16px !important;
        padding: 1rem 2rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 8px 30px rgba(139, 92, 246, 0.4) !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .emotion-analyze-btn button:hover {
        transform: translateY(-4px) scale(1.03) !important;
        box-shadow: 0 12px 40px rgba(139, 92, 246, 0.6) !important;
    }

    .emotion-analyze-btn button:active {
        transform: translateY(-2px) scale(1.01) !important;
    }

    .stButton > button[kind="secondary"] {
        background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
        color: #374151;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }

    .stButton > button[kind="secondary"]:hover {
        background: linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-right: 1px solid #e2e8f0;
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 1.2rem !important;
    }

    .sidebar-title {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 1.3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.75rem;
        background: rgba(255,255,255,0.9);
        padding: 0.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        border: 1px solid #e5e7eb;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.75rem;
        font-size: 0.95rem;
        font-weight: 600;
        border-radius: 12px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        color: #6b7280;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(59, 130, 246, 0.08);
        color: #3b82f6;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.35);
    }

    [data-testid="stFileUploader"] {
        border: 2px dashed #cbd5e1;
        border-radius: 16px;
        padding: 2rem 1.5rem;
        background: linear-gradient(135deg, #fafafa 0%, #f8fafc 100%);
        transition: all 0.3s ease;
    }

    [data-testid="stFileUploader"]:hover {
        border-color: #3b82f6;
        background: linear-gradient(135deg, #f0f9ff 0%, #f5f3ff 100%);
    }

    .stChatMessage {
        margin: 0.75rem 0;
        padding: 0.5rem 0;
    }

    .stChatMessage[data-testid="stChatMessageUser"] {
        animation: slideInRight 0.3s ease-out;
    }

    .stChatMessage[data-testid="stChatMessageAssistant"] {
        animation: slideInLeft 0.3s ease-out;
    }

    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    .welcome-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e5e7eb;
        border-radius: 20px;
        padding: 2.5rem 2rem;
        text-align: center;
        box-shadow: 0 10px 40px rgba(0,0,0,0.06);
        margin: 1rem 0;
        animation: fadeInUp 0.5s ease-out;
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .welcome-card h3 {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.75rem;
    }

    .welcome-card p {
        color: #6b7280;
        font-size: 1rem;
        margin: 0.3rem 0;
    }

    .greeting-card {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 10px 30px rgba(59, 130, 246, 0.25);
        animation: popIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    }

    @keyframes popIn {
        0% {
            opacity: 0;
            transform: scale(0.9);
        }
        100% {
            opacity: 1;
            transform: scale(1);
        }
    }

    .greeting-card h4 {
        font-size: 1.2rem;
        margin: 0 0 0.5rem 0;
        font-weight: 600;
    }

    .greeting-card p {
        opacity: 0.95;
        margin: 0;
        font-size: 0.95rem;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid #e5e7eb;
        background: white;
        transition: all 0.3s ease;
        font-size: 0.95rem;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
    }

    .stSelectbox > div > div {
        border-radius: 12px;
        border: 2px solid #e5e7eb;
        background: white;
    }

    .stSelectbox > div > div:focus-within {
        border-color: #3b82f6;
        box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
    }

    .emotion-tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
        margin: 0.25rem 0.25rem 0 0;
    }

    .role-preview-card {
        background: white;
        border-radius: 16px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #f3f4f6;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
    }

    .role-preview-card:hover {
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }

    .result-card {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.06);
        border: 1px solid #f3f4f6;
        animation: fadeInUp 0.4s ease-out;
    }

    .emotion-result {
        border-radius: 16px;
        padding: 1.25rem;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }

    .emotion-result h4 {
        margin: 0;
        font-size: 1.15rem;
        font-weight: 600;
    }

    .emotion-result p {
        margin: 0.5rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.95;
    }

    .probability-bar {
        background: #f3f4f6;
        border-radius: 10px;
        height: 16px;
        margin: 0.25rem 0 0.75rem 0;
        overflow: hidden;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
    }

    .probability-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .prob-label {
        font-weight: 600;
        color: #374151;
        font-size: 0.9rem;
    }

    .prob-value {
        color: #6b7280;
        font-size: 0.85rem;
        font-weight: 500;
    }

    /* 左右对话气泡样式 */
    .chat-container {
        max-width: 100%;
        padding: 0.5rem;
        padding-bottom: 2rem;
    }

    .chat-message-wrapper {
        display: flex;
        margin-bottom: 1.25rem;
        animation: fadeIn 0.3s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .user-message-wrapper {
        justify-content: flex-end;
    }

    .user-bubble-container {
        display: inline-flex;
        flex-direction: column;
        align-items: flex-end;
        max-width: 75%;
    }

    .assistant-message-wrapper {
        justify-content: flex-start;
    }

    .chat-bubble {
        max-width: 75%;
        border-radius: 18px;
        padding: 0.75rem 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        position: relative;
        word-wrap: break-word;
        overflow-wrap: break-word;
        word-break: break-word;
        display: inline-block;
        white-space: pre-wrap;
        line-height: 1.5;
    }

    .user-bubble {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        color: white;
        border-bottom-right-radius: 4px;
        width: fit-content;
        max-width: 100%;
    }

    .assistant-bubble {
        background: white;
        color: #1f2937;
        border-bottom-left-radius: 4px;
        border: 1px solid #e5e7eb;
        width: fit-content;
        max-width: 75%;
    }

    .emotion-tag {
        display: block;
        background: linear-gradient(135deg, #f0f9ff 0%, #faf5ff 100%);
        padding: 0.35rem 0.7rem;
        border-radius: 12px;
        font-size: 0.8rem;
        margin-top: 0.5rem;
        color: #4b5563;
        border: 1px solid #dbeafe;
        clear: both;
    }

    .message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.25rem;
        flex-shrink: 0;
        background: transparent !important;
        border: none !important;
    }

    .user-avatar {
        margin-left: 0.75rem;
    }

    .assistant-avatar {
        margin-right: 0.75rem;
    }

    .timestamp {
        font-size: 0.7rem;
        color: #9ca3af;
        margin-top: 0.25rem;
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    
    /* 只在对话页面固定输入框在屏幕底部 */
    /* 通过 body 属性或更精确的选择器来限定作用域 */
    .stApp [data-testid="stTextInput"]:not(.st-emotion-cache-*) {
        /* 默认不固定 */
        position: relative;
    }
    
    /* 只在聊天标签页内固定输入框 */
    .tab-chat [data-testid="stTextInput"] {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 0.75rem 1rem;
        background: white;
        border-top: 1px solid #e5e7eb;
        z-index: 1000;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }
    
    [data-testid="stTextInput"] input {
        max-width: 800px;
        margin: 0 auto;
    }
    
    /* 聊天容器固定高度，可滚动 */
    .chat-container {
        max-width: 100%;
        padding: 0.5rem;
        padding-bottom: 100px;  /* 为输入框预留空间 */
        max-height: calc(100vh - 280px);
        overflow-y: auto;
    }
    
    hr {
        margin: 1rem 0;
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, #e5e7eb, transparent);
    }

    .footer-text {
        text-align: center;
        color: #9ca3af;
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }

    [data-testid="stExpander"] {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    [data-testid="stExpander"] > div {
        background: white;
    }

    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #e5e7eb, transparent);
        margin: 1rem 0;
    }

    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.5rem;
        animation: pulse 2s infinite;
    }

    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }

    .status-indicator.ready {
        background: #10b981;
    }

    @media (max-width: 768px) {
        .main-header {
            padding: 1rem 1.5rem;
            border-radius: 16px;
        }

        .main-header h1 {
            font-size: 1.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 1rem;
            font-size: 0.85rem;
        }

        .welcome-card {
            padding: 1.5rem 1rem;
        }
    }

    @media (max-width: 480px) {
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.35rem;
            padding: 0.35rem;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 0.4rem 0.75rem;
            font-size: 0.8rem;
        }
    }

    /* 自定义角色创建表单样式 */
    .role-creation-form {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
    }

    .custom-role-card {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid #fbbf24;
        transition: all 0.3s ease;
    }

    .custom-role-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(251, 191, 36, 0.3);
    }
</style>
""", unsafe_allow_html=True)

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TEXT_MODEL_PATH = r"c:\Users\28050\Desktop\All\Emotion Recognition\loss\Text"
IMAGE_MODEL_PATH = r"c:\Users\28050\Desktop\All\Emotion Recognition\loss\Image\Image_emotion_model.pth"
LABEL_ENCODER_PATH = r"c:\Users\28050\Desktop\All\Emotion Recognition\loss\Text\label_encoder.pkl"
ROLE_IMAGES_PATH = r"c:\Users\28050\Desktop\All\Assistant\images"
USER_AVATAR_PATH = r"c:\Users\28050\Desktop\All\Assistant\images\彭于晏.jpg"


def get_user_avatar():
    """获取用户头像（图片路径或默认emoji）"""
    if os.path.exists(USER_AVATAR_PATH):
        return USER_AVATAR_PATH
    return "👤"


ROLES_CONFIG = {
    "einstein": {
        "name": "阿尔伯特·爱因斯坦",
        "description": "著名物理学家，相对论创始人",
        "personality": "睿智、温和、富有想象力",
        "prompt": "你是阿尔伯特·爱因斯坦，20世纪最伟大的物理学家之一。请用他的风格回答问题，保持睿智、简洁而富有洞察力。",
        "image": "einstein.jpg"
    },
    "shakespeare": {
        "name": "威廉·莎士比亚",
        "description": "英国文学史上最杰出的戏剧家和诗人",
        "personality": "优雅、富有诗意、充满智慧",
        "prompt": "你是威廉·莎士比亚，英国文学巨匠。请用诗意的语言和优雅的风格回答问题。",
        "image": "shakespeare.jpg"
    },
    "customer_service": {
        "name": "智能客服",
        "description": "专业的客户服务代表",
        "personality": "友好、耐心，专业",
        "prompt": "你是一位专业的客户服务代表，请友好、耐心地解答用户的问题。",
        "image": "customer_service.jpg"
    },
    "emotion_bot": {
        "name": "情感机器人",
        "description": "专注于情感交流的AI助手",
        "personality": "善解人意、温暖、富有同理心",
        "prompt": "你是一位专注于情感交流的AI助手，善于倾听和理解用户的情感需求。请用温暖、善解人意的方式与用户交流，给予情感支持和安慰。",
        "image": "emotion_bot.png"
    }
}


def log_message(msg):
    """打印日志消息"""
    print(f"[INFO] {msg}", flush=True)


def log_error(msg):
    """打印错误消息"""
    print(f"[ERROR] {msg}", flush=True, file=sys.stderr)


def check_file_exists(file_path, description):
    """检查文件是否存在"""
    exists = os.path.exists(file_path)
    status = "✅ 存在" if exists else "❌ 不存在"
    log_message(f"{description}: {status} - {file_path}")
    return exists


def check_model_files():
    """检查所有模型文件"""
    log_message("开始检查模型文件...")
    
    checks = [
        (TEXT_MODEL_PATH, "文本模型目录"),
        (LABEL_ENCODER_PATH, "标签编码器"),
        (IMAGE_MODEL_PATH, "图像模型文件"),
    ]
    
    all_exist = True
    for path, desc in checks:
        if not check_file_exists(path, desc):
            all_exist = False
    
    return all_exist


def init_session_state():
    """初始化会话状态"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_role" not in st.session_state:
        st.session_state.current_role = None
    if "role_info" not in st.session_state:
        st.session_state.role_info = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "enable_emotion_detection" not in st.session_state:
        st.session_state.enable_emotion_detection = True
    if "text_predictor" not in st.session_state:
        st.session_state.text_predictor = None
    if "image_predictor" not in st.session_state:
        st.session_state.image_predictor = None
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())[:8]
    if "conversation_started" not in st.session_state:
        st.session_state.conversation_started = False


def load_text_model():
    """加载文本情绪模型"""
    if st.session_state.text_predictor is not None:
        return True, None
    
    log_message("开始加载文本情绪模型...")
    
    try:
        if not os.path.exists(TEXT_MODEL_PATH):
            error_msg = f"文本模型目录不存在: {TEXT_MODEL_PATH}"
            log_error(error_msg)
            return False, error_msg
        
        if not os.path.exists(LABEL_ENCODER_PATH):
            error_msg = f"标签编码器文件不存在: {LABEL_ENCODER_PATH}"
            log_error(error_msg)
            return False, error_msg
        
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import joblib
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        log_message(f"使用设备: {device}")
        
        tokenizer = AutoTokenizer.from_pretrained(TEXT_MODEL_PATH)
        log_message("Tokenizer加载成功")
        
        text_model = AutoModelForSequenceClassification.from_pretrained(TEXT_MODEL_PATH)
        text_model.to(device)
        text_model.eval()
        log_message("模型加载成功")
        
        label_encoder = joblib.load(LABEL_ENCODER_PATH)
        log_message("标签编码器加载成功")
        
        st.session_state.text_predictor = {
            'model': text_model,
            'tokenizer': tokenizer,
            'label_encoder': label_encoder,
            'device': device
        }
        
        log_message("文本情绪模型加载完成")
        return True, None
        
    except Exception as e:
        error_msg = f"加载失败: {str(e)}\n{traceback.format_exc()}"
        log_error(error_msg)
        return False, error_msg


def load_image_model():
    """加载图像情绪模型"""
    if st.session_state.image_predictor is not None:
        return True, None
    
    log_message("开始加载图像情绪模型...")
    
    try:
        if not os.path.exists(IMAGE_MODEL_PATH):
            error_msg = f"图像模型文件不存在: {IMAGE_MODEL_PATH}"
            log_error(error_msg)
            return False, error_msg
        
        import torch
        import torch.nn as nn
        from torchvision import transforms, models
        
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        log_message(f"使用设备: {device}")
        
        image_model = models.resnet50(weights=None)
        image_model.fc = nn.Sequential(
            nn.Dropout(0.5),
            nn.Linear(image_model.fc.in_features, 512),
            nn.ReLU(),
            nn.BatchNorm1d(512),
            nn.Dropout(0.3),
            nn.Linear(512, 7)
        )
        log_message("模型结构创建成功")
        
        checkpoint = torch.load(IMAGE_MODEL_PATH, map_location=device, weights_only=False)
        
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            state_dict = checkpoint['model_state_dict']
            log_message("检测到checkpoint格式")
            if 'best_val_acc' in checkpoint:
                log_message(f"最佳验证准确率: {checkpoint['best_val_acc']:.2f}%")
        else:
            state_dict = checkpoint
            log_message("检测到旧格式state_dict")
        
        image_model.load_state_dict(state_dict)
        log_message("模型权重加载成功")
        
        image_model.to(device)
        image_model.eval()
        
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                               std=[0.229, 0.224, 0.225])
        ])
        
        st.session_state.image_predictor = {
            'model': image_model,
            'transform': transform,
            'device': device
        }
        
        log_message("图像情绪模型加载完成")
        return True, None
        
    except Exception as e:
        error_msg = f"加载失败: {str(e)}\n{traceback.format_exc()}"
        log_error(error_msg)
        return False, error_msg


EMOTION_EMOJI_MAP = {
    '积极': '😊', 'positive': '😊', 'joy': '😊', 'happiness': '😄', 'happy': '😄',
    '中性': '�', 'neutral': '😐',
    '负面': '�', 'negative': '😔', 'sadness': '😢', 'sad': '😢',
    'anger': '😠', 'angry': '😠', 'fear': '😨', 'surprise': '😮'
}

EMOTION_LABEL_MAP = {
    '正面': '积极', 'positive': '积极', '阳性': '积极',
    '负面': '负面', 'negative': '负面', '阴性': '负面',
    '中性': '中性', 'neutral': '中性'
}

def get_emotion_emoji(emotion: str) -> str:
    """获取情绪对应的emoji"""
    return EMOTION_EMOJI_MAP.get(emotion, '❓')

def normalize_emotion_label(emotion: str) -> str:
    """标准化情绪标签（将模型输出转换成统一中文标签）"""
    return EMOTION_LABEL_MAP.get(emotion, emotion)


def build_emotion_aware_message(role_id: str, message: str, emotion_result: dict = None) -> str:
    """为情感机器人构建情绪感知的消息"""
    if role_id != "emotion_bot" or not emotion_result:
        return message
    
    emotion = emotion_result.get('emotion', 'neutral')
    confidence = emotion_result.get('confidence', 0.0)
    emoji = get_emotion_emoji(emotion)
    
    emotion_contexts = {
        '积极': f'用户似乎情绪积极（{emoji} {emotion}，置信度{confidence:.0%}）',
        '正面': f'用户似乎情绪积极（{emoji} {emotion}，置信度{confidence:.0%}）',
        '负面': f'用户似乎情绪低落或消极（{emoji} {emotion}，置信度{confidence:.0%}），请给予更多关心和支持',
        '中性': f'用户情绪较为平静（{emoji} {emotion}，置信度{confidence:.0%}）'
    }
    
    context = emotion_contexts.get(emotion, emotion_contexts['中性'])
    
    enhanced_message = f"""【情绪感知】{context}

用户消息：{message}

请根据用户的情绪状态，以温暖、善解人意的方式回应。在回应中适当表达理解和共情。"""
    
    return enhanced_message


def get_role_avatar(role_info):
    """获取角色头像（图片路径或emoji）"""
    if role_info and role_info.get('image'):
        image_path = os.path.join(ROLE_IMAGES_PATH, role_info['image'])
        if os.path.exists(image_path):
            return image_path
    return "🤖"


def image_to_base64(image_path):
    """将图片转换为base64编码"""
    import base64
    try:
        with open(image_path, "rb") as img_file:
            img_data = base64.b64encode(img_file.read()).decode("utf-8")
            # 根据文件扩展名确定MIME类型
            ext = os.path.splitext(image_path)[1].lower()
            if ext == '.png':
                mime_type = 'image/png'
            elif ext in ['.jpg', '.jpeg']:
                mime_type = 'image/jpeg'
            elif ext == '.gif':
                mime_type = 'image/gif'
            else:
                mime_type = 'image/jpeg'
            return img_data, mime_type
    except Exception:
        return None, 'image/jpeg'


def get_user_avatar():
    """获取用户头像"""
    user_avatar_path = r"c:\Users\28050\Desktop\All\Assistant\images\彭于晏.jpg"
    if os.path.exists(user_avatar_path):
        return user_avatar_path
    return "👤"


def analyze_text_emotion(text: str):
    """分析文本情绪"""
    if st.session_state.text_predictor is None:
        success, error = load_text_model()
        if not success:
            return None
    
    try:
        import torch
        
        predictor = st.session_state.text_predictor
        model = predictor['model']
        tokenizer = predictor['tokenizer']
        label_encoder = predictor['label_encoder']
        device = predictor['device']
        
        inputs = tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=128,
            return_tensors="pt"
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            pred_label = torch.argmax(probs, dim=-1).cpu().numpy()[0]
            confidence = probs[0][pred_label].item()
        
        emotion = label_encoder.inverse_transform([pred_label])[0]
        all_probs = probs[0].cpu().numpy()
        
        # 标准化情绪标签
        normalized_emotion = normalize_emotion_label(emotion)
        
        return {
            'emotion': normalized_emotion,
            'confidence': confidence,
            'probabilities': {
                normalize_emotion_label(label): float(prob)
                for label, prob in zip(label_encoder.classes_, all_probs)
            }
        }
    except Exception as e:
        st.error(f"❌ 文本情绪分析失败: {str(e)}")
        return None


def analyze_image_emotion(image):
    """分析图像情绪"""
    if st.session_state.image_predictor is None:
        success, error = load_image_model()
        if not success:
            return None
    
    try:
        import torch
        
        predictor = st.session_state.image_predictor
        model = predictor['model']
        transform = predictor['transform']
        device = predictor['device']
        
        idx_to_label = {
            0: 'angry', 1: 'disgust', 2: 'fear',
            3: 'happy', 4: 'sad', 5: 'surprise', 6: 'neutral'
        }
        
        image_rgb = image.convert('RGB')
        image_tensor = transform(image_rgb).unsqueeze(0).to(device)
        
        with torch.no_grad():
            outputs = model(image_tensor)
            probs = torch.nn.functional.softmax(outputs, dim=1)
            pred_idx = torch.argmax(probs, dim=1).item()
            confidence = probs[0][pred_idx].item()
        
        emotion = idx_to_label[pred_idx]
        all_probs = probs[0].cpu().numpy()
        
        return {
            'emotion': emotion,
            'confidence': confidence,
            'probabilities': {
                idx_to_label[i]: float(prob)
                for i, prob in enumerate(all_probs)
            }
        }
    except Exception as e:
        st.error(f"❌ 图像情绪分析失败: {str(e)}")
        return None


def chat_with_backend(role_id: str, message: str, chat_history: list, prompt_template: str = None,
                      session_id: str = "default", emotion_context: dict = None) -> str:
    """模拟对话响应 - 独立前端版本"""
    
    responses = [
        "您好！有什么我可以帮助您的吗？",
        "我理解您的意思，让我来帮您分析一下。",
        "这是一个很有趣的问题！让我思考一下...",
        "好的，我明白了。请问还有什么需要我帮忙的吗？",
        "感谢您的分享！如果您有其他问题，随时问我。",
        "好的，我正在倾听。请告诉我更多细节。",
        "让我为您解答：这个功能目前正在开发中。",
        "您的想法很有价值！我会认真考虑的。",
        "没问题，我会尽力帮助您。请问具体是什么情况？",
        "明白了。让我为您提供一些建议..."
    ]
    
    return random.choice(responses)


def show_role_management_page():
    """显示角色管理页面"""
    st.markdown("## 🎨 创建自定义角色")
    st.markdown("---")

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 角色基本信息")
        role_name = st.text_area(
            "角色名称（必填）",
            placeholder="例如：智能助手",
            height=80
        )
        role_description = st.text_area(
            "角色描述",
            placeholder="描述这个角色的身份和特点...",
            height=80
        )
        role_personality = st.text_area(
            "性格特征",
            placeholder="例如：友善、专业、有耐心",
            height=80
        )

    with col2:
        st.subheader("💡 提示词模板（必填）")
        st.caption("定义角色行为的提示词，这是角色对话的核心")
        prompt_template = st.text_area(
            "提示词模板",
            placeholder="你是一个善良的AI助手。请用友好、耐心的方式回答用户的问题...",
            height=200
        )

    st.markdown("---")

    col_upload, col_button = st.columns([2, 1])
    with col_upload:
        uploaded_file = st.file_uploader(
            "🎭 上传角色头像（可选）",
            type=['jpg', 'png', 'gif'],
            help="支持 JPG、PNG、GIF 格式，建议尺寸 200x200"
        )
        
        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            st.image(file_bytes, width=100, caption="头像预览")
            avatar_data = base64.b64encode(file_bytes).decode()
        else:
            avatar_data = None

    with col_button:
        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("✨ 创建角色", use_container_width=True):
            if not role_name.strip():
                st.error("❌ 请填写角色名称")
            elif not prompt_template.strip():
                st.error("❌ 请填写提示词模板")
            else:
                if create_custom_role(
                    name=role_name.strip(),
                    description=role_description.strip() if role_description.strip() else None,
                    personality=role_personality.strip() if role_personality.strip() else None,
                    prompt_template=prompt_template.strip(),
                    avatar_name=uploaded_file.name if uploaded_file else None,
                    avatar_data=avatar_data
                ):
                    st.success("✅ 角色创建成功！")
                    st.rerun()
                else:
                    st.error("❌ 角色创建失败")

    st.markdown("---")

    st.subheader("📋 已创建的角色")
    custom_roles = get_custom_roles()
    
    if not custom_roles:
        st.info("暂无自定义角色，请在上方创建您的第一个角色！")
    else:
        for role in custom_roles:
            with st.container():
                cols = st.columns([1, 4, 1])
                with cols[0]:
                    if role['avatar_data']:
                        st.image(base64.b64decode(role['avatar_data']), width=60)
                    else:
                        st.markdown("👤")
                with cols[1]:
                    st.markdown(f"**✨ {role['name']}**")
                    if role['description']:
                        st.caption(f"描述: {role['description']}")
                    if role['personality']:
                        st.caption(f"性格: {role['personality']}")
                    st.caption(f"创建时间: {role['created_at'][:10]}")
                with cols[2]:
                    if st.button("🗑️", key=f"delete_{role['id']}"):
                        delete_custom_role(role['id'])
                        st.success("角色已删除")
                        st.rerun()
                st.markdown("---")


def show_diagnostic_info():
    """显示诊断信息"""
    with st.expander("🔧 诊断信息"):
        st.write("**检查模型文件...**")
        
        checks = [
            (TEXT_MODEL_PATH, "文本模型目录"),
            (LABEL_ENCODER_PATH, "标签编码器"),
            (IMAGE_MODEL_PATH, "图像模型文件"),
        ]
        
        for path, desc in checks:
            exists = os.path.exists(path)
            status = "✅ 存在" if exists else "❌ 不存在"
            color = "green" if exists else "red"
            st.markdown(f"- **{desc}**: :{color}[{status}]")
        
        try:
            import torch
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            st.markdown(f"- **PyTorch设备**: {device}")
            if torch.cuda.is_available():
                st.markdown(f"- **GPU**: {torch.cuda.get_device_name(0)}")
        except Exception as e:
            st.markdown(f"- **PyTorch**: ❌ 错误 - {str(e)}")


def show_chat_page():
    """显示对话页面"""
    
    st.markdown('<div class="tab-chat">', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🎭 角色选择</div>', unsafe_allow_html=True)
        
        preset_roles = {role_id: info["name"] for role_id, info in ROLES_CONFIG.items()}
        custom_roles = get_custom_roles()
        
        for custom_role in custom_roles:
            role_id = f"custom_{custom_role['id']}"
            preset_roles[role_id] = f"✨ {custom_role['name']}"
        
        role_keys = list(preset_roles.keys())
        default_index = role_keys.index("emotion_bot") if "emotion_bot" in role_keys else 0
        selected_role_id = st.selectbox(
            "选择一个角色：",
            options=role_keys,
            index=default_index,
            format_func=lambda x: preset_roles[x]
        )
        
        if selected_role_id.startswith("custom_"):
            custom_role_id = selected_role_id.replace("custom_", "")
            role_data = role_db.get_role_with_avatar(custom_role_id)
            if role_data:
                selected_role_info = {
                    "name": role_data["name"],
                    "description": role_data.get("description", ""),
                    "personality": role_data.get("personality", ""),
                    "prompt_template": role_data["prompt_template"],
                    "image": "",
                    "is_custom": True,
                    "avatar_data": role_data.get("avatar_data"),
                    "id": custom_role_id
                }
            else:
                selected_role_info = ROLES_CONFIG["emotion_bot"]
                st.error("❌ 角色不存在或已删除")
        else:
            selected_role_info = ROLES_CONFIG[selected_role_id]
            selected_role_info["is_custom"] = False

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        with st.container():
            col1, col2 = st.columns([1, 2])
            with col1:
                if selected_role_info.get("is_custom") and selected_role_info.get("avatar_data"):
                    try:
                        avatar_base64 = selected_role_info["avatar_data"]
                        st.markdown(
                            f'<img src="data:image/jpeg;base64,{avatar_base64}" '
                            f'style="width:70px;height:70px;border-radius:50%;object-fit:cover;">',
                            unsafe_allow_html=True
                        )
                    except Exception:
                        st.markdown("🤖")
                elif selected_role_info.get('image'):
                    image_path = os.path.join(ROLE_IMAGES_PATH, selected_role_info['image'])
                    if os.path.exists(image_path):
                        st.image(image_path, width=70)
                else:
                    st.markdown("🤖")
            with col2:
                role_display_name = "✨ " + selected_role_info['name'] if selected_role_info.get("is_custom") else selected_role_info['name']
                st.markdown(f"### {role_display_name}")
                st.markdown(f"*{selected_role_info.get('description', '')}*")
                st.markdown(f"**性格特征：** {selected_role_info.get('personality', '')}")

        if selected_role_id == "emotion_bot":
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            enable_emotion = st.checkbox("🎯 启用实时情绪检测", value=True)
            st.session_state.enable_emotion_detection = enable_emotion

            if enable_emotion:
                if st.session_state.text_predictor:
                    st.markdown('<span class="status-indicator ready"></span>✅ 文本情绪模型已就绪', unsafe_allow_html=True)
                else:
                    st.info("💡 首次分析时将自动加载模型")
        elif selected_role_info.get("is_custom"):
            st.session_state.enable_emotion_detection = False
        else:
            st.session_state.enable_emotion_detection = False

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        if st.button(" 开始对话", type="primary", use_container_width=True, key="start_chat_btn"):
            st.session_state.current_role = selected_role_id
            st.session_state.role_info = selected_role_info
            st.session_state.messages = []
            st.session_state.chat_history = []
            st.session_state.conversation_started = False  # 欢迎消息只显示一次
            st.rerun()

        if st.session_state.current_role:
            if st.button("🗑️ 清空对话", type="secondary", use_container_width=True, key="clear_chat_btn"):
                st.session_state.messages = []
                st.session_state.chat_history = []
                st.session_state.conversation_started = False
                st.rerun()

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        show_diagnostic_info()

    if not st.session_state.current_role:
        st.markdown("""
        <div class="welcome-card">
            <h3>👋 欢迎使用 ChainSenti 情链心智</h3>
            <p>请在左侧边栏选择一个角色，然后点击「开始对话」</p>
            <p style="color: #8b5cf6; font-size: 0.9rem; font-weight: 500;">💡 提示：情感机器人支持实时情绪分析功能</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        role_name = st.session_state.role_info.get("name", "助手") if st.session_state.role_info else "助手"
        
        if st.session_state.role_info and st.session_state.role_info.get("is_custom") and st.session_state.role_info.get("avatar_data"):
            role_avatar = st.session_state.role_info["avatar_data"]
        else:
            role_avatar = get_role_avatar(st.session_state.role_info)

        # 欢迎消息只在对话刚开始且没有发送任何消息时显示
        if not st.session_state.conversation_started and not st.session_state.messages:
            welcome_avatar = None
            if st.session_state.role_info and st.session_state.role_info.get("is_custom") and st.session_state.role_info.get("avatar_data"):
                welcome_avatar = f"data:image/jpeg;base64,{st.session_state.role_info['avatar_data']}"
            
            st.chat_message("assistant", avatar=welcome_avatar if welcome_avatar else role_avatar).markdown(
                f"""
                <div class="greeting-card">
                    <h4>✨ 你好！我是 {role_name}</h4>
                    <p>有什么我可以帮助你的吗？我随时在这里倾听你 😊</p>
                </div>
                """, unsafe_allow_html=True
            )

        # 使用自定义的左右对话气泡样式
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                # 用户消息 - 右侧
                user_av = get_user_avatar()
                if isinstance(user_av, str) and os.path.exists(user_av):
                    result = image_to_base64(user_av)
                    if result and result[0]:
                        avatar_html = f'<img src="data:{result[1]};base64,{result[0]}" class="message-avatar user-avatar" style="object-fit: cover;">'
                    else:
                        avatar_html = f'<div class="message-avatar user-avatar">👤</div>'
                else:
                    avatar_html = f'<div class="message-avatar user-avatar">{user_av if user_av else "👤"}</div>'
                
                emotion_html = ""
                if msg.get("emotion") and st.session_state.enable_emotion_detection and st.session_state.current_role == "emotion_bot":
                    emotion = msg["emotion"]['emotion']
                    confidence = msg["emotion"]['confidence']
                    emoji = get_emotion_emoji(emotion)
                    emotion_html = f'<div class="emotion-tag">{emoji} 情绪: {emotion} ({confidence:.1%})</div>'
                
                # 只有在有情绪标签时才包含div
                if emotion_html:
                    bubble_content = f"""
                    <div class="chat-message-wrapper user-message-wrapper">
                        <div class="user-bubble-container">
                            <div class="chat-bubble user-bubble">{msg["content"]}</div>
                            {emotion_html}
                        </div>
                        {avatar_html}
                    </div>
                    """
                else:
                    bubble_content = f"""
                    <div class="chat-message-wrapper user-message-wrapper">
                        <div class="user-bubble-container">
                            <div class="chat-bubble user-bubble">{msg["content"]}</div>
                        </div>
                        {avatar_html}
                    </div>
                    """
                
                st.markdown(bubble_content, unsafe_allow_html=True)
            else:
                # AI消息 - 左侧
                if st.session_state.role_info and st.session_state.role_info.get("is_custom") and st.session_state.role_info.get("avatar_data"):
                    avatar_html = f'<img src="data:image/jpeg;base64,{st.session_state.role_info["avatar_data"]}" class="message-avatar assistant-avatar" style="object-fit: cover;">'
                elif isinstance(role_avatar, str) and os.path.exists(role_avatar):
                    result = image_to_base64(role_avatar)
                    if result and result[0]:
                        avatar_html = f'<img src="data:{result[1]};base64,{result[0]}" class="message-avatar assistant-avatar" style="object-fit: cover;">'
                    else:
                        avatar_html = f'<div class="message-avatar assistant-avatar">🤖</div>'
                else:
                    avatar_html = f'<div class="message-avatar assistant-avatar">{role_avatar if role_avatar else "🤖"}</div>'
                
                st.markdown(f"""
                <div class="chat-message-wrapper assistant-message-wrapper">
                    {avatar_html}
                    <div class="chat-bubble assistant-bubble">{msg["content"]}</div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)  # 关闭chat-container

        if prompt := st.chat_input(f"向 {role_name} 提问..."):
            # 只显示一次用户消息
            user_av = get_user_avatar()
            if isinstance(user_av, str) and os.path.exists(user_av):
                result = image_to_base64(user_av)
                if result and result[0]:
                    avatar_html = f'<img src="data:{result[1]};base64,{result[0]}" class="message-avatar user-avatar" style="object-fit: cover;">'
                else:
                    avatar_html = f'<div class="message-avatar user-avatar">👤</div>'
            else:
                avatar_html = f'<div class="message-avatar user-avatar">{user_av if user_av else "👤"}</div>'

            emotion_result = None
            emotion_context = None
            emotion_html = ""
            # 只有在启用情绪检测且当前角色是"情绪机器人"时才分析情绪
            if st.session_state.enable_emotion_detection and st.session_state.current_role == "emotion_bot":
                with st.spinner("🔍 分析情绪中..."):
                    emotion_result = analyze_text_emotion(prompt)
                    if emotion_result:
                        emoji = get_emotion_emoji(emotion_result['emotion'])
                        emotion_html = f'<div class="emotion-tag">{emoji} 情绪: {emotion_result["emotion"]} ({emotion_result["confidence"]:.1%})</div>'
                        emotion_context = {
                            "emotion": emotion_result['emotion'],
                            "confidence": emotion_result['confidence']
                        }
            
            # 只渲染一次用户消息，带情绪标签
            if emotion_html:
                bubble_content = f"""
                <div class="chat-message-wrapper user-message-wrapper">
                    <div class="user-bubble-container">
                        <div class="chat-bubble user-bubble">{prompt}</div>
                        {emotion_html}
                    </div>
                    {avatar_html}
                </div>
                """
            else:
                bubble_content = f"""
                <div class="chat-message-wrapper user-message-wrapper">
                    <div class="user-bubble-container">
                        <div class="chat-bubble user-bubble">{prompt}</div>
                    </div>
                    {avatar_html}
                </div>
                """
            
            st.markdown(bubble_content, unsafe_allow_html=True)

            st.session_state.messages.append({"role": "user", "content": prompt, "emotion": emotion_result})
            st.session_state.conversation_started = True  # 标记对话已开始，隐藏欢迎消息

            enhanced_message = build_emotion_aware_message(
                st.session_state.current_role,
                prompt,
                emotion_result
            )

            # AI回复气泡
            if st.session_state.role_info and st.session_state.role_info.get("is_custom") and st.session_state.role_info.get("avatar_data"):
                ai_avatar_html = f'<img src="data:image/jpeg;base64,{st.session_state.role_info["avatar_data"]}" class="message-avatar assistant-avatar" style="object-fit: cover;">'
            elif isinstance(role_avatar, str) and os.path.exists(role_avatar):
                result = image_to_base64(role_avatar)
                if result and result[0]:
                    ai_avatar_html = f'<img src="data:{result[1]};base64,{result[0]}" class="message-avatar assistant-avatar" style="object-fit: cover;">'
                else:
                    ai_avatar_html = f'<div class="message-avatar assistant-avatar">🤖</div>'
            else:
                ai_avatar_html = f'<div class="message-avatar assistant-avatar">{role_avatar if role_avatar else "🤖"}</div>'
            
            # 显示AI思考并回复
            with st.spinner("思考中..."):
                custom_prompt = None
                if st.session_state.role_info and st.session_state.role_info.get("is_custom"):
                    custom_prompt = st.session_state.role_info.get("prompt_template")
                
                response = chat_with_backend(
                    st.session_state.current_role,
                    enhanced_message,
                    st.session_state.chat_history,
                    custom_prompt,
                    st.session_state.session_id,
                    emotion_context
                )
                
                # 显示AI气泡
                st.markdown(f"""
                <div class="chat-message-wrapper assistant-message-wrapper">
                    {ai_avatar_html}
                    <div class="chat-bubble assistant-bubble">{response}</div>
                </div>
                """, unsafe_allow_html=True)

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.chat_history.append({"role": "assistant", "content": response})
        
        st.markdown('</div>', unsafe_allow_html=True)  # 关闭 tab-chat


def uploaded_file_to_preview(uploaded_file):
    """将上传的文件转换为可用于预览的图像"""
    if uploaded_file is None:
        return None
    try:
        image = Image.open(uploaded_file)
        return image
    except Exception as e:
        return None


def show_image_emotion_page():
    """显示图像情绪识别页面"""
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        # 左侧：状态 + 上传 + 预览 + 按钮
        if st.session_state.image_predictor:
            st.markdown('<span class="status-indicator ready"></span>✅ 图像情绪模型已就绪', unsafe_allow_html=True)
        else:
            st.info("💡 首次分析时将自动加载模型")
        
        st.markdown("### 📤 上传图像")
        uploaded_file = st.file_uploader(
            "拖拽或点击上传人脸图像",
            type=['jpg', 'jpeg', 'png'],
            help="支持 JPG、PNG 格式的人脸图像"
        )
        
        # 图片预览放在下方，按钮放右侧
        if uploaded_file is not None:
            st.markdown("### 👁️ 图像预览 & 执行分析")
            # 两列布局：图片 + 按钮
            img_col, btn_col = st.columns([1, 1])
            with img_col:
                image = Image.open(uploaded_file)
                st.image(image, caption="上传的图像", width=220)
            with btn_col:
                st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
                st.markdown('<div class="emotion-analyze-btn">', unsafe_allow_html=True)
                analyze_btn = st.button("🎭 分析情绪", type="primary", use_container_width=True, key="image_analyze_btn")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("👆 请先上传一张人脸图像")
            analyze_btn = False
    
    with col_right:
        # 右侧：预展示模块 + 分析结果
        if uploaded_file is None:
            # 预展示模块
            st.markdown("### 🎯 分析结果")
            st.markdown("""
            <div class="result-card" style="text-align: center; padding: 2rem;">
                <p style="color: #6b7280; font-size: 1.1rem;">👆 请先上传一张人脸图像</p>
                <p style="color: #9ca3af; font-size: 0.9rem; margin-top: 0.5rem;">上传后点击「分析情绪」按钮查看结果</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 预展示的情绪类别
            st.markdown("### 📊 可识别的情绪类别")
            preview_emotions = [
                ('angry', '😠', '愤怒'),
                ('disgust', '🤢', '厌恶'),
                ('fear', '😨', '恐惧'),
                ('happy', '😄', '开心'),
                ('sad', '😢', '悲伤'),
                ('surprise', '😮', '惊喜'),
                ('neutral', '😐', '中性')
            ]
            for emotion, emoji, name in preview_emotions:
                st.markdown(f"""
                <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: #f9fafb; border-radius: 8px;">
                    <span style="font-size: 1.2rem; margin-right: 0.5rem;">{emoji}</span>
                    <span style="color: #4b5563; font-weight: 500;">{name} ({emotion})</span>
                </div>
                """, unsafe_allow_html=True)
        elif not analyze_btn:
            # 已上传但未分析
            st.markdown("### 🎯 分析结果")
            st.markdown("""
            <div class="result-card" style="text-align: center; padding: 2rem;">
                <p style="color: #3b82f6; font-size: 1.1rem;">⏳ 点击「分析情绪」按钮</p>
                <p style="color: #6b7280; font-size: 0.9rem; margin-top: 0.5rem;">图像已就绪，等待分析...</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # 已分析，显示结果
            with st.spinner("正在分析情绪..."):
                uploaded_file.seek(0)
                image = Image.open(uploaded_file)
                result = analyze_image_emotion(image)
            
            if result:
                st.markdown("### 🎯 分析结果")
                st.success(f"✅ 检测到情绪: **{result['emotion']}** (置信度: {result['confidence']:.2%})")

                emotion_colors = {
                    'angry': {'bg': 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)', 'emoji': '😠', 'name': '愤怒'},
                    'disgust': {'bg': 'linear-gradient(135deg, #9333ea 0%, #7c3aed 100%)', 'emoji': '🤢', 'name': '厌恶'},
                    'fear': {'bg': 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)', 'emoji': '😨', 'name': '恐惧'},
                    'happy': {'bg': 'linear-gradient(135deg, #10b981 0%, #059669 100%)', 'emoji': '😄', 'name': '开心'},
                    'sad': {'bg': 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', 'emoji': '😢', 'name': '悲伤'},
                    'surprise': {'bg': 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)', 'emoji': '😮', 'name': '惊喜'},
                    'neutral': {'bg': 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)', 'emoji': '😐', 'name': '中性'}
                }
                emotion_data = emotion_colors.get(result['emotion'], emotion_colors['neutral'])

                st.markdown(f"""
                <div class="emotion-result" style="background: {emotion_data['bg']}; color: white;">
                    <h4>{emotion_data['emoji']} {emotion_data['name']}</h4>
                    <p>置信度: {result['confidence']:.2%}</p>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("### 📊 情绪概率分布")

                max_emotion = max(result['probabilities'].keys(), key=lambda x: result['probabilities'][x])
                for emotion, prob in result['probabilities'].items():
                    emo_info = emotion_colors.get(emotion, {'name': emotion})
                    is_max = " ⭐" if emotion == max_emotion else ""
                    bar_color = emotion_colors.get(emotion, {'bg': 'linear-gradient(135deg, #6b7280 0%, #4b5563 100%)'})['bg']
                    st.markdown(f"""
                    <div style="margin-bottom: 0.75rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span class="prob-label">{emo_info['emoji']} {emo_info['name']}{is_max}</span>
                            <span class="prob-value">{prob:.2%}</span>
                        </div>
                        <div class="probability-bar">
                            <div class="probability-fill" style="background: {bar_color}; width: {prob * 100}%;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


def main():
    """主函数"""
    init_database()
    
    try:
        log_message("=" * 50)
        log_message("开始启动应用...")

        log_message("检查模型文件...")
        files_ok = check_model_files()

        if not files_ok:
            st.warning("⚠️ 部分模型文件不存在，相关功能可能不可用")

        init_session_state()

        # 页面顶部主标题
        col1, col2, col3 = st.columns([1, 4, 1])
        with col2:
            st.markdown("""
            <div class="main-header">
                <h1>🧠 ChainSenti 情链心智</h1>
                <p>多模态情绪识别系统 - 支持文本情感分析与图像情绪识别</p>
            </div>
            """, unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["💬 AI对话", "🖼️ 图像情绪识别", "🎨 角色管理"])

        with tab1:
            show_chat_page()

        with tab2:
            show_image_emotion_page()
        
        with tab3:
            show_role_management_page()

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 3])
        with btn_col1:
            with st.popover("🎯 功能说明", use_container_width=True):
                st.markdown("""
**💬 AI对话**: 基于DeepSeek大模型的智能对话系统
- 🎭 **角色扮演**: 4个预设角色（爱因斯坦、莎士比亚、智能客服、情感机器人）+ 自定义角色
- 😊 **情绪感知**: 情感机器人支持实时文本情绪分析（负面/中性/正面）
- 💾 **记忆功能**: 支持会话历史管理和上下文记忆
- 🎯 **个性化**: 可创建和管理自定义AI角色

---

**🖼️ 图像情绪识别**: 基于ResNet50的深度学习模型
- 🎯 **7种情绪类别**: 愤怒(angry)、厌恶(disgust)、恐惧(fear)、高兴(happy)、悲伤(sad)、惊讶(surprise)、中性(neutral)
- 🔬 **技术特点**:
  - 迁移学习（ImageNet预训练权重）
  - 早停机制防止过拟合
  - 混合精度训练加速
  - 7种数据增强策略
- 📊 **输出信息**:
  - 主要情绪预测及置信度
  - 各情绪类别概率分布
- 🖥️ **模型架构**: ResNet50骨干网络 + 自定义分类头

---

**🎨 角色管理**: 创建和管理自定义AI角色
- ✨ **创建角色**: 完整的角色创建表单
- 🎭 **上传头像**: 支持JPG、PNG、GIF格式
- 📋 **角色列表**: 查看和管理已创建的角色
- 🗑️ **删除角色**: 轻松删除不需要的角色
""")
        with btn_col2:
            with st.popover("📝 使用指南", use_container_width=True):
                st.markdown("""
**🚀 快速启动**:
直接运行: `streamlit run unified_app.py`

---

**💬 AI对话使用**:
1. 在左侧边栏选择一个角色
2. 点击「开始对话」按钮
3. 输入问题，与AI角色互动
4. 系统会自动分析你的情绪

---

**🖼️ 图像情绪识别使用**:
1. 切换到「图像情绪识别」标签页
2. 上传人脸图像（支持JPG/PNG）
3. 点击「分析情绪」按钮
4. 查看情绪预测结果和概率分布

---

**🎨 角色管理使用**:
1. 切换到「角色管理」标签页
2. 填写角色名称、描述、性格设定
3. 编写提示词模板
4. （可选）上传头像
5. 点击「创建角色」按钮
6. 创建后返回「AI对话」标签页使用新角色
""")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<p class="footer-text">🧠 ChainSenti 情链心智 - 多模态情绪识别系统</p>', unsafe_allow_html=True)
        st.markdown('<p class="footer-text" style="margin-top: 0.25rem;">💡 图像情绪识别: ResNet50 | 文本情感分析: BERT</p>', unsafe_allow_html=True)

        log_message("应用启动成功！")
        
    except Exception as e:
        error_msg = f"应用运行出错: {str(e)}\n{traceback.format_exc()}"
        log_error(error_msg)
        st.error(f"❌ {error_msg}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("应用被用户中断")
    except Exception as e:
        error_msg = f"严重错误: {str(e)}"
        log_error(error_msg)
        log_error(traceback.format_exc())
        input("\n按 Enter 键退出...")
