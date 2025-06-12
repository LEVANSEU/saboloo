import streamlit as st
import pandas as pd
import io
from openpyxl import Workbook
import re

st.set_page_config(layout="wide")
st.title("Excel გენერატორი")

report_file = st.file_uploader("ატვირთე ანგარიშფაქტურების ფაილი (report.xlsx)", type=["xlsx"])
statement_files = st.file_uploader("ატვირთე საბანკო ამონაწერის ფაილები (statement.xlsx)", type=["xlsx"], accept_multiple_files=True)

if report_file and statement_files:
    try:
        purchases_df = pd.read_excel(report_file, sheet_name='Grid')
    except Exception as e:
        st.error(f"ანგარიშფაქტურის ფაილის წაკითხვის შეცდომა: {str(e)}")
        purchases_df = pd.DataFrame()

    bank_dfs = []
    for statement_file in statement_files:
        try:
            df = pd.read_excel(statement_file)
            df['P'] = df.iloc[:, 15].astype(str).str.strip()
            df['Name'] = df.iloc[:, 14].astype(str).str.strip()
            df['Amount'] = pd.to_numeric(df.iloc[:, 3], errors='coerce').fillna(0)
            bank_dfs.append(df)
        except Exception as e:
            st.error(f"საბანკო ამონაწერის წაკითხვის შეცდომა ({statement_file.name}): {str(e)}")

    bank_df = pd.concat(bank_dfs, ignore_index=True) if bank_dfs else pd.DataFrame()

    purchases_df['დასახელება'] = purchases_df['გამყიდველი'].astype(str).apply(lambda x: re.sub(r'^\(\d+\)\s*', '', x).strip())
    purchases_df['საიდენტიფიკაციო კოდი'] = purchases_df['გამყიდველი'].apply(lambda x: ''.join(re.findall(r'\d', str(x)))[:11])

    wb = Workbook()
    wb.remove(wb.active)
    ws1 = wb.create_sheet(title="ანგარიშფაქტურები კომპანიით")
    ws1.append(['დასახელება', 'საიდენტიფიკაციო კოდი', 'ანგარიშფაქტურების ჯამი', 'ჩარიცხული თანხა', 'სხვაობა'])

    company_summaries = []
    for company_id, group in purchases_df.groupby('საიდენტიფიკაციო კოდი'):
        try:
            company_name = group['დასახელება'].iloc[0]
            unique_invoices = group.groupby('სერია №')['ღირებულება დღგ და აქციზის ჩათვლით'].sum().reset_index()
            company_invoice_sum = unique_invoices['ღირებულება დღგ და აქციზის ჩათვლით'].sum()

            paid_sum = bank_df[bank_df["P"] == str(company_id)]['Amount'].sum()
            difference = company_invoice_sum - paid_sum

            ws1.append([company_name, company_id, company_invoice_sum, paid_sum, difference])
            company_summaries.append((company_name, company_id, company_invoice_sum, paid_sum, difference))
        except Exception as e:
            st.error(f"კომპანიის დამუშავების შეცდომა {company_id}: {str(e)}")

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    st.subheader("📋 კომპანიები ანგარიშფაქტურის სიაში არ არიან")
    search_query = st.text_input("🔎 ძებნა (კოდი ან დასახელება):", key="search_query_missing")
    sort_order_missing = st.radio("სორტირება:", ["ზრდადობით", "კლებადობით"], key="sort_order_missing", horizontal=True)

    bank_company_ids = bank_df['P'].unique()
    invoice_company_ids = purchases_df['საიდენტიფიკაციო კოდი'].unique()
    missing_company_ids = [cid for cid in bank_company_ids if cid not in invoice_company_ids]

    if missing_company_ids:
        missing_data = []
        for company_id in missing_company_ids:
            matching_rows = bank_df[bank_df['P'] == str(company_id)]
            company_name = matching_rows['Name'].iloc[0] if not matching_rows.empty else "-"
            total_amount = bank_df[bank_df['P'] == str(company_id)]['Amount'].sum()
            invoice_amount = 0.00
            difference = total_amount - invoice_amount
            missing_data.append([company_name, company_id, total_amount, invoice_amount, difference])

        if search_query.strip():
            missing_data = [item for item in missing_data if 
                          str(item[1]) == search_query.strip() or 
                          str(item[0]).lower().find(search_query.lower().strip()) != -1]

        sort_reverse = sort_order_missing == "კლებადობით"
        missing_data.sort(key=lambda x: x[2], reverse=sort_reverse)

        st.markdown("""
        <div style='display: flex; font-weight: bold; margin-top: 1em; padding-bottom: 0.5rem; border-bottom: 2px solid #999; text-align: center; background-color: #f0f0f0; border-radius: 8px; color: #222;'>
            <div style='flex: 2;'>დასახელება</div>
            <div style='flex: 2;'>საიდენტიფიკაციო კოდი</div>
            <div style='flex: 1.5;'>ჩარიცხული თანხა</div>
            <div style='flex: 1.5;'>ანგარიშფაქტურის თანხა</div>
            <div style='flex: 1.5;'>სხვაობა</div>
        </div>
        """, unsafe_allow_html=True)

        for item in missing_data:
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 1.5, 1.5])
            with col1:
                st.write(item[0])
            with col2:
                st.write(item[1])
            with col3:
                st.write(f"{item[2]:,.2f}")
            with col4:
                st.write(f"{item[3]:,.2f}")
            with col5:
                st.write(f"{item[4]:,.2f}")
    else:
        st.info("ყველა კომპანია ანგარიშფაქტურის სიაში მოხვდა.")

    st.download_button(
        label="⬇️ ჩამოტვირთე Excel ფაილი",
        data=output,
        file_name="ანგარიშფაქტურები.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
