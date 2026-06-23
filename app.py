import streamlit as st
import numpy as np
import pandas as pd
from scipy.io import loadmat
from scipy.stats import kurtosis
from scipy.fft import rfft, rfftfreq
import plotly.graph_objects as go
import plotly.express as px
import os

# 페이지 기본 설정
st.set_page_config(page_title="설비 진동 분석 대시보드", page_icon="⚙️", layout="wide")

st.title("⚙️ CBM 기반 베어링 진동 분석 대시보드")
st.markdown("정상, 내륜 결함, 볼 결함 진동 데이터를 비교 분석하여 설비의 이상 유무를 진단합니다.")

# ---------------------------------------------------------
# 1. 데이터 로드 및 처리 함수 정의
# ---------------------------------------------------------
@st.cache_data
def get_cwru_signal(file_path_or_obj):
    """.mat 파일에서 DE_time (드라이브 엔드 진동) 신호를 추출합니다."""
    try:
        mat_data = loadmat(file_path_or_obj)
        for key in mat_data.keys():
            if 'DE_time' in key:
                return mat_data[key].flatten()
        return None
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return None

def calculate_features(sig):
    """신호의 시간 영역 통계적 특징값을 계산합니다."""
    rms = np.sqrt(np.mean(sig**2))
    peak = np.max(np.abs(sig))
    kurt = kurtosis(sig, fisher=False)
    crest_factor = peak / rms if rms != 0 else 0
    return {
        'RMS': rms,
        'Peak': peak,
        'Kurtosis': kurt,
        'Crest Factor': crest_factor
    }

def get_fft(sig, fs=12000):
    """FFT(고속 푸리에 변환)를 수행합니다."""
    n = len(sig)
    yf = np.abs(rfft(sig)) / n
    xf = rfftfreq(n, 1/fs)
    return xf, yf

# ---------------------------------------------------------
# 2. 사이드바 - 파일 업로드 및 데이터 설정
# ---------------------------------------------------------
st.sidebar.header("📁 진동 데이터 설정")
st.sidebar.markdown("`.mat` 파일을 직접 업로드하거나 로컬 데이터를 사용합니다.")

uploaded_normal = st.sidebar.file_uploader("정상 상태 (Time_Normal)", type=['mat'])
uploaded_inner = st.sidebar.file_uploader("내륜 결함 (IR007)", type=['mat'])
uploaded_ball = st.sidebar.file_uploader("볼 결함 (B007)", type=['mat'])

# 파일 객체 또는 기본 경로 매핑
data_sources = {
    "정상 (Normal)": uploaded_normal if uploaded_normal else "Time_Normal_1_098.mat",
    "내륜 결함 (Inner)": uploaded_inner if uploaded_inner else "IR007_1_110.mat",
    "볼 결함 (Ball)": uploaded_ball if uploaded_ball else "B007_1_123.mat"
}

# 데이터 추출
signals = {}
features_list = []

with st.spinner("데이터를 분석 중입니다..."):
    for label, source in data_sources.items():
        # 파일이 문자열(경로)이고 존재하지 않으면 스킵
        if isinstance(source, str) and not os.path.exists(source):
            continue
            
        sig = get_cwru_signal(source)
        if sig is not None:
            signals[label] = sig
            # 특징값 계산
            feats = calculate_features(sig)
            feats['Condition'] = label
            features_list.append(feats)

if not signals:
    st.warning("⚠️ 분석할 데이터가 없습니다. 좌측 사이드바에서 `.mat` 파일을 업로드해주세요.")
    st.stop()

df_features = pd.DataFrame(features_list)
# 컬럼 순서 재배치
cols = ['Condition', 'RMS', 'Peak', 'Kurtosis', 'Crest Factor']
df_features = df_features[cols]

# ---------------------------------------------------------
# 3. 대시보드 뷰 구성 (탭)
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📊 특징값 요약 & 진단", "📈 시간 영역 파형", "〰️ 주파수 영역 (FFT)", "📋 상세 데이터"])

# --- Tab 1: 특징값 요약 및 진단 ---
with tab1:
    st.subheader("💡 설비 상태 진단 (CBM)")
    
    if "정상 (Normal)" in df_features['Condition'].values:
        baseline_rms = df_features[df_features['Condition'] == '정상 (Normal)']['RMS'].values[0]
        st.info(f"**진단 기준:** 정상 상태의 RMS({baseline_rms:.4f}) 대비 1.5배 초과 시 '주의', 2배 초과 시 '경고'로 판단합니다.")
    else:
        baseline_rms = 0.07 # 임의의 기본값
        
    cols = st.columns(len(signals))
    
    for idx, (label, sig) in enumerate(signals.items()):
        feats = df_features[df_features['Condition'] == label].iloc[0]
        
        # 상태 진단 로직
        status = "🟢 정상"
        status_color = "normal"
        if feats['RMS'] > baseline_rms * 2:
            status = "🔴 경고 (위험)"
            status_color = "inverse"
        elif feats['RMS'] > baseline_rms * 1.5:
            status = "🟡 주의 (점검 요망)"
            status_color = "off"
            
        with cols[idx]:
            st.markdown(f"### {label}")
            st.metric("진단 상태", status, delta_color=status_color)
            st.metric("RMS (에너지)", f"{feats['RMS']:.4f}")
            st.metric("Kurtosis (충격도)", f"{feats['Kurtosis']:.2f}")

    st.markdown("---")
    st.subheader("📊 지표별 비교 차트")
    
    fig_col1, fig_col2, fig_col3 = st.columns(3)
    with fig_col1:
        fig_rms = px.bar(df_features, x='Condition', y='RMS', color='Condition', title='RMS 비교 (전반적 진동 크기)')
        st.plotly_chart(fig_rms, use_container_width=True)
    with fig_col2:
        fig_kurt = px.bar(df_features, x='Condition', y='Kurtosis', color='Condition', title='Kurtosis 비교 (충격성 결함)')
        st.plotly_chart(fig_kurt, use_container_width=True)
    with fig_col3:
        fig_crest = px.bar(df_features, x='Condition', y='Crest Factor', color='Condition', title='Crest Factor 비교')
        st.plotly_chart(fig_crest, use_container_width=True)


# --- Tab 2: 시간 영역 파형 ---
with tab2:
    st.subheader("📈 시간 영역 진동 파형 (Time Domain)")
    st.markdown("데이터의 크기가 크므로 처음 **2,000개**의 데이터 포인트만 시각화합니다.")
    
    fig_time = go.Figure()
    for label, sig in signals.items():
        # 시각화 최적화를 위해 앞 2000개만 슬라이싱
        plot_sig = sig[:2000] 
        fig_time.add_trace(go.Scatter(y=plot_sig, mode='lines', name=label, opacity=0.8))
        
    fig_time.update_layout(
        title="Time Domain Signal (First 2000 points)",
        xaxis_title="Data Points",
        yaxis_title="Amplitude",
        height=500,
        hovermode="x unified"
    )
    st.plotly_chart(fig_time, use_container_width=True)


# --- Tab 3: 주파수 영역 (FFT) ---
with tab3:
    st.subheader("〰️ 주파수 영역 파형 (Frequency Domain / FFT)")
    fs = st.slider("샘플링 주파수 (Hz)", min_value=1000, max_value=20000, value=12000, step=1000, help="CWRU 데이터는 기본 12kHz를 사용합니다.")
    
    fig_fft = go.Figure()
    for label, sig in signals.items():
        xf, yf = get_fft(sig, fs=fs)
        # 0Hz(DC 성분) 제외하고 플롯
        fig_fft.add_trace(go.Scatter(x=xf[1:], y=yf[1:], mode='lines', name=label, opacity=0.7))
        
    fig_fft.update_layout(
        title="FFT Spectrum",
        xaxis_title="Frequency (Hz)",
        yaxis_title="Amplitude",
        xaxis=dict(range=[0, 2000]), # 주요 주파수 대역인 0~2000Hz 범위로 제한
        height=600,
        hovermode="x unified"
    )
    st.plotly_chart(fig_fft, use_container_width=True)


# --- Tab 4: 데이터 요약 표 ---
with tab4:
    st.subheader("📋 추출된 특징값 데이터")
    st.dataframe(df_features.style.highlight_max(axis=0, color='lightcoral', subset=['RMS', 'Peak', 'Kurtosis']))
    
    # CSV 다운로드 버튼
    csv = df_features.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 CSV로 결과 다운로드",
        data=csv,
        file_name='bearing_fault_comparison.csv',
        mime='text/csv',
    )
