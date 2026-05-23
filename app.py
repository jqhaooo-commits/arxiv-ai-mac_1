import streamlit as st
import arxiv
import datetime

# 页面配置
st.set_page_config(page_title="ArXiv 概率论学术助手", page_icon="🎲", layout="wide")
st.title("🎲 ArXiv 概率论 (math.PR) 精准科研雷达")

# --- 核心数据抓取引擎 ---
def fetch_arxiv_data(query, target_count, days_ago, mode="search"):
    client = arxiv.Client()
    
    # 根据模式选择排序依据
    if mode == "search":
        # 第一栏：精准检索，按首次提交时间倒序
        sort_by = arxiv.SortCriterion.SubmittedDate
    else:
        # 第二栏：动态浏览，按最后更新时间（包含Replacements）倒序，完全对齐官网
        sort_by = arxiv.SortCriterion.LastUpdatedDate

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
            # 时间截止判断
            if mode == "search":
                if result.published.replace(tzinfo=None) < target_date:
                    break
            else:
                if result.updated.replace(tzinfo=None) < target_date:
                    break
            
            # 严格复核分类，确保属于概率论方向
            if "math.PR" in result.categories:
                papers.append({
                    "title": result.title,
                    "authors": ", ".join([a.name for a in result.authors]),
                    "published": result.published.strftime("%Y-%m-%d"),
                    "updated": result.updated.strftime("%Y-%m-%d"),
                    "summary": result.summary,
                    "pdf_url": result.pdf_url,
                    "primary_cat": result.primary_category
                })
    except Exception as e:
        if "429" in str(e):
            st.error("⚠️ 触发了 arXiv 官方接口限流保护（HTTP 429）。请静置网页 3-5 分钟后再试。")
        else:
            st.error(f"检索出错: {e}")
        return papers
        
    return papers

# --- 界面布局 ---
tab1, tab2 = st.tabs(["🔍 题目/摘要精准检索 (近10年)", "🆕 官网同步动态浏览 (近2年)"])

# ==========================================
# 第一栏：精准检索模式 (近10年，无上限)
# ==========================================
with tab1:
    st.header("🔍 概率论文献精准检索")
    st.caption("限定 math.PR 领域。关键词仅在【题目】和【摘要】中进行匹配。")
    
    col1, col2 = st.columns(2)
    with col1:
        keyword = st.text_input("🔍 检索关键词 (题目或摘要):", placeholder="例如: McKean-Vlasov, SDEs...")
    with col2:
        author = st.text_input("👤 作者姓名 (Author):", placeholder="例如: Bao, Jianhai...")
        
    # 无上限数字输入框
    num_search = st.number_input(
        "预计检索最大篇数 (无上限，可自由输入):", 
        min_value=1, 
        value=100, 
        step=50, 
        key="input_search"
    )
    
    if st.button("🚀 开始近十年检索", type="primary"):
        if not keyword and not author:
            st.warning("⚠️ 请至少输入一个关键词或作者姓名！")
        else:
            # 构造检索语句：限定题目、摘要以及概率论分类
            query_parts = []
            if keyword:
                query_parts.append(f"(ti:{keyword} OR abs:{keyword})")
            if author:
                query_parts.append(f"au:{author}")
            query_parts.append("cat:math.PR")
            search_query = " AND ".join(query_parts)
            
            with st.spinner("正在检索过去 10 年内的概率论文献..."):
                # 10年约 3650 天
                papers = fetch_arxiv_data(search_query, num_search, days_ago=3650, mode="search")
                
            if not papers:
                st.info("💡 未找到符合条件的文献。")
            else:
                st.success(f"✨ 成功筛选出 {len(papers)} 篇近十年内的相关概率论论文！")
                for p in papers:
                    st.markdown(f"### [{p['title']}]({p['pdf_url']})")
                    st.markdown(f"**作者**：{p['authors']} | **首发日期**：{p['published']}")
                    st.write(p['summary'])
                    st.markdown("---")

# ==========================================
# 第二栏：最新动态浏览 (近2年更新，无上限)
# ==========================================
with tab2:
    st.header("🆕 概率论最新更新动态")
   st.caption("同步 arXiv 官网更新序列。注：受 arXiv 官方发榜时差影响，此处显示的为作者**真实提交/更新日**，通常比官网批次名称早 1-2 天。")
    
    # 无上限数字输入框
    num_browse = st.number_input(
        "想要纵览的更新篇数 (无上限，可自由输入):", 
        min_value=1, 
        value=100, 
        step=50, 
        key="input_browse"
    )
    
    if st.button("🔄 刷新获取最新动态", type="primary"):
        with st.spinner("正在同步官网近 2 年的更新日志..."):
            # 锁定概率论分类
            browse_query = "cat:math.PR"
            # 2年约 730 天
            papers = fetch_arxiv_data(browse_query, num_browse, days_ago=730, mode="browse")
            
        if not papers:
            st.info("💡 暂无更新或接口处于保护期。")
        else:
            st.success(f"✨ 成功同步 {len(papers)} 篇近两年内的更新成果！")
            for p in papers:
                st.markdown(f"### [{p['title']}]({p['pdf_url']})")
                
                # 区分主学科和交叉学科显示
                cat_info = f" [主分类: {p['primary_cat']}]" if p['primary_cat'] != "math.PR" else ""
                st.markdown(f"**作者**：{p['authors']} | **最新更新**：{p['updated']}{cat_info} | *(首发: {p['published']})*")
                st.write(p['summary'])
                st.markdown("---")
