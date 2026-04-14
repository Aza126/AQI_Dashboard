import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

def load_and_clean_data(filepath):
    print("1. Đang tải dữ liệu thô...")
    new_df = pd.read_csv(filepath)
    new_df['time'] = pd.to_datetime(new_df['time'])
    
    print("2. Đang đọc kho lịch sử để cộng dồn (Kiến trúc Streaming)...")
    try:
        old_df = pd.read_csv('processed_aqi_data.csv')
        old_df['time'] = pd.to_datetime(old_df['time'])
        
        # Cộng dồn (Append) dữ liệu giờ mới vào đáy bảng lịch sử cũ
        df = pd.concat([old_df, new_df], ignore_index=True)
        
        # Xóa các dòng trùng lặp (nếu Actions lỡ chạy 2 lần 1 giờ). 
        # keep='first' để ưu tiên giữ lại dòng cũ VÌ DÒNG CŨ ĐÃ CÓ KẾT QUẢ DỰ BÁO CỦA AI.
        df = df.drop_duplicates(subset=['time', 'Tỉnh'], keep='first')
        print("🔄 Đã cộng dồn thành công vào kho dữ liệu!")
    except FileNotFoundError:
        print("🆕 Chạy lần đầu, tạo mới kho dữ liệu...")
        df = new_df
        # Khởi tạo sẵn 2 cột dự báo bằng rỗng (NaN) để không bị lỗi print
        df['AQI_RF_Predict'] = np.nan
        df['AQI_LSTM_Predict'] = np.nan

    print("3. Đang xử lý khuyết thiếu (Nội suy)...")
    # Sắp xếp lại theo Tỉnh và Thời gian để chuẩn bị nội suy
    df = df.sort_values(by=['Tỉnh', 'time']).reset_index(drop=True)
    
    # Kỹ thuật transform() an toàn: Giúp nội suy mà KHÔNG BAO GIỜ bị Pandas nuốt mất cột Tỉnh
    env_cols = ['Nhiệt_độ', 'Độ_ẩm', 'Tốc_độ_gió', 'pm2_5', 'pm10', 'carbon_monoxide', 'nitrogen_dioxide', 'ozone']
    df[env_cols] = df.groupby('Tỉnh')[env_cols].transform(
        lambda x: x.interpolate(method='linear').bfill().ffill()
    )

    print("4. Đang tính toán chỉ số AQI...")
    def calculate_aqi(pm25):
        breakpoints = [
            (0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
            (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 350.4, 301, 400),
            (350.5, 500.4, 401, 500)
        ]
        for (c_low, c_high, i_low, i_high) in breakpoints:
            if c_low <= pm25 <= c_high:
                return ((i_high - i_low) / (c_high - c_low)) * (pm25 - c_low) + i_low
        return 500
        
    df['AQI'] = df['pm2_5'].apply(calculate_aqi).round(0)

    print("5. Đang trích xuất đặc trưng chu kỳ thời gian...")
    df['hour'] = df['time'].dt.hour
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 23.0)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 23.0)

    # print("6. Đang chuẩn hóa các biến số môi trường...")
    # scaler = StandardScaler()
    # df[env_cols] = scaler.fit_transform(df[env_cols])
    
    return df

if __name__ == "__main__":
    try:
        processed_df = load_and_clean_data("raw_aqi_data.csv")
        
        # Lưu đè file đích (lúc này đã kẹp cả lịch sử cũ và dữ liệu mới)
        processed_df.to_csv("processed_aqi_data.csv", index=False)
        
        print("\n✅ Hoàn tất! Xem thử 5 dòng dữ liệu MỚI NHẤT:")
        # In tail() để thấy những dòng mới nhất có cột Predict đang trống chờ AI
        print(processed_df[['time', 'Tỉnh', 'AQI', 'AQI_RF_Predict', 'AQI_LSTM_Predict']].tail())
        print("\n💾 Đã lưu thành công ra file 'processed_aqi_data.csv'")
        
    except FileNotFoundError:
        print("❌ Không tìm thấy file 'raw_aqi_data.csv'.")