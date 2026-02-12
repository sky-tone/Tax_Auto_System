import streamlit as st
import pandas as pd
from utils import ocr_process, accounting_rules

# --- 这是一个标准的 Streamlit 开源界面框架 ---

st.set_page_config(page_title="智能税务记账系统", layout="wide")

st.title("🧾 智能税务转会计系统 (开源修改版)")
st.markdown("基于 PaddleOCR 和 Pandas 构建")

# 1. 侧边栏：上传文件
with st.sidebar:
    st.header("1. 上传发票")
    uploaded_files = st.file_uploader("请上传图片或 PDF", accept_multiple_files=True, type=['png', 'jpg', 'jpeg', 'pdf'])

# 2. 主界面：处理逻辑
if uploaded_files:
    st.success(f"已上传 {len(uploaded_files)} 张发票")
    
    if st.button("开始自动化识别与记账"):
        progress_bar = st.progress(0)
        all_data = []

        for i, file in enumerate(uploaded_files):
            # 调用 utils.py 中的功能（这是我们要修改的地方）
            # 第一步：OCR 识别
            raw_text_data = ocr_process.extract_text(file)
            
            # 第二步：记账规则映射
            processed_data = accounting_rules.map_subject(raw_text_data)
            
            all_data.append(processed_data)
            progress_bar.progress((i + 1) / len(uploaded_files))

        # 3. 结果展示
        df = pd.DataFrame(all_data)
        st.subheader("2. 识别结果与科目自动生成")
        
        # 显示所有列（包括新增的发票字段）
        display_cols = [
            '文件名', '识别商品名', '金额', '日期',
            '发票号', '发票代码', '开票机构', '购方', '税额',
            '会计科目', '错误', '警告'
        ]
        display_df = df[[col for col in display_cols if col in df.columns]]
        st.dataframe(display_df, use_container_width=True)

        # 4. 报表生成（直接用 Pandas 的透视表功能）
        st.subheader("3. 自动生成资产负债表预览")
        if '金额' in df.columns and '会计科目' in df.columns:
            report = df.groupby('会计科目')['金额'].sum().reset_index()
            st.dataframe(report, use_container_width=True)
            
        # 5. 下载结果
        # (此处省略下载代码，AI会自动补全)