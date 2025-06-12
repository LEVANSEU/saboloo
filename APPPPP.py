import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")
st.markdown("""
    <style>
        body, .main, .block-container {
            background-color: white !important;
            color: #222 !important;
            font-family: 'Segoe UI', sans-serif;
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
            padding: 0.5rem;
            border-bottom: 2px solid #999;
            text-align: center;
            background-color: #f0f0f0;
            border-radius: 8px;
            color: #222 !important;
        }
        .summary-header div {
            flex: 1;
            padding: 0.5rem;
            background-color: #f0f0f0; /* Match the header background */
            border-right: 1px solid #ccc; /* Add separation between columns */
        }
        .summary-header div:last-child {
            border-right: none; /* Remove border from the last column */
        }
    </style>
""", unsafe_allow_html=True)

st.title("💵 ჩარიცხვების ანალიზი")

if 'selected_missing_company' not in st.session_state:
    st.session_state['selected_missing_company'] = None

statement_files = st.file_uploader("ატვირთე საბანკო ამონაწერის ფაილები (statement.xlsx)", type=["xlsx"], accept_multiple_files=True)

if statement_files:
    bank_dfs = []
    for statement_file in statement_files:
        try:
            df = pd.read_excel(statement_file)
            df['P'] = df.iloc[:, 15].astype(str).str.strip()
            df['Name'] = df.iloc[:, 14].astype(str).str.strip()
            df['Amount'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)
            bank_dfs.append(df)
        except Exception as e:
            st.error(f"ფაილის წაკითხვის შეცდომა {statement_file.name}: {str(e)}")

    bank_df = pd.concat(bank_dfs, ignore_index=True) if bank_dfs else pd.DataFrame()

    missing_data = []
    if not bank_df.empty:
        grouped = bank_df.groupby('P')
        for company_id, group in grouped:
            company_name = group['Name'].iloc[0] if not group.empty else "-"
            total_amount = group['Amount'].sum()
            missing_data.append([company_name, company_id, total_amount, 0.0, total_amount])

    if st.session_state['selected_missing_company'] is None:
        st.subheader("📋 კომპანიები")
        st.markdown("""
        <div class='summary-header'>
            <div style='flex: 2;'>დასახელება</div>
            <div style='flex: 2;'>საიდენტიფიკაციო კოდი</div>
            <div style='flex: 1.5;'>ჩარიცხული თანხა</div>
            <div style='flex: 1.5;'>ანგარიშფაქტურის თანხა</div>
            <div style='flex: 1.5;'>სხვაობა</div>
        </div>
        """, unsafe_allow_html=True)

        detail_container = st.container()
        with detail_container:
            for item in missing_data:
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 1.5, 1.5])
                with col1:
                    st.write(item[0])
                with col2:
                    if st.button(str(item[1]), key=f"mid_{item[1]}"):
                        st.session_state['selected_missing_company'] = item[1]
                with col3:
                    st.write(f"{item[2]:,.2f}")
                with col4:
                    st.write(f"{item[3]:,.2f}")
                with col5:
                    st.write(f"{item[4]:,.2f}")
    else:
        mid = st.session_state['selected_missing_company']
        transaction_data = bank_df[bank_df['P'] == str(mid)]
        st.subheader(f"📌 ჩარიცხვების დეტალურად: {mid}")

        st.markdown("""
        <div class='summary-header'>
            <div>თარიღი</div>
            <div>დანიშნულება</div>
            <div>დასახელება</div>
            <div>თანხა</div>
        </div>
        """, unsafe_allow_html=True)

        for _, row in transaction_data.iterrows():
            col1, col2, col3, col4 = st.columns([2, 4, 2, 2])
            with col1:
                st.write(str(row[0])[:10])
            with col2:
                st.write(str(row[10]))
            with col3:
                st.write(str(row['Name']))
            with col4:
                st.write(f"{row['Amount']:,.2f}")

        if st.button("⬅️ დაბრუნება"):
            st.session_state['selected_missing_company'] = None
