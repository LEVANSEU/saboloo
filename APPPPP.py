import streamlit as st
import pandas as pd
import re

st.set_page_config(layout="wide")

st.title("ფაილების ანალიზი")

report_file = st.file_uploader("ატვირთე ანგარიშფაქტურების ფაილი", type=["xlsx"])
statement_files = st.file_uploader("ატვირთე საბანკო ამონაწერის ფაილები", type=["xlsx"], accept_multiple_files=True)

if report_file and statement_files:
    purchases_df = pd.read_excel(report_file, sheet_name='Grid')
    bank_dfs = []
    for statement_file in statement_files:
        df = pd.read_excel(statement_file)
        df['P'] = df.iloc[:, 15].astype(str).str.strip()
        df['Name'] = df.iloc[:, 14].astype(str).str.strip()
        df['Amount'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)
        bank_dfs.append(df)
    bank_df = pd.concat(bank_dfs, ignore_index=True) if bank_dfs else pd.DataFrame()
    purchases_df['დასახელება'] = purchases_df['გამყიდველი'].astype(str).apply(lambda x: re.sub(r'^\(\d+\)\s*', '', x).strip())
    purchases_df['საიდენტიფიკაციო კოდი'] = purchases_df['გამყიდველი'].apply(lambda x: ''.join(re.findall(r'\d', str(x)))[:11])

    tab_choice = st.radio("აირჩიე ფუნქციონალი:", ["ანგარიშფაქტურები", "ჩარიცხვები"])

    if tab_choice == "ანგარიშფაქტურები":
        st.subheader("ანგარიშფაქტურები კომპანიით")
        unique_codes = purchases_df['საიდენტიფიკაციო კოდი'].unique()
        for code in unique_codes:
            company_df = purchases_df[purchases_df['საიდენტიფიკაციო კოდი'] == code]
            company_name = company_df['დასახელება'].iloc[0]
            invoice_sum = company_df['ღირებულება დღგ და აქციზის ჩათვლით'].sum()
            payment_sum = bank_df[bank_df['P'] == str(code)]['Amount'].sum()
            diff = invoice_sum - payment_sum
            st.markdown(f"**{company_name} ({code})**")
            st.write(f"ინვოისების ჯამი: {invoice_sum:,.2f}")
            st.write(f"ჩარიცხვების ჯამი: {payment_sum:,.2f}")
            st.write(f"სხვაობა: {diff:,.2f}")
            st.markdown("---")

    elif tab_choice == "ჩარიცხვები":
        bank_company_ids = bank_df['P'].unique()
        invoice_company_ids = purchases_df['საიდენტიფიკაციო კოდი'].unique()
        missing_company_ids = [cid for cid in bank_company_ids if cid not in invoice_company_ids]

        if missing_company_ids:
            st.subheader("კომპანიები ანგარიშფაქტურის სიაში არ არიან")
            missing_data = []
            for company_id in missing_company_ids:
                matching_rows = bank_df[bank_df['P'] == str(company_id)]
                company_name = matching_rows['Name'].iloc[0] if not matching_rows.empty else "-"
                total_amount = matching_rows['Amount'].sum()
                invoice_amount = 0.00
                difference = total_amount - invoice_amount
                missing_data.append([company_name, company_id, total_amount, invoice_amount, difference])

            for item in missing_data:
                st.markdown(f"**{item[0]} ({item[1]})**")
                st.write(f"ჩარიცხული თანხა: {item[2]:,.2f}")
                st.write(f"ანგარიშფაქტურის თანხა: {item[3]:,.2f}")
                st.write(f"სხვაობა: {item[4]:,.2f}")
                st.markdown("---")
        else:
            st.info("ყველა კომპანია ანგარიშფაქტურის სიაში გამოჩნდა.")
