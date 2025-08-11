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
    initial_sidebar_state="expanded"
)

# 모바일 반응형 CSS 스타일
st.markdown("""
<style>
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
    
    /* 모바일 반응형 스타일 */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.8rem;
        }
        .stMetric {
            margin-bottom: 1rem;
        }
        .metric-row {
            flex-direction: column;
        }
        .mobile-signal-box {
            margin-bottom: 1rem;
            padding: 0.8rem;
        }
        /* 플롯 차트 모바일 최적화 */
        .js-plotly-plot {
            width: 100% !important;
        }
        .plotly {
            width: 100% !important;
        }
    }
    
    /* 신호 박스 스타일 */
    .signal-box {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
        border-left: 4px solid #667eea;
    }
    
    .buy-signal {
        background-color: #d4edda;
        border-left-color: #28a745;
    }
    
    .sell-signal {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }
    
    .neutral-signal {
        background-color: #d1ecf1;
        border-left-color: #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

# 디바이스 감지 함수
def is_mobile():
    """모바일 디바이스 감지 (간단한 방법)"""
    try:
        # streamlit session state에 모바일 여부 저장
        if 'is_mobile' not in st.session_state:
            st.session_state.is_mobile = False
        return st.session_state.is_mobile
    except:
        return False

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

def create_mobile_chart(df, support_levels, resistance_levels, show_volume_profile, volume_profile_df, indicators):
    """모바일 최적화 차트 생성 (단순화된 레이아웃)"""
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.7, 0.3],
        specs=[[{"secondary_y": False}],
               [{"secondary_y": False}]],
        subplot_titles=('가격 차트', '거래량'),
        vertical_spacing=0.1
    )
    
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
    
    # 이동평균선 (모바일에서는 주요한 것만)
    if 'MA20' in indicators:
        fig.add_trace(
            go.Scatter(x=df['candle_date_time_kst'], y=df['MA20'], 
                      name='MA20', line=dict(color='blue', width=2)),
            row=1, col=1
        )
    if 'MA60' in indicators:
        fig.add_trace(
            go.Scatter(x=df['candle_date_time_kst'], y=df['MA60'], 
                      name='MA60', line=dict(color='purple', width=2)),
            row=1, col=1
        )
    
    # 지지선/저항선 (주요한 것만)
    if support_levels:
        level = support_levels[0]  # 가장 강한 지지선만
        fig.add_hline(y=level, line_dash="dash", line_color="green", 
                     annotation_text=f"지지: {level:,.0f}", row=1, col=1)
    
    if resistance_levels:
        level = resistance_levels[0]  # 가장 강한 저항선만
        fig.add_hline(y=level, line_dash="dash", line_color="red", 
                     annotation_text=f"저항: {level:,.0f}", row=1, col=1)
    
    # 거래량 차트
    colors = ['red' if row['opening_price'] > row['trade_price'] else 'blue' for _, row in df.iterrows()]
    fig.add_trace(
        go.Bar(x=df['candle_date_time_kst'], y=df['candle_acc_trade_volume'],
               name='거래량', marker_color=colors),
        row=2, col=1
    )
    
    # 레이아웃 설정 (모바일 최적화)
    fig.update_layout(
        title="업비트 차트 분석",
        xaxis_rangeslider_visible=False,
        height=600,  # 모바일에 맞게 높이 조정
        showlegend=False,  # 범례 숨김으로 공간 확보
        template="plotly_white",
        margin=dict(l=20, r=20, t=50, b=20)  # 여백 최소화
    )
    
    return fig

def create_main_chart(df, support_levels, resistance_levels, show_volume_profile, volume_profile_df, indicators):
    """데스크탑용 메인 차트 생성"""
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
    
    # 이동평균선
    if 'MA5' in indicators:
        fig.add_trace(
            go.Scatter(x=df['candle_date_time_kst'], y=df['MA5'], 
                      name='MA5', line=dict(color='orange', width=1)),
            row=1, col=1
        )
    if 'MA20' in indicators:
        fig.add_trace(
            go.Scatter(x=df['candle_date_time_kst'], y=df['MA20'], 
                      name='MA20', line=dict(color='blue', width=1)),
            row=1, col=1
        )
    if 'MA60' in indicators:
        fig.add_trace(
            go.Scatter(x=df['candle_date_time_kst'], y=df['MA60'], 
                      name='MA60', line=dict(color='purple', width=1)),
            row=1, col=1
        )
    
    # 볼린저 밴드
    if '볼린저밴드' in indicators:
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
    
    # 지지선/저항선
    if support_levels:
        for level in support_levels[-5:]:  # 최근 5개만
            fig.add_hline(y=level, line_dash="dash", line_color="green", 
                         annotation_text=f"지지: {level:,.0f}", row=1, col=1)
    
    if resistance_levels:
        for level in resistance_levels[-5:]:  # 최근 5개만
            fig.add_hline(y=level, line_dash="dash", line_color="red", 
                         annotation_text=f"저항: {level:,.0f}", row=1, col=1)
    
    # 거래량 프로파일
    if show_volume_profile and not volume_profile_df.empty:
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
    fig.add_trace(
        go.Bar(x=df['candle_date_time_kst'], y=df['candle_acc_trade_volume'],
               name='거래량', marker_color=colors),
        row=2, col=1
    )
    
    # RSI
    if not df['RSI'].isna().all():
        fig.add_trace(
            go.Scatter(x=df['candle_date_time_kst'], y=df['RSI'], 
                      name='RSI', line=dict(color='purple')),
            row=3, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    # 레이아웃 설정
    fig.update_layout(
        title="업비트 차트 분석",
        xaxis_rangeslider_visible=False,
        height=800,
        showlegend=True,
        template="plotly_white"
    )
    
    return fig

# 모바일 매매 신호 표시 함수
def display_mobile_signals(buy_signals, sell_signals, current_price):
    """모바일용 매매 신호 표시"""
    st.markdown("## 🎯 매매 추천")
    
    # 탭으로 구분하여 공간 절약
    tab1, tab2 = st.tabs(["💰 매수", "💸 매도"])
    
    with tab1:
        if buy_signals:
            for i, (reason, price, strength) in enumerate(buy_signals[:2]):  # 모바일에서는 2개만
                percentage = ((current_price - price) / current_price) * 100
                
                if strength == '강력 추천':
                    color = "🟢"
                    bg_class = "buy-signal"
                elif strength == '추천':
                    color = "🟡"
                    bg_class = "signal-box"
                else:
                    color = "🔵"
                    bg_class = "neutral-signal"
                
                st.markdown(f"""
                <div class="signal-box {bg_class}">
                    <strong>{color} {reason}</strong><br>
                    매수가: <strong>{price:,.0f}원</strong><br>
                    현재가 대비: <strong>{percentage:+.2f}%</strong><br>
                    추천도: <strong>{strength}</strong>
                </div>
                """, unsafe_allow_html=True)
    
    with tab2:
        if sell_signals:
            for i, (reason, price, strength) in enumerate(sell_signals[:2]):  # 모바일에서는 2개만
                percentage = ((price - current_price) / current_price) * 100
                
                if strength == '강력 추천':
                    color = "🔴"
                    bg_class = "sell-signal"
                elif strength == '추천':
                    color = "🟠"
                    bg_class = "signal-box"
                else:
                    color = "🔵"
                    bg_class = "neutral-signal"
                
                st.markdown(f"""
                <div class="signal-box {bg_class}">
                    <strong>{color} {reason}</strong><br>
                    매도가: <strong>{price:,.0f}원</strong><br>
                    수익률: <strong>+{percentage:.2f}%</strong><br>
                    추천도: <strong>{strength}</strong>
                </div>
                """, unsafe_allow_html=True)

# 메인 애플리케이션
def main():
    # 모바일 감지 토글 (개발용)
    mobile_mode = st.sidebar.checkbox("📱 모바일 모드", value=False)
    
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
        show_volume_profile = st.checkbox("📊 거래량 프로파일", value=not mobile_mode)  # 모바일에서는 기본 비활성화
        
        st.markdown("### 📈 기술적 지표")
        default_indicators = ['MA20', 'RSI'] if mobile_mode else ['MA20', 'MA60', 'RSI']
        indicators = st.multiselect(
            "표시할 지표를 선택하세요",
            options=['MA5', 'MA20', 'MA60', 'MA120', '볼린저밴드', 'RSI'],
            default=default_indicators
        )
        
        # 새로고침 버튼
        if st.button("🔄 데이터 새로고침", type="primary"):
            st.cache_data.clear()
            st.rerun()
    
    # 메인 컨텐츠
    if coin_name:
        # 모바일 모드에 따른 레이아웃 조정
        if mobile_mode:
            # 모바일: 세로 배치
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
            
            # 현재 가격 정보 (모바일용 세로 배치)
            current_price = df.iloc[-1]['trade_price']
            prev_price = df.iloc[-2]['trade_price'] if len(df) > 1 else current_price
            price_change = current_price - prev_price
            price_change_pct = (price_change / prev_price) * 100 if prev_price != 0 else 0
            
            st.metric("현재가", f"{current_price:,.0f}원", f"{price_change:+.0f}원 ({price_change_pct:+.2f}%)")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("거래량", f"{df.iloc[-1]['candle_acc_trade_volume']:,.0f}")
            with col2:
                if not df['RSI'].isna().iloc[-1]:
                    rsi_value = df['RSI'].iloc[-1]
                    rsi_status = "과매수" if rsi_value > 70 else "과매도" if rsi_value < 30 else "중립"
                    st.metric("RSI", f"{rsi_value:.1f}", rsi_status)
            
            # 모바일 차트
            fig = create_mobile_chart(df, support_levels, resistance_levels, 
                                    show_volume_profile, volume_profile_df, indicators)
            st.plotly_chart(fig, use_container_width=True)
            
            # 모바일용 매매 신호
            if buy_signals and sell_signals:
                display_mobile_signals(buy_signals, sell_signals, current_price)
            
            # 간단한 분석 요약 (모바일용)
            with st.expander("📋 분석 요약"):
                analysis_text = []
                
                if not df['RSI'].isna().iloc[-1]:
                    rsi = df['RSI'].iloc[-1]
                    if rsi > 70:
                        analysis_text.append("🔴 RSI 과매수 상태")
                    elif rsi < 30:
                        analysis_text.append("🟢 RSI 과매도 상태")
                    else:
                        analysis_text.append("🟡 RSI 중립 구간")
                
                if support_levels:
                    nearest_support = min(support_levels, key=lambda x: abs(x - current_price))
                    support_distance = ((current_price - nearest_support) / nearest_support) * 100
                    analysis_text.append(f"🛡️ 지지선: {nearest_support:,.0f}원 ({support_distance:+.1f}%)")
                
                if resistance_levels:
                    nearest_resistance = min(resistance_levels, key=lambda x: abs(x - current_price))
                    resistance_distance = ((nearest_resistance - current_price) / current_price) * 100
                    analysis_text.append(f"🎯 저항선: {nearest_resistance:,.0f}원 (+{resistance_distance:.1f}%)")
                
                for text in analysis_text:
                    st.markdown(f"- {text}")
        
        else:
            # 데스크탑: 기존 레이아웃
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
                        distance = ((current_price - level) / current_price) * 100
                        st.markdown(f"**{i+1}.** {level:,.0f}원 (현재가 대비 -{distance:.2f}%)")
                else:
                    st.markdown("### 🛡️ 주요 지지선")
                    st.markdown("지지선을 찾을 수 없습니다.")
            
            with col2:
                if resistance_levels:
                    st.markdown("### 🎯 주요 저항선")
                    for i, level in enumerate(resistance_levels[:5]):
                        distance = ((level - current_price) / current_price) * 100
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
            
            # 🎯 매매 추천 시스템 (데스크탑 버전)
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
            
            # 데이터 테이블 (데스크탑에서만)
            with st.expander("📊 원시 데이터 보기"):
                display_df = df[['candle_date_time_kst', 'opening_price', 'high_price', 
                               'low_price', 'trade_price', 'candle_acc_trade_volume']].copy()
                display_df.columns = ['시간', '시가', '고가', '저가', '종가', '거래량']
                st.dataframe(display_df.tail(20), use_container_width=True)

if __name__ == "__main__":
    main()

# 사용법 안내
st.markdown("---")
if st.sidebar.checkbox("📱 모바일 모드", value=False):
    st.markdown("""
    ### 📱 모바일 최적화 모드
    
    - **간소화된 차트**: 핵심 정보만 표시
    - **세로 배치**: 모바일 화면에 최적화된 레이아웃
    - **탭 방식**: 매수/매도 신호를 탭으로 구분
    - **터치 친화적**: 버튼과 요소들이 터치하기 쉽게 배치
    """)
else:
    st.markdown("""
    ### 💡 사용법 가이드

    1. **종목 선택**: 좌측 사이드바에서 분석하고 싶은 암호화폐를 선택하세요.
    2. **시간 간격**: 1분봉부터 월봉까지 다양한 시간대로 분석 가능합니다.
    3. **분석 도구**: 지지선/저항선, 거래량 프로파일, 각종 기술적 지표를 선택할 수 있습니다.
    4. **실시간 업데이트**: '데이터 새로고침' 버튼으로 최신 데이터를 불러올 수 있습니다.
    5. **모바일 모드**: 좌측 사이드바에서 모바일 모드를 활성화하여 모바일 최적화 화면을 확인할 수 있습니다.

    ### 🚀 주요 기능

    - **📊 거래량 프로파일**: 가격대별 거래량 분포를 시각화
    - **🛡️ 지지선/저항선**: 자동으로 계산된 주요 지지/저항 구간
    - **📈 기술적 지표**: 이동평균선, RSI, 볼린저밴드 등
    - **🎯 POC 분석**: 최대 거래량이 발생한 가격대 표시
    - **📋 종합 분석**: RSI 상태, 지지/저항 거리 등 핵심 정보 요약
    - **📱 반응형 디자인**: 데스크탑과 모바일 모두 최적화

    **🔄 데이터는 1분마다 자동 캐시되어 API 호출을 최적화합니다.**
    """)
