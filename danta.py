# 메인 애플리케이션
def main():
    # 화면 크기 감지 (JavaScript)
    screen_width = st.session_state.get('screen_width', 1200)
    
    # 화면 크기 감지 스크립트
    st.markdown("""
    <script>
    function updateScreenWidth() {
        const width = window.innerWidth;
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            data: { screen_width: width }
        }, '*');
    }
    updateScreenWidth();
    window.addEventListener('resize', updateScreenWidth);
    </script>
    """, unsafe_allow_html=True)
    
    # 모바일 감지
    is_mobile = screen_width < 768
    
    # 헤더
    if is_mobile:
        st.markdown("""
        <div class="main-header">
            <h1>📊 업비트 분석기</h1>
            <p style="text-align: center; color: white; margin: 0; font-size: 0.9rem;">실시간 차트 분석</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="main-header">
            <h1>📊 업비트 차트 분석기</h1>
            <p style="text-align: center; color: white; margin: 0;">실시간 업비트 데이터로 전문가급 차트 분석</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 모바일용 간소화된 사이드바
    if is_mobile:
        # 모바일에서는 상단에 주요 설정만 표시
        st.markdown("### ⚙️ 설정")
        col1, col2 = st.columns(2)
        
        with col1:
            tickers = get_upbit_tickers()
            coin_name = st.selectbox("종목", list(tickers.keys()), key="mobile_coin")
        
        with col2:
            interval = st.selectbox("간격", ['1시간', '4시간', '일봉', '주봉'], index=2, key="mobile_interval")
        
        # 간단한 설정
        show_support_resistance = st.checkbox("📊 지지/저항선", value=True, key="mobile_sr")
        indicators = ['MA20']  # 모바일에서는 MA20만
        
        market_code = tickers[coin_name]
        candle_count = 100  # 모바일에서는 데이터 적게
        show_volume_profile = False
        
    else:
        # 데스크톱용 전체 사이드바
        with st.sidebar:
            st.markdown("## ⚙️ 분석 설정")
            
            # 주요 암호화폐 선택
            tickers = get_upbit_tickers()
            
            # 종목 선택
            coin_name = st.selectbox(
                "📈 분석할 종목을 선택하세요",
                options=list(tickers.keys()),
                index=0
            )
            
            if coin_name:
                market_code = tickers[coin_name]
                st.success(f"선택된 종목: {market_code}")
            
            # 시간 간격 선택
            interval = st.selectbox(
                "⏰ 차트 간격",
                options=['1분', '5분', '15분', '30분', '1시간', '4시간', '일봉', '주봉', '월봉'],
                index=6  # 기본값: 일봉
            )
            
            # 캔들 개수
            candle_count = st.slider("📊 캔들 개수", min_value=50, max_value=500, value=200, step=50)
            
            st.markdown("---")
            
            # 분석 도구 선택
            st.markdown("## 🛠️ 분석 도구")
            
            show_support_resistance = st.checkbox("🛡️ 지지선/저항선", value=True)
            show_volume_profile = st.checkbox("📊 거래량 프로파일", value=True)
            
            st.markdown("### 📈 기술적 지표")
            indicators = st.multiselect(
                "표시할 지표를 선택하세요",
                options=['MA5', 'MA20', 'MA60', 'MA120', '볼린저밴드', 'RSI'],
                default=['MA20', 'MA60', 'RSI']
            )
            
            # 새로고침 버튼
            if st.button("🔄 데이터 새로고침", type="primary"):
                st.cache_data.clear()
                st.rerun()
    
    # 메인 컨텐츠
    if coin_name:
        # 모바일에서는 세로 배치, 데스크톱에서는 가로 배치
        if is_mobile:
            # 모바일: 세로 배치
            with st.spinner("📊 데이터 분석 중..."):
                df = get_upbit_candles(market_code, interval, candle_count)
                
                if df.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                    return
                
                df = calculate_technical_indicators(df)
                
                support_levels, resistance_levels = [], []
                if show_support_resistance:
                    support_levels, resistance_levels = calculate_support_resistance(df)
                
                volume_profile_df = pd.DataFrame()
                if show_volume_profile:
                    volume_profile_df = calculate_volume_profile(df)
                
                buy_signals, sell_signals, nearest_support, nearest_resistance = calculate_trade_signals(
                    df, support_levels, resistance_levels, volume_profile_df
                )
            
            # 현재 가격 정보 (모바일용 간소화)
            current_price = df.iloc[-1]['trade_price']
            prev_price = df.iloc[-2]['trade_price'] if len(df) > 1 else current_price
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
            
            # 큰 글씨로 현재가 표시
            st.markdown(f"""
            <div style="text-align: center; background: #f8f9fa; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                <h1 style="margin: 0; color: #333;">{current_price:,.0f}원</h1>
                <h3 style="margin: 0; color: {'red' if price_change > 0 else 'blue'};">
                    {price_change:+.0f}원 ({price_change_pct:+.2f}%)
                </h3>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            # 데스크톱: 기존 레이아웃
            col1, col2, col3 = st.columns(3)
            
            with st.spinner("데이터를 분석하는 중..."):
                df = get_upbit_candles(market_code, interval, candle_count)
                
                if df.empty:
                    st.error("데이터를 불러올 수 없습니다.")
                    return
                
                df = calculate_technical_indicators(df)
                
                support_levels, resistance_levels = [], []
                if show_support_resistance:
                    support_levels, resistance_levels = calculate_support_resistance(df)
                
                volume_profile_df = pd.DataFrame()
                if show_volume_profile:
                    volume_profile_df = calculate_volume_profile(df)
                
                buy_signals, sell_signals, nearest_support, nearest_resistance = calculate_trade_signals(
                    df, support_levels, resistance_levels, volume_profile_df
                )
            
            # 현재 가격 정보
            current_price = df.iloc[-1]['trade_price']
            prev_price = df.iloc[-2]['trade_price'] if len(df) > 1 else current_price
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
            
            with col1:
                st.metric("현재가", f"{current_price:,.0f}원", f"{price_change:+.0f}원 ({price_change_pct:+.2f}%)")
            
            with col2:
                st.metric("24시간 거래량", f"{df.iloc[-1]['candle_acc_trade_volume']:,.0f}")
            
            with col3:
                if not df['RSI'].isna().iloc[-1]:
                    rsi_value = df['RSI'].iloc[-1]
                    rsi_status = "과매수" if rsi_value > 70 else "과매도" if rsi_value < 30 else "중립"
                    st.metric("RSI", f"{rsi_value:.1f}", rsi_status)
        
        # 메인 차트 (화면 크기에 따라 최적화)
        st.session_state['screen_width'] = 500 if is_mobile else 1200  # 임시 설정
        fig = create_main_chart(df, support_levels, resistance_levels, 
                               show_volume_profile, volume_profile_df, indicators)
        
        # 모바일에서는 차트를 더 크게 표시
        if is_mobile:
            st.plotly_chart(fig, use_container_width=True, config={
                'displayModeBar': False,  # 도구 모음 숨김
                'doubleClick': 'reset+autosize'  # 더블클릭으로 리셋
            })
        else:
            st.plotly_chart(fig, use_container_width=True)
        
        # 분석 정보 (모바일에서는 간소화)
        if is_mobile:
            # 모바일용 간소화된 정보
            if buy_signals and sell_signals:
                st.markdown("### 🎯 추천가")
                
                # 주요 추천가만 표시
                best_buy = min(buy_signals, key=lambda x: abs(x[1] - current_price))
                best_sell = min(sell_signals, key=lambda x: abs(x[1] - current_price))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    **💰 매수 추천**  
                    {best_buy[1]:,.0f}원  
                    ({best_buy[0]})
                import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 페이지 설정
st.set_page_config(
    page_title="업비트 차트 분석기",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="auto"  # 모바일에서 자동 조정
)

# CSS 스타일
st.markdown("""
<style>
    /* 모바일 최적화 스타일 */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .main-header h1 {
        color: white;
        text-align: center;
        margin: 0;
        font-size: 2.5rem;
    }
    
    /* 모바일에서 글자 크기 조정 */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.8rem !important;
        }
        .main-header p {
            font-size: 0.9rem !important;
        }
        
        /* 메트릭 카드 모바일 최적화 */
        .metric-card {
            font-size: 0.85rem !important;
            padding: 0.5rem !important;
        }
        
        /* 사이드바 숨기기 버튼 스타일 */
        .css-1d391kg {
            padding-top: 1rem;
        }
        
        /* 차트 컨테이너 최적화 */
        .stPlotlyChart {
            width: 100% !important;
            height: auto !important;
        }
        
        /* 버튼 크기 조정 */
        .stButton button {
            width: 100% !important;
            padding: 0.5rem !important;
        }
        
        /* 선택박스 최적화 */
        .stSelectbox {
            font-size: 0.9rem !important;
        }
        
        /* 멀티셀렉트 최적화 */
        .stMultiSelect {
            font-size: 0.85rem !important;
        }
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .analysis-section {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .stAlert > div {
        background-color: #d4edda;
        border-color: #c3e6cb;
        color: #155724;
    }
    
    /* 모바일 차트 최적화 */
    @media (max-width: 768px) {
        .js-plotly-plot {
            width: 100% !important;
            height: 400px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# 업비트 API 함수들
@st.cache_data(ttl=60)  # 1분 캐시
def get_upbit_tickers():
    """주요 암호화폐만 선별"""
    # 주요 암호화폐 직접 지정
    major_cryptos = {
        '비트코인': 'KRW-BTC',
        '이더리움': 'KRW-ETH', 
        '솔라나': 'KRW-SOL',
        'XRP': 'KRW-XRP',
        '에테나': 'KRW-ENA',
        '도지코인': 'KRW-DOGE',
        '바빌론': 'KRW-BABY'  # 바빌론 추가
    }
    return major_cryptos

@st.cache_data(ttl=60)
def get_upbit_candles(market, interval, count=200):
    """업비트 캔들 데이터 조회"""
    try:
        intervals = {
            '1분': 'minutes/1',
            '5분': 'minutes/5', 
            '15분': 'minutes/15',
            '30분': 'minutes/30',
            '1시간': 'minutes/60',
            '4시간': 'minutes/240',
            '일봉': 'days',
            '주봉': 'weeks',
            '월봉': 'months'
        }
        
        url = f"https://api.upbit.com/v1/candles/{intervals[interval]}"
        params = {'market': market, 'count': count}
        
        response = requests.get(url, params=params)
        data = response.json()
        
        df = pd.DataFrame(data)
        df['candle_date_time_kst'] = pd.to_datetime(df['candle_date_time_kst'])
        df = df.sort_values('candle_date_time_kst').reset_index(drop=True)
        
        return df
    except Exception as e:
        st.error(f"캔들 데이터를 가져오는데 실패했습니다: {e}")
        return pd.DataFrame()

def calculate_support_resistance(df, window=20):
    """지지선/저항선 계산 (개선된 버전)"""
    if len(df) < window:
        return [], []
    
    current_price = df.iloc[-1]['trade_price']
    
    # 피봇 포인트 계산
    highs = df['high_price'].rolling(window=window, center=True).max()
    lows = df['low_price'].rolling(window=window, center=True).min()
    
    resistance_levels = []
    support_levels = []
    
    for i in range(window, len(df) - window):
        if df.iloc[i]['high_price'] == highs.iloc[i]:
            resistance_levels.append(df.iloc[i]['high_price'])
        if df.iloc[i]['low_price'] == lows.iloc[i]:
            support_levels.append(df.iloc[i]['low_price'])
    
    # 이동평균선도 동적 지지/저항으로 추가
    if len(df) >= 20:
        ma20 = df['MA20'].iloc[-1]
        ma60 = df['MA60'].iloc[-1] if len(df) >= 60 else None
        
        if ma20 < current_price:
            support_levels.append(ma20)
        else:
            resistance_levels.append(ma20)
            
        if ma60:
            if ma60 < current_price:
                support_levels.append(ma60)
            else:
                resistance_levels.append(ma60)
    
    # 현재가 기준으로 올바른 지지/저항 분리
    support_levels = [level for level in support_levels if level < current_price]
    resistance_levels = [level for level in resistance_levels if level > current_price]
    
    # 중복 제거 및 정렬
    support_levels = sorted(list(set([round(x, -1) for x in support_levels])), reverse=True)[:10]
    resistance_levels = sorted(list(set([round(x, -1) for x in resistance_levels])))[:10]
    
    return support_levels, resistance_levels

def calculate_volume_profile(df, bins=50):
    """거래량 프로파일 계산"""
    if df.empty:
        return pd.DataFrame()
    
    min_price = df['low_price'].min()
    max_price = df['high_price'].max()
    price_bins = np.linspace(min_price, max_price, bins)
    
    volume_profile = []
    
    for i in range(len(price_bins) - 1):
        bin_low = price_bins[i]
        bin_high = price_bins[i + 1]
        bin_center = (bin_low + bin_high) / 2
        
        # 각 가격 구간에 해당하는 거래량 합계
        mask = (df['low_price'] <= bin_high) & (df['high_price'] >= bin_low)
        total_volume = df.loc[mask, 'candle_acc_trade_volume'].sum()
        
        volume_profile.append({
            'price': bin_center,
            'volume': total_volume,
            'price_range': f"{bin_low:.0f} - {bin_high:.0f}"
        })
    
    return pd.DataFrame(volume_profile)

def calculate_technical_indicators(df):
    """기술적 지표 계산"""
    if df.empty or len(df) < 20:
        return df
    
    # 이동평균선
    df['MA5'] = df['trade_price'].rolling(window=5).mean()
    df['MA20'] = df['trade_price'].rolling(window=20).mean()
    df['MA60'] = df['trade_price'].rolling(window=60).mean()
    df['MA120'] = df['trade_price'].rolling(window=120).mean()
    
    # RSI 계산
    delta = df['trade_price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 볼린저 밴드
    df['BB_middle'] = df['trade_price'].rolling(window=20).mean()
    bb_std = df['trade_price'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
    df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
    
    return df

def calculate_trade_signals(df, support_levels, resistance_levels, volume_profile_df):
    """매수/매도 신호 계산 (개선된 버전)"""
    if df.empty or len(df) < 20:
        return None, None, None, None
    
    current_price = df.iloc[-1]['trade_price']
    rsi = df['RSI'].iloc[-1] if not df['RSI'].isna().iloc[-1] else 50
    
    # 거래량 프로파일에서 POC (Point of Control) 찾기
    poc_price = None
    if not volume_profile_df.empty:
        poc_idx = volume_profile_df['volume'].idxmax()
        poc_price = volume_profile_df.iloc[poc_idx]['price']
        
        # POC가 현재가보다 아래면 지지선으로 추가
        if poc_price < current_price:
            support_levels.append(poc_price)
        elif poc_price > current_price:
            resistance_levels.append(poc_price)
    
    # 지지선/저항선 재정렬
    support_levels = sorted([s for s in support_levels if s < current_price], reverse=True)
    resistance_levels = sorted([r for r in resistance_levels if r > current_price])
    
    # 가장 가까운 지지선/저항선 찾기
    nearest_support = support_levels[0] if support_levels else current_price * 0.85
    nearest_resistance = resistance_levels[0] if resistance_levels else current_price * 1.15
    
    # 변동성 계산 (최근 20일 변동폭)
    recent_volatility = df['trade_price'].tail(20).std() / current_price
    volatility_factor = max(0.02, min(0.1, recent_volatility))  # 2%~10% 범위
    
    # 매수 추천가 계산
    buy_signals = []
    
    # 1. 강력한 지지선 근처 (가장 강력한 지지선 +2%)
    if support_levels:
        strong_support = support_levels[0]
        buy_price_1 = strong_support * 1.02
        confidence = "강력 추천" if current_price > strong_support * 1.1 else "추천"
        buy_signals.append(('강력 지지선', buy_price_1, confidence))
    
    # 2. POC 근처 (거래량 집중 구간)
    if poc_price and poc_price < current_price:
        buy_price_poc = poc_price * 1.01
        buy_signals.append(('POC 지지', buy_price_poc, '강력 추천'))
    
    # 3. 단기 매수 (현재가 기준)
    buy_price_2 = current_price * (1 - volatility_factor * 1.5)
    buy_signals.append(('단기 매수', buy_price_2, '추천'))
    
    # 4. RSI 기반 매수가
    if rsi < 30:  # 과매도
        buy_price_3 = current_price * 0.95
        buy_signals.append(('RSI 과매도', buy_price_3, '강력 추천'))
    elif rsi < 40:  # 중립 하단
        buy_price_3 = current_price * 0.97
        buy_signals.append(('RSI 약세', buy_price_3, '추천'))
    elif rsi < 50:
        buy_price_3 = current_price * 0.98
        buy_signals.append(('RSI 중립하', buy_price_3, '보통'))
    
    # 5. 이동평균선 지지
    if len(df) >= 20 and not df['MA20'].isna().iloc[-1]:
        ma20 = df['MA20'].iloc[-1]
        if ma20 < current_price:
            buy_signals.append(('MA20 지지', ma20 * 1.005, '추천'))
    
    # 매도 추천가 계산
    sell_signals = []
    
    # 1. 강력한 저항선 근처
    if resistance_levels:
        strong_resistance = resistance_levels[0]
        sell_price_1 = strong_resistance * 0.98
        confidence = "강력 추천" if current_price < strong_resistance * 0.9 else "추천"
        sell_signals.append(('강력 저항선', sell_price_1, confidence))
    
    # 2. POC 저항 근처
    if poc_price and poc_price > current_price:
        sell_price_poc = poc_price * 0.99
        sell_signals.append(('POC 저항', sell_price_poc, '강력 추천'))
    
    # 3. 단기 목표 (변동성 기반)
    target_profit = max(0.05, volatility_factor * 2)  # 최소 5% 목표
    sell_price_2 = current_price * (1 + target_profit)
    sell_signals.append(('단기 목표', sell_price_2, '추천'))
    
    # 4. RSI 기반 매도가
    if rsi > 70:  # 과매수
        sell_price_3 = current_price * 1.02
        sell_signals.append(('RSI 과매수', sell_price_3, '강력 추천'))
    elif rsi > 60:  # 중립 상단
        sell_price_3 = current_price * 1.04
        sell_signals.append(('RSI 강세', sell_price_3, '추천'))
    elif rsi > 50:
        sell_price_3 = current_price * 1.06
        sell_signals.append(('RSI 중립상', sell_price_3, '보통'))
    
    # 5. 중장기 목표 (피보나치 기반)
    if resistance_levels:
        fib_target = current_price + (resistance_levels[0] - current_price) * 0.618
        sell_signals.append(('피보나치 61.8%', fib_target, '보통'))
    
    # 중복 제거 및 정렬
    buy_signals = sorted(list(set(buy_signals)), key=lambda x: x[1], reverse=True)
    sell_signals = sorted(list(set(sell_signals)), key=lambda x: x[1])
    
    return buy_signals, sell_signals, nearest_support, nearest_resistance
    """기술적 지표 계산"""
    if df.empty or len(df) < 20:
        return df
    
    # 이동평균선
    df['MA5'] = df['trade_price'].rolling(window=5).mean()
    df['MA20'] = df['trade_price'].rolling(window=20).mean()
    df['MA60'] = df['trade_price'].rolling(window=60).mean()
    df['MA120'] = df['trade_price'].rolling(window=120).mean()
    
    # RSI 계산
    delta = df['trade_price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # 볼린저 밴드
    df['BB_middle'] = df['trade_price'].rolling(window=20).mean()
    bb_std = df['trade_price'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
    df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
    
    return df

def create_main_chart(df, support_levels, resistance_levels, show_volume_profile, volume_profile_df, indicators):
    """메인 차트 생성 (모바일 최적화)"""
    
    # 모바일 감지 (JavaScript를 통한 화면 크기 감지)
    is_mobile = st.session_state.get('is_mobile', False)
    
    # 모바일용 차트 설정
    if st.session_state.get('screen_width', 1200) < 768:
        # 모바일: 단순화된 레이아웃
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            specs=[[{"secondary_y": False}],
                   [{"secondary_y": False}]],
            subplot_titles=('📈 가격 차트', '📊 거래량'),
            vertical_spacing=0.1
        )
        chart_height = 500
        show_volume_profile = False  # 모바일에서는 거래량 프로파일 숨김
    else:
        # 데스크톱: 전체 레이아웃
        fig = make_subplots(
            rows=3, cols=2,
            row_heights=[0.6, 0.2, 0.2],
            column_widths=[0.8, 0.2],
            specs=[[{"secondary_y": False}, {"type": "bar"}],
                   [{"secondary_y": False}, None],
                   [{"secondary_y": False}, None]],
            subplot_titles=('가격 차트', '거래량 프로파일', '거래량', '', 'RSI', ''),
            vertical_spacing=0.05,
            horizontal_spacing=0.05
        )
        chart_height = 800
    
    # 캔들스틱 차트
    fig.add_trace(
        go.Candlestick(
            x=df['candle_date_time_kst'],
            open=df['opening_price'],
            high=df['high_price'],
            low=df['low_price'],
            close=df['trade_price'],
            name="캔들스틱",
            increasing_line_color='#ff6b6b',
            decreasing_line_color='#4ecdc4'
        ),
        row=1, col=1
    )
    
    # 이동평균선 (모바일에서는 개수 제한)
    mobile_indicators = ['MA20'] if st.session_state.get('screen_width', 1200) < 768 else indicators
    
    if 'MA5' in mobile_indicators:
        fig.add_trace(
            go.Scatter(x=df['candle_date_time_kst'], y=df['MA5'], 
                      name='MA5', line=dict(color='orange', width=1)),
            row=1, col=1
        )
    if 'MA20' in mobile_indicators:
        fig.add_trace(
            go.Scatter(x=df['candle_date_time_kst'], y=df['MA20'], 
                      name='MA20', line=dict(color='blue', width=2)),
            row=1, col=1
        )
    if 'MA60' in mobile_indicators and st.session_state.get('screen_width', 1200) >= 768:
        fig.add_trace(
            go.Scatter(x=df['candle_date_time_kst'], y=df['MA60'], 
                      name='MA60', line=dict(color='purple', width=1)),
            row=1, col=1
        )
    
    # 볼린저 밴드 (데스크톱만)
    if '볼린저밴드' in indicators and st.session_state.get('screen_width', 1200) >= 768:
        fig.add_trace(
            go.Scatter(x=df['candle_date_time_kst'], y=df['BB_upper'], 
                      name='BB Upper', line=dict(color='gray', width=1, dash='dash')),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['candle_date_time_kst'], y=df['BB_lower'], 
                      name='BB Lower', line=dict(color='gray', width=1, dash='dash')),
            row=1, col=1
        )
    
    # 지지선/저항선 (개수 제한)
    max_lines = 3 if st.session_state.get('screen_width', 1200) < 768 else 5
    
    if support_levels:
        for level in support_levels[:max_lines]:
            fig.add_hline(y=level, line_dash="dash", line_color="green", 
                         annotation_text=f"지지: {level:,.0f}", row=1, col=1)
    
    if resistance_levels:
        for level in resistance_levels[:max_lines]:
            fig.add_hline(y=level, line_dash="dash", line_color="red", 
                         annotation_text=f"저항: {level:,.0f}", row=1, col=1)
    
    # 거래량 프로파일 (데스크톱만)
    if show_volume_profile and not volume_profile_df.empty and st.session_state.get('screen_width', 1200) >= 768:
        fig.add_trace(
            go.Bar(
                y=volume_profile_df['price'],
                x=volume_profile_df['volume'],
                orientation='h',
                name='거래량 프로파일',
                marker_color='rgba(102, 126, 234, 0.6)',
                hovertemplate='가격: %{y:,.0f}<br>거래량: %{x:,.0f}<extra></extra>'
            ),
            row=1, col=2
        )
    
    # 거래량 차트
    colors = ['red' if row['opening_price'] > row['trade_price'] else 'blue' for _, row in df.iterrows()]
    volume_row = 2 if st.session_state.get('screen_width', 1200) < 768 else 2
    fig.add_trace(
        go.Bar(x=df['candle_date_time_kst'], y=df['candle_acc_trade_volume'],
               name='거래량', marker_color=colors),
        row=volume_row, col=1
    )
    
    # RSI (데스크톱만)
    if not df['RSI'].isna().all() and st.session_state.get('screen_width', 1200) >= 768:
        fig.add_trace(
            go.Scatter(x=df['candle_date_time_kst'], y=df['RSI'], 
                      name='RSI', line=dict(color='purple')),
            row=3, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    # 레이아웃 설정
    fig.update_layout(
        title="📊 업비트 차트 분석",
        xaxis_rangeslider_visible=False,
        height=chart_height,
        showlegend=True,
        template="plotly_white",
        # 모바일 최적화
        margin=dict(l=20, r=20, t=50, b=20) if st.session_state.get('screen_width', 1200) < 768 else dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

# 메인 애플리케이션
def main():
    # 헤더
    st.markdown("""
    <div class="main-header">
        <h1>📊 업비트 차트 분석기</h1>
        <p style="text-align: center; color: white; margin: 0;">실시간 업비트 데이터로 전문가급 차트 분석</p>
    </div>
    """, unsafe_allow_html=True)
    
            # 사이드바
    with st.sidebar:
        st.markdown("## ⚙️ 분석 설정")
        
        # 주요 암호화폐 선택
        tickers = get_upbit_tickers()
        
        # 종목 선택
        coin_name = st.selectbox(
            "📈 분석할 종목을 선택하세요",
            options=list(tickers.keys()),
            index=0
        )
        
        if coin_name:
            market_code = tickers[coin_name]
            st.success(f"선택된 종목: {market_code}")
        
        # 시간 간격 선택
        interval = st.selectbox(
            "⏰ 차트 간격",
            options=['1분', '5분', '15분', '30분', '1시간', '4시간', '일봉', '주봉', '월봉'],
            index=6  # 기본값: 일봉
        )
        
        # 캔들 개수
        candle_count = st.slider("📊 캔들 개수", min_value=50, max_value=500, value=200, step=50)
        
        st.markdown("---")
        
        # 분석 도구 선택
        st.markdown("## 🛠️ 분석 도구")
        
        show_support_resistance = st.checkbox("🛡️ 지지선/저항선", value=True)
        show_volume_profile = st.checkbox("📊 거래량 프로파일", value=True)
        
        st.markdown("### 📈 기술적 지표")
        indicators = st.multiselect(
            "표시할 지표를 선택하세요",
            options=['MA5', 'MA20', 'MA60', 'MA120', '볼린저밴드', 'RSI'],
            default=['MA20', 'MA60', 'RSI']
        )
        
        # 새로고침 버튼
        if st.button("🔄 데이터 새로고침", type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    # 메인 컨텐츠
    if coin_name:
        col1, col2, col3 = st.columns(3)
        
        with st.spinner("데이터를 분석하는 중..."):
            # 데이터 로드
            df = get_upbit_candles(market_code, interval, candle_count)
            
            if df.empty:
                st.error("데이터를 불러올 수 없습니다.")
                return
            
            # 기술적 지표 계산
            df = calculate_technical_indicators(df)
            
            # 지지선/저항선 계산
            support_levels, resistance_levels = [], []
            if show_support_resistance:
                support_levels, resistance_levels = calculate_support_resistance(df)
            
            # 거래량 프로파일 계산
            volume_profile_df = pd.DataFrame()
            if show_volume_profile:
                volume_profile_df = calculate_volume_profile(df)
            
            # 매매 신호 계산
            buy_signals, sell_signals, nearest_support, nearest_resistance = calculate_trade_signals(
                df, support_levels, resistance_levels, volume_profile_df
            )
        
        # 현재 가격 정보
        current_price = df.iloc[-1]['trade_price']
        prev_price = df.iloc[-2]['trade_price'] if len(df) > 1 else current_price
        price_change = current_price - prev_price
        price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
        
        with col1:
            st.metric("현재가", f"{current_price:,.0f}원", f"{price_change:+.0f}원 ({price_change_pct:+.2f}%)")
        
        with col2:
            st.metric("24시간 거래량", f"{df.iloc[-1]['candle_acc_trade_volume']:,.0f}")
        
        with col3:
            if not df['RSI'].isna().iloc[-1]:
                rsi_value = df['RSI'].iloc[-1]
                rsi_status = "과매수" if rsi_value > 70 else "과매도" if rsi_value < 30 else "중립"
                st.metric("RSI", f"{rsi_value:.1f}", rsi_status)
        
        # 메인 차트
        fig = create_main_chart(df, support_levels, resistance_levels, 
                               show_volume_profile, volume_profile_df, indicators)
        st.plotly_chart(fig, use_container_width=True)
        
        # 분석 정보
        col1, col2 = st.columns(2)
        
        with col1:
            if support_levels:
                st.markdown("### 🛡️ 주요 지지선")
                for i, level in enumerate(support_levels[:5]):
                    distance = ((current_price - level) / current_price) * 100  # 수정된 계산
                    st.markdown(f"**{i+1}.** {level:,.0f}원 (현재가 대비 -{distance:.2f}%)")
            else:
                st.markdown("### 🛡️ 주요 지지선")
                st.markdown("지지선을 찾을 수 없습니다.")
        
        with col2:
            if resistance_levels:
                st.markdown("### 🎯 주요 저항선")
                for i, level in enumerate(resistance_levels[:5]):
                    distance = ((level - current_price) / current_price) * 100  # 수정된 계산
                    st.markdown(f"**{i+1}.** {level:,.0f}원 (현재가 대비 +{distance:.2f}%)")
            else:
                st.markdown("### 🎯 주요 저항선")
                st.markdown("저항선을 찾을 수 없습니다.")
        
        # 거래량 프로파일 정보
        if show_volume_profile and not volume_profile_df.empty:
            st.markdown("### 📊 거래량 분석")
            
            # POC (Point of Control) 찾기
            poc_idx = volume_profile_df['volume'].idxmax()
            poc_price = volume_profile_df.iloc[poc_idx]['price']
            poc_volume = volume_profile_df.iloc[poc_idx]['volume']
            
            st.info(f"🎯 **POC (최대 거래량 가격)**: {poc_price:,.0f}원 (거래량: {poc_volume:,.0f})")
            
            # 상위 거래량 구간
            top_volumes = volume_profile_df.nlargest(3, 'volume')
            st.markdown("**📈 거래량 상위 3구간:**")
            for i, row in top_volumes.iterrows():
                st.markdown(f"- {row['price']:,.0f}원: {row['volume']:,.0f}")
        
        # 분석 요약
        st.markdown("### 📋 분석 요약")
        analysis_text = []
        
        if not df['RSI'].isna().iloc[-1]:
            rsi = df['RSI'].iloc[-1]
            if rsi > 70:
                analysis_text.append("🔴 RSI가 70을 초과하여 과매수 상태입니다.")
            elif rsi < 30:
                analysis_text.append("🟢 RSI가 30 미만으로 과매도 상태입니다.")
            else:
                analysis_text.append("🟡 RSI가 중립 구간에 있습니다.")
        
        if support_levels:
            nearest_support = min(support_levels, key=lambda x: abs(x - current_price))
            support_distance = ((current_price - nearest_support) / nearest_support) * 100
            analysis_text.append(f"🛡️ 가장 가까운 지지선: {nearest_support:,.0f}원 ({support_distance:+.2f}%)")
        
        if resistance_levels:
            nearest_resistance = min(resistance_levels, key=lambda x: abs(x - current_price))
            resistance_distance = ((nearest_resistance - current_price) / current_price) * 100
            analysis_text.append(f"🎯 가장 가까운 저항선: {nearest_resistance:,.0f}원 (+{resistance_distance:.2f}%)")
        
        for text in analysis_text:
            st.markdown(f"- {text}")
        
        # 데이터 테이블 (선택사항)
        with st.expander("📊 원시 데이터 보기"):
            display_df = df[['candle_date_time_kst', 'opening_price', 'high_price', 
                           'low_price', 'trade_price', 'candle_acc_trade_volume']].copy()
            display_df.columns = ['시간', '시가', '고가', '저가', '종가', '거래량']
            st.dataframe(display_df.tail(20), use_container_width=True)
        
        # 🎯 매매 추천 시스템
        st.markdown("---")
        st.markdown("## 🎯 AI 매매 추천 시스템")
        
        if buy_signals and sell_signals:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 💰 추천 매수가")
                for i, (reason, price, strength) in enumerate(buy_signals[:3]):
                    percentage = ((current_price - price) / current_price) * 100
                    
                    # 추천도에 따른 색상
                    if strength == '강력 추천':
                        color = "🟢"
                        bg_color = "#d4edda"
                    elif strength == '추천':
                        color = "🟡"
                        bg_color = "#fff3cd"
                    else:
                        color = "🔵"
                        bg_color = "#d1ecf1"
                    
                    st.markdown(f"""
                    <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin: 5px 0;">
                        <strong>{color} {reason}</strong><br>
                        매수가: <strong>{price:,.0f}원</strong><br>
                        현재가 대비: <strong>{percentage:+.2f}%</strong><br>
                        추천도: <strong>{strength}</strong>
                    </div>
                    """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("### 💸 추천 매도가")
                for i, (reason, price, strength) in enumerate(sell_signals[:3]):
                    percentage = ((price - current_price) / current_price) * 100
                    
                    # 추천도에 따른 색상
                    if strength == '강력 추천':
                        color = "🔴"
                        bg_color = "#f8d7da"
                    elif strength == '추천':
                        color = "🟠"
                        bg_color = "#ffeaa7"
                    else:
                        color = "🔵"
                        bg_color = "#d1ecf1"
                    
                    st.markdown(f"""
                    <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin: 5px 0;">
                        <strong>{color} {reason}</strong><br>
                        매도가: <strong>{price:,.0f}원</strong><br>
                        수익률: <strong>+{percentage:.2f}%</strong><br>
                        추천도: <strong>{strength}</strong>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 종합 추천
            st.markdown("### 🧠 AI 종합 분석")
            
            # RSI 기반 추천
            if not df['RSI'].isna().iloc[-1]:
                rsi = df['RSI'].iloc[-1]
                if rsi < 30:
                    st.success("🟢 **강력 매수 신호**: RSI가 과매도 구간입니다. 단계적 매수를 고려하세요.")
                elif rsi > 70:
                    st.error("🔴 **매도 신호**: RSI가 과매수 구간입니다. 수익 실현을 고려하세요.")
                elif 30 <= rsi <= 50:
                    st.info("🟡 **중립-매수**: RSI가 중립 하단입니다. 지지선 근처에서 매수 고려.")
                else:
                    st.warning("🟠 **중립-매도**: RSI가 중립 상단입니다. 저항선 근처에서 매도 고려.")
            
            # 지지선/저항선 기반 추천
            if nearest_support and nearest_resistance:
                support_distance = ((current_price - nearest_support) / current_price) * 100
                resistance_distance = ((nearest_resistance - current_price) / current_price) * 100
                
                if support_distance < 5:
                    st.success(f"🛡️ **지지선 근처**: 현재가가 지지선({nearest_support:,.0f}원)에서 {support_distance:.1f}% 위에 있습니다. 매수 기회!")
                elif resistance_distance < 5:
                    st.error(f"🎯 **저항선 근처**: 현재가가 저항선({nearest_resistance:,.0f}원)에서 {resistance_distance:.1f}% 아래에 있습니다. 매도 고려!")
                else:
                    st.info(f"📊 **중간 구간**: 지지선까지 -{support_distance:.1f}%, 저항선까지 +{resistance_distance:.1f}% 거리입니다.")
            
            # 리스크 관리 조언
            st.markdown("### ⚠️ 리스크 관리")
            st.markdown(f"""
            - **손절선**: {current_price * 0.95:,.0f}원 (-5%) 이하에서 손절 고려
            - **분할매수**: 추천 매수가에서 3-4회 나누어 매수
            - **수익실현**: 목표가 도달 시 50% 이상 수익실현 권장
            - **변동성 주의**: 암호화폐는 높은 변동성을 가지므로 소액으로 시작하세요
            """)
        
        else:
            st.warning("매매 신호를 계산하기에 데이터가 부족합니다. 더 많은 캔들 데이터가 필요합니다.")

if __name__ == "__main__":
    main()

# 사용법 안내
st.markdown("---")
st.markdown("""
### 💡 사용법 가이드

1. **종목 선택**: 좌측 사이드바에서 분석하고 싶은 암호화폐를 선택하세요.
2. **시간 간격**: 1분봉부터 월봉까지 다양한 시간대로 분석 가능합니다.
3. **분석 도구**: 지지선/저항선, 거래량 프로파일, 각종 기술적 지표를 선택할 수 있습니다.
4. **실시간 업데이트**: '데이터 새로고침' 버튼으로 최신 데이터를 불러올 수 있습니다.

### 🚀 주요 기능

- **📊 거래량 프로파일**: 가격대별 거래량 분포를 시각화
- **🛡️ 지지선/저항선**: 자동으로 계산된 주요 지지/저항 구간
- **📈 기술적 지표**: 이동평균선, RSI, 볼린저밴드 등
- **🎯 POC 분석**: 최대 거래량이 발생한 가격대 표시
- **📋 종합 분석**: RSI 상태, 지지/저항 거리 등 핵심 정보 요약

**🔄 데이터는 1분마다 자동 캐시되어 API 호출을 최적화합니다.**
""")
