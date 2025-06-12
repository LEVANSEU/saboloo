import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("💵 ჩარიცხვების დეტალური ანალიზი")

# საბანკო ფაილების ატვირთვა
statement_files = st.file_uploader("ატვირთე საბანკო ამონაწერის ფაილები", type=["xlsx"], accept_multiple_files=True)

if statement_files:
    bank_dfs = []
    for file in statement_files:
        df = pd.read_excel(file)
        df['P'] = df.iloc[:, 15].astype(str).str.strip()
        df['Name'] = df.iloc[:, 14].astype(str).str.strip()
        df['Amount'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)
        bank_dfs.append(df)

    bank_df = pd.concat(bank_dfs, ignore_index=True)

    if 'selected_missing_company' not in st.session_state:
        st.session_state['selected_missing_company'] = None

    if st.session_state['selected_missing_company'] is None:
        st.subheader("📋 კომპანიები რომლებიც ანგარიშფაქტურებში არ არიან")

        # უნიკალური კოდები
        unique_ids = bank_df['P'].unique()
        company_data = []
        for cid in unique_ids:
            rows = bank_df[bank_df['P'] == str(cid)]
            name = rows['Name'].iloc[0] if not rows.empty else "-"
            total = rows['Amount'].sum()
            company_data.append((name, cid, total))

        search_input = st.text_input("🔍 ძებნა (დასახელება ან კოდი)")
        filtered = [
            item for item in company_data
            if search_input.lower() in item[0].lower() or search_input.strip() in item[1]
        ] if search_input else company_data

        for name, cid, total in filtered:
            col1, col2, col3 = st.columns([2, 2, 2])
            with col1:
                st.markdown(name)
            with col2:
                if st.button(cid, key=f"mid_{cid}"):
                    st.session_state['selected_missing_company'] = cid
                    st.experimental_rerun()
            with col3:
                st.markdown(f"{total:,.2f}")
    else:
        selected_id = st.session_state['selected_missing_company']
        selected_df = bank_df[bank_df['P'] == str(selected_id)]

        st.subheader(f"📌 დეტალური ჩარიცხვები: {selected_id}")
        st.dataframe(selected_df[['Name', 'P', 'Amount']], use_container_width=True)

        if st.button("⬅️ დაბრუნება"):
            st.session_state['selected_missing_company'] = None
            st.experimental_rerun()
