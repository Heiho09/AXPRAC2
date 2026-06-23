import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 한글 폰트 설정 (Streamlit Cloud 및 리눅스 환경 대응)
@st.cache_resource
def setup_font():
    # 나눔고딕 설치 경로 확인 (보통 리눅스 서버 기본 경로)
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    if os.path.exists(font_path):
        fe = fm.FontEntry(fname=font_path, name='NanumGothic')
        fm.fontManager.ttflist.insert(0, fe)
        plt.rcParams['font.family'] = fe.name
    plt.rcParams['axes.unicode_minus'] = False

setup_font()

st.title("🏭 설비 진동 분석 대시보드")

# 데이터 로드
try:
    comp_df = pd.read_csv('bearing_fault_comparison.csv')
    
    # 상단 지표
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
    fig, ax = plt.subplots(figsize=(10, 5))
    comp_df.plot(x='Fault_Type', y='rms', kind='bar', ax=ax, color='skyblue')
    ax.set_title("결함 유형별 RMS 비교")
    ax.set_ylabel("RMS Value")
    st.pyplot(fig)

    # 상세 데이터
    st.header("상세 분석 데이터")
    st.dataframe(comp_df)

except FileNotFoundError:
    st.error("CSV 파일을 찾을 수 없습니다. GitHub 저장소에 'bearing_fault_comparison.csv' 파일이 있는지 확인하세요.")
