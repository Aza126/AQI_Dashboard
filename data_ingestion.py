import requests
import pandas as pd 
from datetime import datetime

cities = {
    "Hà Nội": {"lat": 21.0285, "lon": 105.8542},
    "Hải Phòng": {"lat": 20.8449, "lon": 106.6881},
    "Quảng Ninh": {"lat": 20.9510, "lon": 107.0730},
    "Lào Cai": {"lat": 22.4800, "lon": 103.9750},

    "Đà Nẵng": {"lat": 16.0544, "lon": 108.2022},
    "Huế": {"lat": 16.4637, "lon": 107.5909},
    "Quảng Nam": {"lat": 15.5394, "lon": 108.0191},
    "Khánh Hòa": {"lat": 12.2388, "lon": 109.1967},

    "TP.HCM": {"lat": 10.8231, "lon": 106.6297},
    "Bình Dương": {"lat": 11.3254, "lon": 106.4770},
    "Cần Thơ": {"lat": 10.0452, "lon": 105.7469},
    "Kiên Giang": {"lat": 10.0125, "lon": 105.0809}
}

def fetch_aqi_data(cities):
    cities_data = [] # Rỏ rỗng để đựng dữ liệu gom về

    print("🚀 Bắt đầu quá trình nạp dữ liệu từ API Open-Meteo...")

    # Vòng lặp chạy qua từng tỉnh thành
    for city, coords in cities.items():
        print(f"⏳ Đang kéo dữ liệu cho: {city}...")

        try:
            # --- 1. Gọi API Thời tiết (Nhiệt độ, Độ ẩm, Gió) ---
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={coords['lat']}&longitude={coords['lon']}&current=temperature_2m,relative_humidity_2m,wind_speed_10m&timezone=Asia%2FBangkok"
            weather_res = requests.get(weather_url).json()

            # --- 2. Gọi API Không khí (PM2.5 và các khí độc) ---
            aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={coords['lat']}&longitude={coords['lon']}&current=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone&timezone=Asia%2FBangkok"
            aqi_res = requests.get(aqi_url).json()

            # --- 3. Đóng gói dữ liệu lại thành 1 hàng ---
            city_record = {
                "time": weather_res['current']['time'],
                "Tỉnh": city, # Cột mới cực kỳ quan trọng cho Dashboard
                "Nhiệt_độ": weather_res['current']['temperature_2m'],
                "Độ_ẩm": weather_res['current']['relative_humidity_2m'],
                "Tốc_độ_gió": weather_res['current']['wind_speed_10m'],
                "pm2_5": aqi_res['current']['pm2_5'],
                "pm10": aqi_res['current']['pm10'],
                "carbon_monoxide": aqi_res['current']['carbon_monoxide'],
                "nitrogen_dioxide": aqi_res['current']['nitrogen_dioxide'],
                "ozone": aqi_res['current']['ozone']
            }
            # Bỏ data vào rỏ
            cities_data.append(city_record)
        except Exception as e:
            print(f"⚠️ Lỗi mạng hoặc lỗi API ở trạm {city}: {e}. Bỏ qua trạm này.")
    
    # Biến cái rỏ chứa các gói hàng thành một Bảng Pandas (DataFrame)
    df = pd.DataFrame(cities_data)
    return df

if __name__ == "__main__":
    # Chạy hàm và lấy kết quả
    df = fetch_aqi_data(cities)
    
    # Lưu ra file CSV
    df.to_csv("raw_aqi_data.csv", index=False)
    print("\n✅ Đã hoàn tất nạp dữ liệu và lưu ra 'raw_aqi_data.csv'")
