import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib

st.title("🏭 설비 진동 분석 대시보드")

# 데이터 로드
comp_df = pd.read_csv('bearing_fault_comparison.csv')

# 상단 지표 (Metrics)
st.header("핵심 특징값 요약")
cols = st.columns(3)
with cols[0]:
    st.metric("평균 RMS", round(comp_df['rms'].mean(), 3))
with cols[1]:
    st.metric("최고 Kurtosis", round(comp_df['kurtosis'].max(), 3))
with cols[2]:
    st.metric("결함 유형 수", len(comp_df))

# 시각화
st.header("결함 유형별 비교")
fig, ax = plt.subplots()
comp_df.plot(x='Fault_Type', y='rms', kind='bar', ax=ax, color='skyblue')
st.pyplot(fig)

# 상세 데이터 표
st.dataframe(comp_df)
