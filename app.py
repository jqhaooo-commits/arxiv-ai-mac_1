import streamlit as st
import arxiv
import datetime

# 页面配置
st.set_page_config(page_title="ArXiv 数学论文检索", page_icon="📐", layout="wide")
st.title("📐 ArXiv 数学论文精准检索 (近1年)")

# 构造 arXiv 高级检索语句
def build_query(keyword, author):
    query_parts = []
    
    if keyword:
        # 需求3：限制在题目 (ti) 和摘要 (abs) 中检索
        query_parts.append(f"(ti:{keyword} OR abs:{keyword})")
        
    if author:
        query_parts.append(f"au:{author}")
        
    # 需求2：强制限定在 Mathematics (数学) 类别中检索
    query_parts.append("cat:math.*")
    
    # 将多个条件用 AND 连接
    return " AND ".join(query_parts)

# 搜索 arXiv 并过滤近 1 年的文章
def search_arxiv(query, max_results):
    if not query:
        return []
        
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    # 严格计算 1 年前的时间
    one_year_ago = datetime.datetime.now() - datetime.timedelta(days=365)
    papers = []
    
    try:
        for result in client.results(search):
            # 过滤出最近一年的文章
            if result.published.replace(tzinfo=None) >= one_year_ago:
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

# 主界面交互布局
col1, col2 = st.columns(2)
with col1:
    keyword = st.text_input("🔍 关键词 (仅限题目和摘要):", placeholder="例如: SDEs, Wasserstein...")
with col2:
    author = st.text_input("👤 作者 (Author):", placeholder="例如: Bao, Jianhai...")

# 需求1：检索文章最多拉长到 100 篇
num_papers = st.slider("最大检索篇数 (自动过滤出其中的近1年文章)", min_value=10, max_value=100, value=50)

if st.button("🚀 开始检索", type="primary"):
    if not keyword and not author:
        st.warning("⚠️ 关键词和作者至少需要填写一项！")
    else:
        search_query = build_query(keyword, author)
        
        with st.spinner("正在数学 (Mathematics) 分类下检索最近一年的论文..."):
            papers = search_arxiv(search_query, num_papers)
            
        if not papers:
            st.error("❌ 未找到最近一年内符合该条件的数学类文章。")
        else:
            st.success(f"✨ 成功筛选出 {len(papers)} 篇最近一年内的相关数学论文！")
            
            # 直接铺开展示
            for p in papers:
                st.markdown(f"### [{p['title']}]({p['pdf_url']})")
                st.markdown(f"**作者**：{p['authors']} | **发表日期**：{p['published']}")
                st.write(p['summary'])
                st.markdown("---")
