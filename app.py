import streamlit as st
import arxiv
import datetime

# 1. 页面基本配置
st.set_page_config(
    page_title="ArXiv Probability Station", 
    page_icon="🔬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 注入自定义 CSS 样式（核心修改区）
st.markdown("""
    <style>
    /* 强制缩小左侧边栏的宽度 */
    [data-testid="stSidebar"] {
        min-width: 260px !important;
        max-width: 260px !important;
    }
    
    /* 压缩卡片间距和内边距，让一屏能显示更多篇数 */
    .paper-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 12px 15px;
        margin-bottom: 12px;
        border-left: 4px solid #003366;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
    }
    
    /* 稍微调小标题字号并紧凑行高 */
    .paper-title {
        color: #003366;
        font-size: 18px !important;
        font-weight: bold !important;
        text-decoration: none;
        line-height: 1.2;
        display: block;
    }
    .paper-title:hover {
        color: #0056b3;
        text-decoration: underline;
    }
    
    /* 紧凑元数据信息 */
    .metadata {
        color: #666;
        font-size: 13px;
        margin-top: 6px;
        margin-bottom: 6px;
    }
    
    /* 压缩摘要的字号和行距，减少大片留白 */
    .abstract-text {
        font-size: 13px;
        line-height: 1.4;
        color: #333;
        background: #ffffff;
        padding: 8px 10px;
        border-radius: 4px;
        margin-top: 4px;
    }
    
    /* 缩小标签尺寸 */
    .badge {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 10px;
        background-color: #e9ecef;
        color: #495057;
        font-size: 11px;
