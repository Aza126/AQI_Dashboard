import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. CẤU HÌNH TRANG WEB (Bám sát thiết kế)
# ==========================================
st.set_page_config(page_title="AQI Dashboard", layout="wide", page_icon="🌍")

# Từ điển Tọa độ để vẽ Bản đồ (Do file CSV đã lọc bỏ lat/lon)
LOCATIONS = {
    "Hà Nội": {"lat": 21.0285, "lon": 105.8542}, "Hải Phòng": {"lat": 20.8449, "lon": 106.6881},
    "Quảng Ninh": {"lat": 20.9510, "lon": 107.0730}, "Lào Cai": {"lat": 22.4800, "lon": 103.9750},
    "Đà Nẵng": {"lat": 16.0544, "lon": 108.2022}, "Huế": {"lat": 16.4637, "lon": 107.5909},
    "Quảng Nam": {"lat": 15.5394, "lon": 108.0191}, "Khánh Hòa": {"lat": 12.2388, "lon": 109.1967},
    "TP.HCM": {"lat": 10.8231, "lon": 106.6297}, "Bình Dương": {"lat": 11.3254, "lon": 106.4770},
    "Cần Thơ": {"lat": 10.0452, "lon": 105.7469}, "Kiên Giang": {"lat": 10.0125, "lon": 105.0809}
}

# ==========================================
# 2. HÀM XỬ LÝ DỮ LIỆU CỐT LÕI
# ==========================================
@st.cache_data(ttl=60) # Tự động làm mới cache mỗi 60 giây
def load_data():
    try:
        df = pd.read_csv("processed_aqi_data.csv")
        df['time'] = pd.to_datetime(df['time'])
        # Ghép tọa độ vào DataFrame để vẽ map
        df['lat'] = df['Tỉnh'].map(lambda x: LOCATIONS.get(x, {}).get('lat'))
        df['lon'] = df['Tỉnh'].map(lambda x: LOCATIONS.get(x, {}).get('lon'))
        return df
    except FileNotFoundError:
        return None

def get_aqi_status(aqi):
    if pd.isna(aqi): return "Chưa có dữ liệu", "gray"
    if aqi <= 50: return "Tốt", "#00e400"
    elif aqi <= 100: return "Trung bình", "#ffff00"
    elif aqi <= 150: return "Kém", "#ff7e00"
    elif aqi <= 200: return "Xấu", "#ff0000"
    elif aqi <= 300: return "Rất xấu", "#8f3f97"
    else: return "Nguy hại", "#7e0023"

# Load dữ liệu
df = load_data()

if df is None or df.empty:
    st.error("❌ Chưa tìm thấy dữ liệu. Hãy đảm bảo Kịch bản 1 và 2 đã chạy để tạo file 'processed_aqi_data.csv'.")
    st.stop()

# Lấy dữ liệu mới nhất của mỗi tỉnh (Dùng cho Bản đồ và Bảng xếp hạng)
df_latest = df.sort_values('time').groupby('Tỉnh').tail(1).reset_index(drop=True)

# ==========================================
# 3. HEADER & TIPS (Top Bar)
# ==========================================
col_title, col_tips = st.columns([1, 3])
with col_title:
    st.markdown("### 🌍 AQI Dashboard")
with col_tips:
    st.info("💡 **Tips:** Đeo khẩu trang N95 khi chỉ số AQI vượt quá 150 (Mức Xấu). Hạn chế mở cửa sổ vào lúc sáng sớm nếu sương mù dày đặc.")

# ==========================================
# 4. GIAO DIỆN CHÍNH (Chia cột Sidebar và Main)
# ==========================================
# st.sidebar nằm bên trái, Main Area nằm bên phải
st.sidebar.markdown("### 📍 Bảng Điều Khiển")
selected_city = st.sidebar.selectbox("🔍 Search (Chọn Tỉnh)", LOCATIONS.keys(), index=0)

# Trích xuất dữ liệu của riêng tỉnh đang chọn
df_city = df[df['Tỉnh'] == selected_city].sort_values('time')
current_data = df_city.iloc[-1]

# ---- 4.1 BÊN TRÁI: 4 Ô VUÔNG & BẢNG XẾP HẠNG ----
st.sidebar.markdown(f"**Thông số {selected_city} hiện tại:**")
col1, col2 = st.sidebar.columns(2)
col3, col4 = st.sidebar.columns(2)

with col1: st.metric(label="🌡️ Nhiệt độ", value=f"{current_data['Nhiệt_độ']:.1f} °C")
with col2: st.metric(label="💧 Độ ẩm", value=f"{current_data['Độ_ẩm']:.1f} %")
with col3: st.metric(label="🌬️ Gió", value=f"{current_data['Tốc_độ_gió']:.1f} km/h")
with col4: st.metric(label="😷 PM2.5", value=f"{current_data['pm2_5']:.1f} µg/m³")

st.sidebar.divider()
st.sidebar.markdown("### 🏆 Bảng Xếp Hạng AQI")
# Nút bấm đổi chiều sắp xếp (Mũi tên lên/xuống như bản vẽ)
sort_asc = st.sidebar.toggle("🔽 Đảo chiều sắp xếp (Tốt nhất/Tệ nhất)", value=False)

# Tạo bảng hiển thị Leaderboard
leaderboard = df_latest[['Tỉnh', 'AQI', 'pm2_5']].copy()
leaderboard = leaderboard.sort_values(by='AQI', ascending=sort_asc)
leaderboard.columns = ['Tỉnh/Thành', 'Chỉ số AQI', 'Bụi PM2.5']
st.sidebar.dataframe(leaderboard, hide_index=True, use_container_width=True)

# ---- 4.2 BÊN PHẢI: CONTROL BAR, CHART, MAP ----
# Thanh Control Bar (Hour | Model | Dynamic AQI)
ctrl1, ctrl2, ctrl3 = st.columns([1, 1, 2])
with ctrl1:
    time_res = st.selectbox("⏳ HOUR (Độ chia)", ["Giờ", "Ngày (Trung bình)"])
with ctrl2:
    selected_model = st.selectbox("🤖 MODEL", ["Random Forest", "LSTM"])
with ctrl3:
    status_text, status_color = get_aqi_status(current_data['AQI'])
    st.markdown(f"<h3 style='text-align: right; color: {status_color};'>AQI {int(current_data['AQI'])} - {status_text}</h3>", unsafe_allow_html=True)

st.divider()

# Biểu đồ (Chart)
st.markdown(f"**📈 Biểu đồ diễn biến AQI - {selected_city}**")
fig_line = px.line(df_city, x='time', y='AQI', 
                   markers=True, 
                   title=f"Lịch sử AQI tại {selected_city}",
                   labels={'time': 'Thời gian', 'AQI': 'Chỉ số Không khí'})
# Nếu AI đã chạy và có số liệu dự báo, thêm đường dự báo vào biểu đồ
if 'AQI_RF_Predict' in df_city.columns and not df_city['AQI_RF_Predict'].isna().all():
    pred_col = 'AQI_RF_Predict' if selected_model == "Random Forest" else 'AQI_LSTM_Predict'
    fig_line.add_scatter(x=df_city['time'], y=df_city[pred_col], mode='lines+markers', name='Dự báo AI', line=dict(dash='dot', color='red'))

st.plotly_chart(fig_line, use_container_width=True)

# Bản đồ (Map)
st.markdown("**🗺️ Bản đồ Ô nhiễm Không khí Toàn quốc**")
fig_map = px.scatter_mapbox(df_latest, lat="lat", lon="lon", hover_name="Tỉnh", 
                            hover_data=["AQI", "pm2_5"],
                            color="AQI", color_continuous_scale=px.colors.diverging.RdYlGn[::-1], 
                            size="AQI", zoom=4.5, height=500,
                            mapbox_style="carto-positron")
st.plotly_chart(fig_map, use_container_width=True)