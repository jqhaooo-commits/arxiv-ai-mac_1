import streamlit as st
import arxiv
import datetime

# 页面配置
st.set_page_config(page_title="ArXiv 概率论前沿助手", page_icon="🎲", layout="wide")
st.title("🎲 ArXiv 概率论 (math.PR) 检索与最新动态")

# --- 核心拉取逻辑重构 ---
def fetch_papers_with_strict_filter(query, target_count, days_ago):
    client = arxiv.Client()
    search = arxiv.Search(
        query=query, 
        max_results=target_count * 5, # 扩大搜索池，本地过滤
        # 👑 关键修正 1：改回按“首次提交时间”排序，拒绝把老文章的修改版顶上来
        sort_by=arxiv.SortCriterion.SubmittedDate, 
        sort_order=arxiv.SortOrder.Descending
    )
    
    target_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
    papers = []
    
    try:
        for result in client.results(search):
            # 👑 关键修正 2：用 published (首发时间) 作为时间卡尺，对齐官网的 Recent submissions
            if result.published.replace(tzinfo=None) < target_date:
                break
                
            if len(papers) >= target_count:
                break

            # 严格检查该文章的分类列表是否包含 math.PR
            if "math.PR" in result.categories:
                papers.append({
                    "title": result.title,
                    "authors": ", ".join([a.name for a in result.authors]),
                    # 👑 关键修正 3：界面显示首发时间
                    "published": result.published.strftime("%Y-%m-%d"),
                    "summary": result.summary,
                    "pdf_url": result.pdf_url
                })
    except Exception as e:
        st.error(f"arXiv 检索出错: {e}")
        return []
    return papers

# 构造精确检索语句
def build_search_query(keyword, author):
    query_parts = []
    if keyword:
        query_parts.append(f"(ti:{keyword} OR abs:{keyword})")
    if author:
        query_parts.append(f"au:{author}")
    query_parts.append("cat:math.PR") 
    return " AND ".join(query_parts)


# --- 界面布局 ---
tab1, tab2 = st.tabs(["🔍 关键词/作者精准检索 (近10年)", "🆕 浏览最新概率论文章 (近2年)"])

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
            
            with st.spinner("正在检索最近 10 年的相关概率论论文..."):
                papers = fetch_papers_with_strict_filter(search_query, num_papers_search, days_ago=3650)
                
            if not papers:
                st.error("❌ 未找到最近十年内符合该条件的概率论文章。")
            else:
                st.success(f"✨ 成功筛选出 {len(papers)} 篇相关论文！")
                for p in papers:
                    st.markdown(f"### [{p['title']}]({p['pdf_url']})")
                    st.markdown(f"**作者**：{p['authors']} | **发表日期**：{p['published']}")
                    st.write(p['summary'])
                    st.markdown("---")

with tab2:
    st.header("🆕 最新概率论领域动态")
    st.write("获取包含 `math.PR` 标签的最新全新提交 (New Submissions)，拒绝老文章的修改版霸榜。")
    
    num_papers_browse = st.number_input(
        "想要浏览的最新篇数 (无上限，请输入具体的数字)：", 
        min_value=1, 
        value=100, 
        step=50, 
        key="num_browse"
    )
    
    if st.button("🔄 获取最新文章", type="primary"):
        with st.spinner(f"正在深度抓取并过滤最新的 {num_papers_browse} 篇概率论新提交论文..."):
            browse_query = "cat:math.*" 
            papers = fetch_papers_with_strict_filter(browse_query, int(num_papers_browse), days_ago=730)
            
        if not papers:
            st.error("❌ 拉取失败或未找到文章。")
        else:
            st.success(f"✨ 成功拉取 {len(papers)} 篇最新概率论论文！")
            for p in papers:
                st.markdown(f"### [{p['title']}]({p['pdf_url']})")
                st.markdown(f"**作者**：{p['authors']} | **发表日期**：{p['published']}")
                st.write(p['summary'])
                st.markdown("---")
