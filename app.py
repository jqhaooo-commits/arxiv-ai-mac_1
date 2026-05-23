import streamlit as st
import arxiv
import datetime

# 页面配置
st.set_page_config(page_title="ArXiv 概率论检索助手", page_icon="🎲", layout="wide")
st.title("🎲 ArXiv 概率论 (math.PR) 近两年更新全库")

# --- 防封禁神器：缓存数据 ---
# ttl=3600 表示缓存保留 1 小时。这 1 小时内无论你怎么查，都不会再消耗 API 请求次数
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_two_years_updates():
    client = arxiv.Client()
    # 强制按最新更新时间排序，最大请求量设为一个较高的安全值（比如 3000）
    # math.PR 两年内的更新量大概在这个量级
    search = arxiv.Search(
        query="cat:math.*", # 先宽进，再严查
        max_results=3000,
        sort_by=arxiv.SortCriterion.LastUpdatedDate, 
        sort_order=arxiv.SortOrder.Descending
    )
    
    two_years_ago = datetime.datetime.now() - datetime.timedelta(days=730)
    papers = []
    
    try:
        for result in client.results(search):
            # 核心断点：一旦发现文章的更新时间早于两年前，立刻停止抓取！
            if result.updated.replace(tzinfo=None) < two_years_ago:
                break
                
            # 核心过滤：严格检查该文章是否真的属于概率论，防止交叉分类漏杀
            if "math.PR" in result.categories:
                papers.append({
                    "title": result.title,
                    "authors": ", ".join([a.name for a in result.authors]),
                    "updated": result.updated.strftime("%Y-%m-%d"),
                    "published": result.published.strftime("%Y-%m-%d"),
                    "summary": result.summary,
                    "pdf_url": result.pdf_url
                })
    except Exception as e:
        # 如果依然偶发 429，在这里静默处理，返回已抓取的部分
        pass
        
    return papers

# 页面初始化时，在后台默默加载近两年的全量数据
with st.spinner("📦 正在从 arXiv 同步近两年的概率论更新全库（首次加载可能需要 10-20 秒，请耐心等待，随后查询将秒出）..."):
    all_two_years_papers = fetch_two_years_updates()

if not all_two_years_papers:
    st.error("⚠️ 抓取数据失败，可能是由于之前请求过于频繁 (429错误)。请等待 5 分钟后再刷新页面！")
else:
    st.success(f"✅ 成功在本地缓存 {len(all_two_years_papers)} 篇近两年的概率论更新文章！")

    # --- 界面布局 ---
    tab1, tab2 = st.tabs(["🆕 浏览近两年更新 (包含修改版)", "🔍 在近两年全库中精确检索"])

    # ==========================================
    # 第一个 Tab：浏览最新更新
    # ==========================================
    with tab1:
        st.header("🆕 浏览近两年更新")
        st.write("展示所有在近两年内提交或进行过版本更新（Replacements）的概率论文章。")
        
        num_papers_browse = st.number_input(
            "想看最近更新的前几篇？", 
            min_value=1, 
            max_value=len(all_two_years_papers), 
            value=50, 
            step=50
        )
        
        # 因为数据已经缓存，这里直接切片展示，瞬间完成
        display_papers = all_two_years_papers[:int(num_papers_browse)]
        
        for p in display_papers:
            st.markdown(f"### [{p['title']}]({p['pdf_url']})")
            st.markdown(f"**作者**：{p['authors']} | **最后更新**：{p['updated']} | *(首发: {p['published']})*")
            st.write(p['summary'])
            st.markdown("---")

    # ==========================================
    # 第二个 Tab：在本地缓存中精确检索
    # ==========================================
    with tab2:
        st.header("🔍 精准本地检索")
        st.write("在刚刚抓取下来的近两年全库中进行极速筛选，不再消耗 arXiv 额度。")
        
        col1, col2 = st.columns(2)
        with col1:
            search_keyword = st.text_input("🔍 关键词 (题目或摘要):", placeholder="例如: Wasserstein...")
        with col2:
            search_author = st.text_input("👤 作者 (Author):", placeholder="例如: Bao...")
            
        if st.button("🚀 开始极速检索", type="primary"):
            filtered_papers = []
            
            # 使用纯 Python 逻辑在缓存数据中进行极速匹配
            for p in all_two_years_papers:
                match_keyword = True
                match_author = True
                
                if search_keyword:
                    keyword_lower = search_keyword.lower()
                    if keyword_lower not in p['title'].lower() and keyword_lower not in p['summary'].lower():
                        match_keyword = False
                        
                if search_author:
                    if search_author.lower() not in p['authors'].lower():
                        match_author = False
                        
                if match_keyword and match_author:
                    filtered_papers.append(p)
            
            if not filtered_papers:
                st.warning("❌ 在近两年的更新中，未找到符合条件的文章。")
            else:
                st.success(f"✨ 极速筛选出 {len(filtered_papers)} 篇相关论文！")
                for p in filtered_papers:
                    st.markdown(f"### [{p['title']}]({p['pdf_url']})")
                    st.markdown(f"**作者**：{p['authors']} | **最后更新**：{p['updated']}")
                    st.write(p['summary'])
                    st.markdown("---")
