import streamlit as st
import arxiv
import datetime

# 页面配置
st.set_page_config(page_title="ArXiv 概率论前沿助手", page_icon="🎲", layout="wide")
st.title("🎲 ArXiv 概率论 (math.PR) 检索与最新动态")

# 核心：搜索 arXiv 并根据“最新更新时间 (Updated)”过滤
def fetch_papers(query, max_results, days_ago):
    if not query:
        return []
        
    client = arxiv.Client()
    # 关键修改 1：按最后更新时间 (LastUpdatedDate) 倒序排列，与官网同步
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.LastUpdatedDate, 
        sort_order=arxiv.SortOrder.Descending
    )
    
    target_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
    papers = []
    
    try:
        for result in client.results(search):
            # 关键修改 2：使用 updated (更新时间) 而不是 published (首发时间) 来判断
            if result.updated.replace(tzinfo=None) >= target_date:
                papers.append({
                    "title": result.title,
                    "authors": ", ".join([a.name for a in result.authors]),
                    # 界面上标记出这是最后的更新时间
                    "updated": result.updated.strftime("%Y-%m-%d (Updated)"),
                    "summary": result.summary,
                    "pdf_url": result.pdf_url
                })
            else:
                # 遇到超期的文章直接停止抓取，防止死循环
                break
    except Exception as e:
        st.error(f"arXiv 检索出错: {e}")
        return []
    return papers

# 构造精确检索语句
def build_search_query(keyword, author):
    query_parts = []
    if keyword:
        # 仅限题目和摘要
        query_parts.append(f"(ti:{keyword} OR abs:{keyword})")
    if author:
        query_parts.append(f"au:{author}")
    # 锁定在概率论方向
    query_parts.append("cat:math.PR")
    
    return " AND ".join(query_parts)


# --- 界面布局 ---
tab1, tab2 = st.tabs(["🔍 关键词/作者精准检索 (近10年)", "🆕 浏览最新概率论文章 (近2年)"])

# ==========================================
# 第一个 Tab：精准检索
# ==========================================
with tab1:
    st.header("🔍 精准检索模式")
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("🔍 关键词 (仅限题目和摘要):", placeholder="例如: SDEs, Wasserstein...")
    with col2:
        author = st.text_input("👤 作者 (Author):", placeholder="例如: Bao, Jianhai...")

    num_papers_search = st.slider("最大检索篇数 (最多100篇)", min_value=10, max_value=100, value=50, key="slider_search")

    if st.button("🚀 开始精准检索", type="primary"):
        if not keyword and not author:
            st.warning("⚠️ 关键词和作者至少需要填写一项！")
        else:
            search_query = build_search_query(keyword, author)
            
            with st.spinner("正在概率论 (math.PR) 分类下检索最近 10 年的论文..."):
                papers = fetch_papers(search_query, num_papers_search, days_ago=3650)
                
            if not papers:
                st.error("❌ 未找到最近十年内符合该条件的概率论文章。")
            else:
                st.success(f"✨ 成功筛选出 {len(papers)} 篇最近十年内的相关论文！")
                for p in papers:
                    st.markdown(f"### [{p['title']}]({p['pdf_url']})")
                    st.markdown(f"**作者**：{p['authors']} | **最后更新**：{p['updated']}")
                    st.write(p['summary'])
                    st.markdown("---")

# ==========================================
# 第二个 Tab：浏览最新文章 (与官网同步)
# ==========================================
with tab2:
    st.header("🆕 最新概率论领域动态")
    st.write("直接拉取 arXiv Probability (`cat:math.PR`) 的最新提交与版本更新 (Replacements)，与官网动态对齐。")
    
    num_papers_browse = st.number_input(
        "想要浏览的最新篇数 (无上限，请输入具体的数字)：", 
        min_value=1, 
        value=100, 
        step=50, 
        key="num_browse"
    )
    
    if st.button("🔄 获取最新文章", type="primary"):
        with st.spinner(f"正在拉取最新的 {num_papers_browse} 篇概率论论文，这可能需要几秒钟..."):
            browse_query = "cat:math.PR"
            papers = fetch_papers(browse_query, int(num_papers_browse), days_ago=730)
            
        if not papers:
            st.error("❌ 拉取失败或未找到文章。")
        else:
            st.success(f"✨ 成功拉取 {len(papers)} 篇最新概率论论文！")
            for p in papers:
                st.markdown(f"### [{p['title']}]({p['pdf_url']})")
                st.markdown(f"**作者**：{p['authors']} | **最后更新**：{p['updated']}")
                st.write(p['summary'])
                st.markdown("---")
