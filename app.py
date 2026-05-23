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

# 2. 注入自定义 CSS 样式（纯正 arXiv 官网极简风）
st.markdown("""
    <style>
    /* 侧边栏宽度 */
    [data-testid="stSidebar"] {
        min-width: 200px !important;
        max-width: 200px !important;
    }
    [data-testid="stSidebar"] * {
        font-size: 14px;
    }
    
    /* 官网风：去卡片化，纯白背景，紧凑外边距 */
    .paper-container {
        padding: 5px 0px 15px 0px; 
        margin-bottom: 5px;
        border-bottom: none;
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; /* 接近官网字体 */
    }
    
    /* [1] arXiv:xxxx.xxxx [pdf] 这一行的样式 */
    .arxiv-id-line {
        font-size: 13.5px;
        font-weight: bold;
        color: #000;
        margin-bottom: 3px;
    }
    .arxiv-link {
        color: #0000ee;
        text-decoration: none;
    }
    .arxiv-link:hover {
        text-decoration: underline;
    }
    
    /* 纯黑加粗大标题 */
    .paper-title {
        color: #000000 !important;
        font-size: 18px !important; 
        font-weight: bold !important;
        text-decoration: none;
        line-height: 1.2;
        display: block;
        margin-bottom: 3px;
    }
    
    /* 经典蓝色作者列表 */
    .authors {
        color: #0000ee;
        font-size: 15px;
        margin-bottom: 2px;
    }
    
    /* 极简分类与版本信息 */
    .metadata-text {
        color: #000;
        font-size: 13.5px;
        margin-top: 1px;
    }

    /* === 极简版折叠摘要 === */
    .abstract-details {
        margin-top: 4px;
    }
    
    .abstract-summary {
        cursor: pointer;
        color: #0000ee; /* 官网链接蓝 */
        font-size: 13.5px; 
        outline: none;
        user-select: none;
    }
    .abstract-summary:hover {
        text-decoration: underline;
    }
    
    /* 摘要正文，模仿官网的块级缩进 */
    .abstract-text {
        font-size: 14.5px; 
        line-height: 1.5;
        color: #000;
        padding: 0 10px 0 15px; /* 左侧缩进 */
        margin-top: 8px;
        border-left: 2px solid #ddd; /* 极轻微的左侧灰线，帮助视线对齐 */
    }
    
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
                # 提取文章的纯数字 ID，例如 2605.22803
                arxiv_id = result.pdf_url.split('/')[-1].replace('v', ' v')
                
                papers.append({
                    "title": result.title,
                    "authors": ", ".join([a.name for a in result.authors]),
                    "date": result.updated.strftime("%Y-%m-%d") if mode == "browse" else result.published.strftime("%Y-%m-%d"),
                    "summary": result.summary,
                    "url": result.pdf_url,
                    "primary": result.primary_category,
                    "id": arxiv_id
                })
    except Exception as e:
        st.error(f"Error: {e}")
    return papers

# --- 侧边栏：控制中心 ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/b/bc/ArXiv_logo_2022.svg", width=100)
    st.markdown("### 控制中心")
    st.markdown("---")
    
    mode = st.radio("选择工作模式：", ["🆕 每日动态浏览", "🔍 精确文献检索"])
    
    if mode == "🔍 精确文献检索":
        keyword = st.text_input("关键词", placeholder="输入关键词...")
        author = st.text_input("作者", placeholder="输入作者名...")
        limit = st.number_input("检索上限", min_value=10, value=100, step=50)
    else:
        limit = st.number_input("浏览篇数上限", min_value=10, value=100, step=50)
    
    st.markdown("---")
    run_button = st.button("🚀 执行任务", use_container_width=True, type="primary")
    
    st.caption("注：数据同步可能比官网延迟 12h。")

# --- 渲染卡片的复用函数 (完全重构为官网排版) ---
def render_paper_card(p, index):
    st.markdown(f"""
        <div class="paper-container">
            <div class="arxiv-id-line">
                [{index}] <a href="{p['url']}" class="arxiv-link" target="_blank">arXiv:{p['id']}</a> 
                [<a href="{p['url']}" class="arxiv-link" target="_blank">pdf</a>]
            </div>
            <div class="paper-title">{p['title']}</div>
            <div class="authors">{p['authors']}</div>
            <div class="metadata-text"><b>Subjects:</b> {p['primary']} &nbsp;|&nbsp; <b>Date:</b> {p['date']}</div>
            
            <details class="abstract-details">
                <summary class="abstract-summary">▶ Show Abstract</summary>
                <div class="abstract-text">
                    {p['summary']}
                </div>
            </details>
        </div>
    """, unsafe_allow_html=True)


# --- 主界面内容 ---
st.title("Probability (math.PR) Recent Updates")

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
        # 为了模仿官网的 [1], [2] 序号，加入 index
        for index, p in enumerate(results, start=1):
            render_paper_card(p, index)
    else:
        st.error("未找到符合条件的文章。")
