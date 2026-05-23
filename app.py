import streamlit as st
import arxiv

# 页面配置
st.set_page_config(page_title="ArXiv 概率论前沿助手", page_icon="🎲", layout="wide")
st.title("🎲 ArXiv 概率论 (math.PR) 每日更新同步版")

# --- 核心逻辑：直接拉取最新批次，不自己算时间 ---
def fetch_latest_papers(query, max_results):
    client = arxiv.Client()
    # 核心：直接按提交时间倒序排，不加任何时间过滤卡尺，原汁原味还原官网批次
    search = arxiv.Search(
        query=query, 
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate, 
        sort_order=arxiv.SortOrder.Descending
    )
    
    papers = []
    try:
        for result in client.results(search):
            papers.append({
                "title": result.title,
                "authors": ", ".join([a.name for a in result.authors]),
                "published": result.published.strftime("%Y-%m-%d"),
                "summary": result.summary,
                "pdf_url": result.pdf_url
            })
    except Exception as e:
        st.error(f"arXiv 检索出错: {e}")
        return []
    return papers

# --- 界面布局 ---
tab1, tab2 = st.tabs(["🆕 每日最新更新 (对齐官网)", "🔍 关键词/作者精准检索"])

# ==========================================
# 第一个 Tab：浏览最新文章 (与官网绝对同步)
# ==========================================
with tab1:
    st.header("🆕 每日最新更新 (Recent Submissions)")
    st.write("直接拉取 arXiv 官方按最新提交顺序返回的数据，不进行人工时间干预，彻底对齐官网每日发榜。")
    
    num_papers_browse = st.number_input(
        "想要浏览的最新篇数 (建议 50-200)：", 
        min_value=1, 
        value=50, 
        step=50, 
        key="num_browse"
    )
    
    if st.button("🔄 获取今日更新", type="primary"):
        with st.spinner(f"正在拉取最新的 {num_papers_browse} 篇概率论新提交论文..."):
            # 简单粗暴：只要带有 math.PR 标签的最新文章
            browse_query = "cat:math.PR" 
            papers = fetch_latest_papers(browse_query, int(num_papers_browse))
            
        if not papers:
            st.error("❌ 拉取失败或未找到文章。")
        else:
            st.success(f"✨ 成功拉取 {len(papers)} 篇最新概率论论文！")
            for p in papers:
                st.markdown(f"### [{p['title']}]({p['pdf_url']})")
                st.markdown(f"**作者**：{p['authors']} | **首发日期**：{p['published']}")
                st.write(p['summary'])
                st.markdown("---")

# ==========================================
# 第二个 Tab：精准检索
# ==========================================
with tab2:
    st.header("🔍 精准检索模式")
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("🔍 关键词 (仅限题目和摘要):", placeholder="例如: SDEs...")
    with col2:
        author = st.text_input("👤 作者 (Author):", placeholder="例如: Bao, Jianhai...")

    num_papers_search = st.slider("最大检索篇数 (最多200篇)", min_value=10, max_value=200, value=50, key="slider_search")

    if st.button("🚀 开始精准检索", type="primary"):
        if not keyword and not author:
            st.warning("⚠️ 关键词和作者至少需要填写一项！")
        else:
            query_parts = []
            if keyword:
                query_parts.append(f"(ti:{keyword} OR abs:{keyword})")
            if author:
                query_parts.append(f"au:{author}")
            query_parts.append("cat:math.PR") 
            search_query = " AND ".join(query_parts)
            
            with st.spinner("正在检索相关概率论论文..."):
                papers = fetch_latest_papers(search_query, num_papers_search)
                
            if not papers:
                st.error("❌ 未找到符合条件的概率论文章。")
            else:
                st.success(f"✨ 成功筛选出 {len(papers)} 篇相关论文！")
                for p in papers:
                    st.markdown(f"### [{p['title']}]({p['pdf_url']})")
                    st.markdown(f"**作者**：{p['authors']} | **首发日期**：{p['published']}")
                    st.write(p['summary'])
                    st.markdown("---")
