"""
ChainSenti 情链心智 - 独立前端版本
无需后端，可直接部署到 Streamlit Cloud
"""

import streamlit as st
import os
import sys
import sqlite3
import base64
from datetime import datetime
from PIL import Image
import io
import time

st.set_page_config(
    page_title="🧠 ChainSenti情链心智",
    page_icon="🎭",
    layout="wide"
)

DB_PATH = os.path.join(os.path.dirname(__file__), "roles.db")

os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
import warnings
warnings.filterwarnings("ignore")
os.environ['TRANSFORMERS_NO_ADVISORY_WARNINGS'] = 'true'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'

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

    footer { visibility: hidden; }
    
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

    .main-header {
        text-align: center;
        padding: 1.5rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
    }

    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }

    .main-header p {
        font-size: 1.1rem;
        opacity: 0.95;
        margin: 0.5rem 0 0 0;
    }

    .emotion-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }

    .emotion-positive { background: #d4edda; color: #155724; }
    .emotion-neutral { background: #fff3cd; color: #856404; }
    .emotion-negative { background: #f8d7da; color: #721c24; }

    .chat-message {
        padding: 1rem 1.5rem;
        border-radius: 16px;
        margin: 0.5rem 0;
        max-width: 85%;
        animation: fadeIn 0.3s ease-in;
    }

    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }

    .assistant-message {
        background: white;
        border: 1px solid #e5e7eb;
        margin-right: auto;
        border-bottom-left-radius: 4px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .role-card {
        background: white;
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #e5e7eb;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }

    .role-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }

    .role-avatar {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        object-fit: cover;
        border: 3px solid #667eea;
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
""", unsafe_allow_html=True)

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

def analyze_text_emotion(text):
    """简化版文本情绪分析"""
    positive_words = ['好', '喜欢', '开心', '高兴', '棒', '赞', '优秀', '完美', '爱', '美', '棒', '谢谢', '感谢', 'happy', 'good', 'great', 'love', 'nice']
    negative_words = ['差', '坏', '讨厌', '不喜欢', '难过', '伤心', '糟', '失望', '糟糕', 'no', 'bad', 'hate', 'sad', 'angry']
    
    text_lower = text.lower()
    pos_count = sum(1 for word in positive_words if word in text_lower)
    neg_count = sum(1 for word in negative_words if word in text_lower)
    
    if pos_count > neg_count:
        return "positive", 0.7
    elif neg_count > pos_count:
        return "negative", 0.7
    else:
        return "neutral", 0.5

def simple_chat_response(message, role_name, prompt_template):
    """生成简单的对话回复（无后端版本）"""
    emotion, confidence = analyze_text_emotion(message)
    
    emotion_emoji = {"positive": "😊", "neutral": "😐", "negative": "😔"}[emotion]
    
    responses = {
        "positive": [
            f"太棒了！{emotion_emoji} 我能感受到你的好心情！",
            f"听起来你很开心呢！{emotion_emoji} 有什么好事发生了吗？",
        ],
        "negative": [
            f"我理解你的感受。{emotion_emoji} 愿意和我聊聊吗？",
            f"别担心，一切都会好起来的。{emotion_emoji}",
        ],
        "neutral": [
            f"好的，我明白了。有什么我可以帮助你的吗？",
            f"收到！请告诉我更多信息。",
        ]
    }
    
    import random
    response = random.choice(responses[emotion])
    
    if role_name and prompt_template:
        response = f"[{role_name}] {response}"
    
    return response, emotion, confidence

def show_chat_page():
    """显示对话页面"""
    st.markdown('<div class="tab-chat">', unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 🎭 角色选择")
        
        PRESET_ROLES = [
            {
                "id": "einstein",
                "name": "阿尔伯特·爱因斯坦",
                "description": "20世纪最伟大的物理学家",
                "avatar": "einstein.jpg",
                "prompt_template": "你是阿尔伯特·爱因斯坦，20世纪最伟大的物理学家之一。请用他的风格回答问题，保持睿智、简洁而富有洞察力。"
            },
            {
                "id": "shakespeare",
                "name": "威廉·莎士比亚",
                "description": "英国文学史上最伟大的剧作家和诗人",
                "avatar": "shakespeare.jpg",
                "prompt_template": "你是威廉·莎士比亚，用你的诗歌和戏剧风格来回答问题，让语言充满诗意和戏剧性。"
            },
            {
                "id": "customer_service",
                "name": "智能客服",
                "description": "专业、友好的客户服务代表",
                "avatar": "customer_service.jpg",
                "prompt_template": "你是一个专业、友好的智能客服。请耐心解答用户的问题，保持热情和专业的服务态度。"
            },
            {
                "id": "emotion_bot",
                "name": "情感机器人",
                "description": "善解人意的情感陪伴助手",
                "avatar": "emotion_bot.png",
                "prompt_template": "你是情感陪伴助手，善于倾听和理解用户的情感需求。请以温暖、善解人意的方式回应。"
            }
        ]
        
        custom_roles = get_custom_roles()
        
        role_options = ["➕ 创建自定义角色"]
        role_map = {}
        
        for role in custom_roles:
            role_options.append(f"✨ {role['name']}")
            role_map[f"✨ {role['name']}"] = role
        
        selected_role = st.selectbox(
            "选择对话角色：",
            ["➕ 创建自定义角色"] + role_options[1:] if role_options[1:] else ["➕ 创建自定义角色"],
            key="role_selector"
        )
        
        if selected_role != "➕ 创建自定义角色":
            if f"✨ {selected_role.replace('✨ ', '')}" in role_map:
                role = role_map[selected_role]
            else:
                role = None
            
            if role:
                st.session_state.current_role = role
                st.session_state.current_role_type = "custom"
            else:
                role_data = next((r for r in PRESET_ROLES if r["id"] == selected_role), PRESET_ROLES[0])
                st.session_state.current_role = role_data
                st.session_state.current_role_type = "preset"
        else:
            st.info("💡 请先在【角色管理】标签页创建自定义角色")
            st.session_state.current_role = PRESET_ROLES[0]
            st.session_state.current_role_type = "preset"
        
        current_role = st.session_state.get("current_role", PRESET_ROLES[0])
        
        if current_role:
            st.markdown("---")
            st.markdown(f"**当前角色：{current_role['name']}**")
            if current_role.get('description'):
                st.caption(current_role['description'])

    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    st.markdown('<h1>🧠 ChainSenti 情链心智</h1>', unsafe_allow_html=True)
    st.markdown('<p>多模态情绪识别智能对话系统</p>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("emotion"):
                st.markdown(f'<span class="emotion-badge emotion-{message["emotion"]}">{message["emotion_emoji"]} {message["emotion_label"]}</span>', unsafe_allow_html=True)
            st.markdown(message["content"])

    if prompt := st.chat_input("输入消息...", key="chat_input"):
        with st.chat_message("user"):
            st.markdown(prompt)
        
        emotion, confidence = analyze_text_emotion(prompt)
        emotion_emoji = {"positive": "😊", "neutral": "😐", "negative": "😔"}[emotion]
        emotion_label = {"positive": "正面", "neutral": "中性", "negative": "负面"}[emotion]
        
        current_role = st.session_state.get("current_role", {"name": "助手", "prompt_template": ""})
        
        response, _, _ = simple_chat_response(prompt, current_role.get("name", ""), current_role.get("prompt_template", ""))
        
        with st.chat_message("assistant"):
            st.markdown(f'<span class="emotion-badge emotion-{emotion}">{emotion_emoji} {emotion_label}</span>', unsafe_allow_html=True)
            st.markdown(response)
        
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "emotion": emotion,
            "emotion_emoji": emotion_emoji,
            "emotion_label": emotion_label
        })
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append({"role": "assistant", "content": response})
    
    st.markdown('</div>', unsafe_allow_html=True)

def uploaded_file_to_preview(uploaded_file):
    """将上传的文件转换为预览"""
    if uploaded_file is not None:
        return Image.open(uploaded_file)
    return None

def main():
    """主函数"""
    init_database()
    
    tab1, tab2, tab3 = st.tabs(["💬 AI对话", "🖼️ 图像情绪识别", "🎨 角色管理"])
    
    with tab1:
        show_chat_page()
    
    with tab2:
        st.markdown("## 🖼️ 图像情绪识别")
        st.markdown("---")
        
        uploaded_file = st.file_uploader(
            "上传图片",
            type=['jpg', 'jpeg', 'png', 'gif'],
            help="支持 JPG、PNG、GIF 格式"
        )
        
        if uploaded_file is not None:
            image = uploaded_file_to_preview(uploaded_file)
            if image:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.image(image, caption="上传的图片", use_container_width=True)
                
                with col2:
                    st.markdown("### 📊 情绪分析结果")
                    st.markdown("**7种情绪分类：**")
                    st.markdown("😊 **Happy** - 开心")
                    st.markdown("😢 **Sad** - 悲伤")
                    st.markdown("😠 **Angry** - 愤怒")
                    st.markdown("😨 **Fear** - 恐惧")
                    st.markdown("😮 **Surprise** - 惊讶")
                    st.markdown("� disgust **Disgust** - 厌恶")
                    st.markdown("😐 **Neutral** - 中性")
                    
                    st.info("💡 图像情绪识别功能需要加载预训练模型。在 Streamlit Cloud 上可能需要较长的加载时间。")
        
        st.markdown("---")
        st.markdown("**功能说明：**")
        st.markdown("- 支持识别7种基本情绪：开心、悲伤、愤怒、恐惧、惊讶、厌恶、中性")
        st.markdown("- 基于深度学习模型（ResNet50）进行迁移学习")
        st.markdown("- 适合人脸图片的情绪分析")
    
    with tab3:
        show_role_management_page()

if __name__ == "__main__":
    main()
