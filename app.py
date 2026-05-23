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

# 2. 注入自定义 CSS 样式（新增了折叠面板的美化）
st.markdown("""
    <style>
    /* 强制缩小左侧边栏的宽度 */
    [data-testid="stSidebar"] {
        min-width: 200px !important;
        max-width: 200px !important;
    }
    
    /* 卡片基础样式 */
    .paper-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px 18px;
        margin-bottom: 15px;
        border-left: 4px solid #003366;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.05);
    }
    
    /* 论文标题 */
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
    
    /* 元数据信息 */
    .metadata {
        color: #666;
        font-size: 13px;
        margin-top: 6px;
        margin-bottom: 6px;
    }
    
    /* 缩小标签尺寸 */
    .badge {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 10px;
        background-color: #e9ecef;
        color: #495057;
        font-size: 11px;
        margin-right: 4px;
    }

    /* === 新增：折叠面板样式 === */
    .abstract-details {
        margin-top: 8px;
    }
    
    /* 折叠按钮外观 */
    .abstract-summary {
        cursor: pointer;
        color: #0056b3;
        font-size: 13px;
        font-weight: 600;
        outline: none;
        user-select: none;
        transition: color 0.2s;
    }
    .abstract-summary:hover {
        color: #ff6600; /* 悬停时变成亮色提示可点击 */
    }
    
    /* 展开后的摘要文本内容 */
    .abstract-text {
        font-size: 13.5px;
        line-height: 1.5;
        color: #333;
        background: #ffffff;
        padding: 10px 12px;
        border-radius: 6px;
        margin-top: 8px;
        border: 1px dashed #ccc; /* 虚线边框区分层级 */
    }
    
    /* 缩小顶部标题占用空间 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 核心抓取引擎 ---
def fetch_arxiv_data(query, target_count, days_ago, mode="search"):
    client = arxiv.Client()
    sort_by = arxiv.SortCriterion.SubmittedDate if mode == "search" else arxiv.SortCriterion.LastUpdatedDate
    
    search = arxiv.Search(
        query=query,
        max_results=int(target_count),
        sort_by=sort_by,
        sort_order=arxiv.SortOrder.Descending
    )
    
    target_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
    papers = []
    
    try:
        for result in client.results(search):
            if mode == "search":
                if result.published.replace(tzinfo=None) < target_date: break
            else:
                if result.updated.replace(tzinfo=None) < target_date: break
            
            if "math.PR" in result.categories:
                papers.append({
                    "title": result.title,
                    "authors": ", ".join([a.name for a in result.authors]),
                    "date": result.updated.strftime("%Y-%m-%d") if mode == "browse" else result.published.strftime("%Y-%m-%d"),
                    "summary": result.summary,
                    "url": result.pdf_url,
                    "primary": result.primary_category,
                    "version": f"v{result.pdf_url.split('v')[-1]}" if 'v' in result.pdf_url else ""
                })
    except Exception as e:
        st.error(f"Error: {e}")
    return papers

# --- 侧边栏：控制中心 ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/bc/ArXiv_logo_2022.svg", width=120)
    st.markdown("### 控制中心")
    st.markdown("---")
    
    mode = st.radio("选择工作模式：", ["🆕 每日动态浏览", "🔍 精确文献检索"])
    
    if mode == "🔍 精确文献检索":
        keyword = st.text_input("关键词 (题目/摘要)", placeholder="输入关键词...")
        author = st.text_input("作者姓名", placeholder="输入作者名...")
        limit = st.number_input("检索上限 (近10年)", min_value=10, value=100, step=50)
    else:
        limit = st.number_input("浏览篇数上限 (近2年)", min_value=10, value=100, step=50)
    
    st.markdown("---")
    run_button = st.button("🚀 执行任务", use_container_width=True, type="primary")
    
    st.caption("注：数据同步可能比官网延迟 12h。")

# --- 渲染卡片的复用函数 ---
def render_paper_card(p):
    st.markdown(f"""
        <div class="paper-card">
            <a class="paper-title" href="{p['url']}" target="_blank">{p['title']}</a>
            <div class="metadata">
                <span class="badge">👤 {p['authors']}</span>
                <span class="badge">📅 {p['date']}</span>
                <span class="badge">🏷️ {p['primary']}</span>
                <span class="badge">🔢 {p['version']}</span>
            </div>
            <details class="abstract-details">
                <summary class="abstract-summary">▶ 点击展开阅读摘要 (Abstract)</summary>
                <div class="abstract-text">
                    {p['summary']}
                </div>
            </details>
        </div>
    """, unsafe_allow_html=True)


# --- 主界面内容 ---
st.title("🔬 ArXiv Probability Scholar")

if not run_button:
    st.info("👈 请在左侧配置参数并点击【执行任务】开始检索。")
else:
    if mode == "🔍 精确文献检索":
        if not keyword and not author:
            st.warning("请至少输入一个关键词或作者姓名")
        else:
            q = f"(ti:{keyword} OR abs:{keyword}) AND cat:math.PR" if keyword else f"au:{author} AND cat:math.PR"
            if keyword and author: q = f"(ti:{keyword} OR abs:{keyword}) AND au:{author} AND cat:math.PR"
            
            with st.spinner("正在检索精准文献..."):
                results = fetch_arxiv_data(q, limit, 3650, "search")
    else:
        with st.spinner("正在同步官网最新动态..."):
            results = fetch_arxiv_data("cat:math.PR", limit, 730, "browse")

    if results:
        st.success(f"找到 {len(results)} 篇相关论文")
        # 遍历文章并调用卡片渲染函数
        for p in results:
            render_paper_card(p)
    else:
        st.error("未找到符合条件的文章。")
