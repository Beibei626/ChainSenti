# 🧠 ChainSenti 情链心智

> 多模态情绪识别智能对话系统

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=Python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## ✨ 功能特性

- 💬 **AI对话** - 与预设角色进行智能对话
- 😊 **情绪感知** - 实时分析文本情绪
- 🖼️ **图像情绪识别** - 识别图片中的人物情绪
- 🎭 **自定义角色** - 创建和管理自己的AI角色
- 🔧 **无需后端** - 独立前端，直接部署

## 🚀 快速开始

### 本地运行

```bash
# 1. 克隆仓库
git clone https://github.com/你的用户名/chainsenti.git
cd chainsenti

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行应用
streamlit run unified_app.py
```

### 云端部署

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_github.svg)](https://share.streamlit.io)

1. 点击上方按钮或访问 [share.streamlit.io](https://share.streamlit.io)
2. 连接 GitHub 仓库
3. 选择 `unified_app.py` 作为主文件
4. 点击 Deploy!

## 📁 项目结构

```
Git data/
├── unified_app.py          # 主应用
├── requirements.txt        # 依赖
├── .streamlit/
│   └── config.toml        # 配置
└── README.md              # 说明文档
```

## 🎯 功能说明

### 💬 AI对话

选择预设角色或自定义角色进行对话：
- 阿尔伯特·爱因斯坦
- 威廉·莎士比亚
- 智能客服
- 情感机器人

### 😊 情绪分析

系统会自动分析您的输入文本，识别情绪：
- 😊 正面情绪
- 😐 中性情绪
- 😔 负面情绪

### 🖼️ 图像情绪识别

上传图片，系统将识别其中人物的7种情绪：
- Happy（开心）
- Sad（悲伤）
- Angry（愤怒）
- Fear（恐惧）
- Surprise（惊讶）
- Disgust（厌恶）
- Neutral（中性）

### 🎨 自定义角色

创建完全自定义的AI对话角色：
- 自定义角色名称和描述
- 设置性格特征
- 编写提示词模板
- 上传角色头像
- 数据保存在本地 SQLite 数据库

## 🔧 技术栈

- **前端框架**: Streamlit
- **数据库**: SQLite
- **情绪分析**: 基于词典的情感分析
- **部署**: Streamlit Cloud

## 📝 使用说明

### 创建自定义角色

1. 点击 **🎨 角色管理** 标签页
2. 填写角色信息：
   - 角色名称（必填）
   - 角色描述
   - 性格特征
   - 提示词模板（必填）
3. （可选）上传角色头像
4. 点击 **创建角色**
5. 在 **💬 AI对话** 页面选择新角色开始对话

### 对话示例

```
用户: 今天天气真好！
系统: 😊 正面情绪 - 听起来你很开心呢！有什么好事发生了吗？

用户: 这个任务太难了
系统: 😔 负面情绪 - 别担心，一切都会好起来的。
```

## ⚠️ 注意事项

- 本版本为**独立前端版本**，不包含后端 LLM 调用
- AI 对话使用简化版情绪感知回复
- 完整的 LLM 对话功能需要配置 DeepSeek API
- 图像情绪识别在云端可能需要较长加载时间

## 📄 License

MIT License

## 🤝 Contributing

欢迎提交 Issue 和 Pull Request！

## 📧 Contact

如有问题，请提交 GitHub Issue。
