import streamlit as st
import pandas as pd
import io
from openpyxl import Workbook
import re

st.set_page_config(layout="wide")

# Add custom CSS for style
st.markdown("""
    <style>
        body, .main, .block-container {
            background-color: white !important;
            color: #222 !important;
            font-family: 'Segoe UI', sans-serif;
        }
        h1, h2, h3, h4, h5, h6, .stMarkdown, .stText, .stTextLabelWrapper, label {
            color: #222 !important;
        }
        .stFileUploader, .stTextInput, .stSelectbox, .stRadio, .stButton, .stDataFrame,
        .stTextInput input, .stSelectbox div[data-baseweb="select"],
        .stSelectbox div[data-baseweb="select"] *,
        .stRadio div[role="radiogroup"] label,
        .stRadio div[role="radiogroup"] label * {
            background-color: #f5f5f5 !important;
            color: #222 !important;
            border-radius: 10px;
            font-size: 14px !important;
        }
        .stFileUploader {
            max-width: 600px !important;
            margin: 0 auto !important;
        }
        .stButton>button {
            background-color: #4CAF50;
            color: white !important;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            padding: 6px 14px;
            font-size: 14px;
        }
        .stButton>button:hover {
            background-color: #45a049;
        }
        .summary-header {
            display: flex;
            font-weight: bold;
            margin-top: 1em;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #999;
            text-align: center;
            background-color: #f0f0f0;
            border-radius: 8px;
            color: #222 !important;
        }
        .summary-header div {
            flex: 1;
            padding: 0.5rem;
        }
        .number-cell {
            text-align: right !important;
            font-variant-numeric: tabular-nums;
            padding-right: 1rem;
            font-weight: bold;
            color: #222;
        }
        .stTable td, .stTable th {
            color: #222 !important;
            background-color: white !important;
        }
        .stTable td:nth-child(n+3), .stTable th:nth-child(n+3) {
            text-align: right !important;
            font-variant-numeric: tabular-nums;
            padding-right: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

st.title("Excel გენერატორი")

report_file = st.file_uploader("ატვირთე ანგარიშფაქტურების ფაილი (report.xlsx)", type=["xlsx"])
statement_files = st.file_uploader("ატვირთე საბანკო ამონაწერის ფაილები (statement.xlsx)", type=["xlsx"], accept_multiple_files=True)

if 'selected_missing_company' not in st.session_state:
    st.session_state['selected_missing_company'] = None

if report_file and statement_files:
    purchases_df = pd.read_excel(report_file, sheet_name='Grid')

    bank_dfs = []
    for file in statement_files:
        df = pd.read_excel(file)
        df['P'] = df.iloc[:, 15].astype(str).str.strip()
        df['Name'] = df.iloc[:, 14].astype(str).str.strip()
        df['Amount'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)
        bank_dfs.append(df)

    bank_df = pd.concat(bank_dfs, ignore_index=True)

    purchases_df['დასახელება'] = purchases_df['გამყიდველი'].astype(str).apply(lambda x: re.sub(r'^\(\d+\)\s*', '', x).strip())
    purchases_df['საიდენტიფიკაციო კოდი'] = purchases_df['გამყიდველი'].apply(lambda x: ''.join(re.findall(r'\d', str(x)))[:11])

    if st.session_state['selected_missing_company'] is None:
        st.subheader("📋 კომპანიები ანგარიშფაქტურის სიაში არ არიან")

        bank_company_ids = bank_df['P'].unique()
        invoice_company_ids = purchases_df['საიდენტიფიკაციო კოდი'].unique()
        missing_ids = [cid for cid in bank_company_ids if cid not in invoice_company_ids]

        for cid in missing_ids:
            rows = bank_df[bank_df['P'] == cid]
            name = rows['Name'].iloc[0] if not rows.empty else "-"
            total = rows['Amount'].sum()

            col1, col2, col3 = st.columns([3, 3, 2])
            with col1:
                st.write(name)
            with col2:
                if st.button(str(cid), key=f"go_{cid}"):
                    st.session_state['selected_missing_company'] = cid
                    st.experimental_rerun()
            with col3:
                st.write(f"{total:,.2f}")
    else:
        cid = st.session_state['selected_missing_company']
        st.subheader(f"📌 ჩარიცხვების დეტალური სია: {cid}")
        company_data = bank_df[bank_df['P'] == cid]
        st.dataframe(company_data, use_container_width=True)
        if st.button("⬅️ დაბრუნება"):
            st.session_state['selected_missing_company'] = None
            st.experimental_rerun()
