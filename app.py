# streamlit_quality_analysis_named.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ==============================
# Streamlit 페이지 설정
# ==============================
st.set_page_config(page_title="시각화 프로그램", layout="wide")
st.title("설비 데이터 기반 품질관리 분석용 가공 데이터 시각화 프로그램 ")

# ==============================
# 0️⃣ 코드명 테이블 정의
# ==============================
t_msn_code_table = {
    '0': 1, 'C-1-01': 2, 'C-1-02': 3, 'C-1-03': 4, 'C-1-04': 5, 'C-1-05': 6, 'C-1-06': 7,
    'C-1-07': 8, 'C-1-08': 9, 'C-1-09': 10, 'C-1-10': 11, 'C-1-11': 12, 'C-1-12': 13,
    'C-2-01': 14, 'C-2-02': 15, 'C-2-03': 16, 'C-2-04': 17, 'C-2-05': 18, 'C-2-06': 19,
    'C-2-07': 20, 'C-2-08': 21, 'C-2-09': 22, 'C-2-10': 23, 'C-3-01': 24, 'C-3-02': 25,
    'C-3-03': 26, 'C-3-04': 27, 'C-3-05': 28, 'C-3-06': 29, 'C-3-07': 30, 'C-3-08': 31,
    'C-3-09': 32, 'C-3-10': 33, 'C-3-11': 34, 'C-3-12': 35, 'C-4-01': 36, 'C-4-02': 37,
    'C-4-04': 38, 'C-4-05': 39, 'C-4-06': 40, 'C-4-07': 41, 'C-4-08': 42, 'C-5-02': 43,
    'C-5-03': 44, 'C-5-05': 45, 'C-5-06': 46, 'C-5-07': 47, 'C-5-08': 48, 'C-5-09': 49,
    'C-5-10': 50, 'C-5-11': 51, 'C-5-12': 52, 'C-6-01': 53, 'C-6-02': 54, 'C-6-03': 55,
    '도금': 56, '사상': 57
}
t_msn_code_rev = {v:k for k,v in t_msn_code_table.items()}

t_gaf1_code_table = {
    '0': 1, 'HEX': 2, '나사1': 3, '나사2': 4, '나사길이1': 5, '나사길이2': 6, '내경': 7,
    '내경1': 8, '내경2': 9, '내경3': 10, '니시2': 11, '목경': 12, '시트부외경': 13,
    '오링부 목경': 14, '외경': 15, '외경1': 16, '외경2': 17, '전장': 18
}
t_gaf1_code_rev = {v:k for k,v in t_gaf1_code_table.items()}

# ==============================
# 1️⃣ CSV 업로드
# ==============================
uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.subheader("원본 데이터 확인")
    st.dataframe(df.head())

    # ==============================
    # 2️⃣ 데이터 전처리
    # ==============================
    df['T_CHL_numeric'] = pd.to_numeric(df['T_CHL_numeric'], errors='coerce')
    df['T_CHL_rolling3'] = pd.to_numeric(df['T_CHL_rolling3'], errors='coerce')

    # Defect 정의
    df['Defect'] = df['T_CHL_numeric'].apply(lambda x: 1 if pd.notna(x) and x < 10 else 0)

    # 코드값 생성 (모델용)
    df['T_MSN_code'] = df['T_MSN'].map(t_msn_code_table)
    df['T_GAF1_code'] = df['T_GAF1'].map(t_gaf1_code_table)

    # 명칭 생성 (화면용)
    df['T_MSN_name'] = df['T_MSN_code'].map(t_msn_code_rev)
    df['T_GAF1_name'] = df['T_GAF1_code'].map(t_gaf1_code_rev)

    # ==============================
    # 3️⃣ 설비별 요약 테이블
    # ==============================
    equipment_codes = df['T_MSN_code'].unique()
    summary_list = []

    for code in equipment_codes:
        temp = df[df['T_MSN_code']==code]
        summary = {
            '설비': t_msn_code_rev[code],  # 코드 → 명칭
            '작업수량 평균': temp['Qty'].mean(),
            '측정값 평균': temp['T_CHL_numeric'].mean(),
            '롤링평균': temp['T_CHL_rolling3'].mean(),
            '불량률': temp['Defect'].mean()
        }
        summary_list.append(summary)

    df_summary = pd.DataFrame(summary_list).sort_values(by='불량률', ascending=False)
    st.subheader("설비별 품질 현황 (명칭 표시)")
    st.dataframe(df_summary)

    # ==============================
    # 4️⃣ 설비별 막대그래프
    # ==============================
    st.subheader("설비별 품질 현황 막대그래프")
    df_melted = df_summary.melt(id_vars='설비', var_name='지표', value_name='값')
    fig_bar = px.bar(df_melted,
                     x='지표', y='값', color='설비', barmode='group',
                     text='값', height=500,
                     title='설비별 품질 현황 (작업수량, 측정값, 롤링평균, 불량률)')
    fig_bar.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig_bar.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig_bar, use_container_width=True)

    # ==============================
    # 5️⃣ 설비별 상관관계 히트맵
    # ==============================
    st.subheader("설비별 상관관계 히트맵")
    st.markdown("""
    - 설비명(C-2-08 등): 불량률 (Defect)
    - 설비명(C-2-08 등): 작업수량 (Qty)  
    - 설비명(C-2-08 등): 측정값 (T_CHL_numeric)
    - 설비명(C-2-08 등): 측정값 평균 (T_CHL_rolling3)
    """)

    target_cols = ['Defect', 'Qty', 'T_CHL_numeric', 'T_CHL_rolling3']
    z_data = []
    y_labels = []

    for code in equipment_codes:
        temp = df[df['T_MSN_code']==code][target_cols]
        if len(temp) > 1:
            corr = temp.corr().round(2)
            z_data.append(corr.values)
            y_labels.append(t_msn_code_rev[code])

    if z_data:
        n_equip = len(z_data)
        z_combined = np.vstack(z_data)
        y_combined = []
        for equip_name in y_labels:
            for var in target_cols:
                y_combined.append(f"{equip_name} : {var}")

        fig_corr = go.Figure(data=go.Heatmap(
            z=z_combined,
            x=target_cols,
            y=y_combined,
            colorscale='RdBu',
            zmin=-1, zmax=1,
            text=np.round(z_combined, 2),
            hovertemplate='설비-변수: %{y}<br>%{x}: %{text}<extra></extra>'
        ))
        fig_corr.update_layout(height=50*n_equip*4)
        st.plotly_chart(fig_corr, use_container_width=True)
