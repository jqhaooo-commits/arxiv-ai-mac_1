import streamlit as st
import arxiv
import datetime
from openai import OpenAI

# 页面配置
st.set_page_config(page_title="ArXiv AI 助手", page_icon="📚", layout="wide")
st.title("📚 ArXiv AI 论文搜索与分析助手 (Mac 云端版)")

# 侧边栏配置 API
with st.sidebar:
    st.header("⚙️ API 设置")
    api_key = st.text_input("输入你的 API Key", type="password")
    base_url = st.text_input("输入 Base URL (可选)", value="https://api.openai.com/v1")
    model_name = st.text_input("输入模型名称", value="gpt-4o")
    st.markdown("---")
    st.caption("提示：支持任何兼容 OpenAI 格式的 API（如 DeepSeek、通义千问等）。")

# 构造 arXiv 高级检索语句
def build_query(keyword, author):
    query_parts = []
    if keyword:
        # all: 检索标题、摘要、作者等所有文本
        query_parts.append(f"all:{keyword}")
    if author:
        # au: 检索作者名
        query_parts.append(f"au:{author}")
    
    return " AND ".join(query_parts)

# 搜索 arXiv 并过滤近 1 年的文章
def search_arxiv(query, max_results=15):
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

# AI 总结
def analyze_papers(papers, client, model):
    prompt = "你是一个顶级的学术研究助手。请根据以下最近一年的 arXiv 论文信息，为我写一份具有洞察力的中文研究综述，总结这些论文的核心方向、创新点以及发展趋势：\n\n"
    for i, p in enumerate(papers):
        prompt += f"{i+1}. 标题：{p['title']}\n作者：{p['authors']}\n发表日期：{p['published']}\n摘要：{p['summary']}\n\n"
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content

# 主界面交互布局
col1, col2 = st.columns(2)
with col1:
    keyword = st.text_input("🔍 关键词 (Keyword):", placeholder="例如: Transformer, LoRA...")
with col2:
    author = st.text_input("👤 作者 (Author):", placeholder="例如: LeCun, Vaswani...")

num_papers = st.slider("最大检索篇数 (自动过滤出其中近1年的文章)", min_value=5, max_value=30, value=10)

if st.button("🚀 开始检索并让 AI 分析", type="primary"):
    if not keyword and not author:
        st.warning("⚠️ 关键词和作者至少需要填写一项！")
    elif not api_key:
        st.warning("⚠️ 请在左侧边栏配置你的 AI API Key！")
    else:
        # 1. 构造查询语句
        search_query = build_query(keyword, author)
        
        # 2. 检索数据
        with st.spinner("正在 arXiv 上检索最近一年的论文..."):
            papers = search_arxiv(search_query, num_papers)
            
        if not papers:
            st.error("❌ 未找到最近一年内符合该【关键词】和【作者】组合的文章。")
        else:
            st.success(f"✨ 成功筛选出 {len(papers)} 篇最近一年内的相关论文！")
            
            # 展示论文列表
            with st.expander("📄 查看筛选出的论文详情"):
                for p in papers:
                    st.markdown(f"**[{p['title']}]({p['pdf_url']})**")
                    st.markdown(f"*作者：{p['authors']} | 发表日期：{p['published']}*")
                    st.write(p['summary'])
                    st.markdown("---")
            
            # AI 分析
            with st.spinner("🤖 AI 正在深度阅读摘要并生成综述..."):
                ai_client = OpenAI(api_key=api_key, base_url=base_url)
                try:
                    analysis = analyze_papers(papers, ai_client, model_name)
                    st.markdown("---")
                    st.markdown("### 🤖 AI 学术综述 (近1年成果)")
                    st.write(analysis)
                except Exception as e:
                    st.error(f"AI 调用失败: {e}")
