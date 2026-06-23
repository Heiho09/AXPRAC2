import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

# 한글 폰트 설정 (Streamlit Cloud 및 리눅스 환경 대응)
@st.cache_resource
def setup_font():
    font_path = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"
    if os.path.exists(font_path):
        fe = fm.FontEntry(fname=font_path, name='NanumGothic')
        fm.fontManager.ttflist.insert(0, fe)
        plt.rcParams['font.family'] = fe.name
    plt.rcParams['axes.unicode_minus'] = False

setup_font()

st.set_page_config(page_title="설비 진동 모니터링", layout="wide")
st.title("🏭 설비 진동 분석 및 트렌드 대시보드")

try:
    # 데이터 로드
    comp_df = pd.read_csv('bearing_fault_comparison.csv')
    trend_df = pd.read_csv('bearing_trend_data.csv')

    # 1. 상단 요약 지표
    st.header("📍 상태 요약 지표")
    cols = st.columns(3)
    with cols[0]:
        st.metric("평균 RMS", f"{comp_df['rms'].mean():.3f}")
    with cols[1]:
        st.metric("최대 Kurtosis", f"{comp_df['kurtosis'].max():.3f}")
    with cols[2]:
        st.metric("분석 데이터 수", f"{len(trend_df):,}")

    # 2. 결함 유형별 비교 (Static)
    st.header("📊 결함 유형별 특징값 비교")
    col1, col2 = st.columns(2)
    with col1:
        fig1, ax1 = plt.subplots()
        comp_df.plot(x='Fault_Type', y='rms', kind='bar', ax=ax1, color='skyblue')
        ax1.set_title("결함 유형별 RMS (에너지)")
        st.pyplot(fig1)
    with col2:
        fig2, ax2 = plt.subplots()
        comp_df.plot(x='Fault_Type', y='kurtosis', kind='bar', ax=ax2, color='salmon')
        ax2.set_title("결함 유형별 Kurtosis (충격성)")
        st.pyplot(fig2)

    # 3. 구간별 추세 분석 (Dynamic)
    st.header("📈 시간 흐름에 따른 특징값 변화 (Trend)")
    feature_to_plot = st.selectbox("확인할 특징값을 선택하세요", ['rms', 'kurtosis', 'crest_factor'])
    
    fig3, ax3 = plt.subplots(figsize=(12, 4))
    for state, group in trend_df.groupby('state'):
        ax3.plot(group['time_sec'], group[feature_to_plot], label=state, alpha=0.7)
    ax3.set_title(f"시간대별 {feature_to_plot} 추세 비교")
    ax3.set_xlabel("Time (s)")
    ax3.set_ylabel(feature_to_plot)
    ax3.legend()
    st.pyplot(fig3)

    # 4. 데이터 원본 확인
    with st.expander("원본 데이터 보기"):
        st.dataframe(comp_df)

except FileNotFoundError:
    st.error("CSV 파일(bearing_fault_comparison.csv, bearing_trend_data.csv)이 없습니다. GitHub에 파일을 모두 올렸는지 확인하세요.")
