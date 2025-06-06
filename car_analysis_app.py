import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from pymongo import MongoClient
import pandas as pd

# Thiết lập giao diện Streamlit
st.set_page_config(page_title="Phân tích dữ liệu xe hơi", layout="wide")
st.title("Phân tích dữ liệu xe hơi")

# Kết nối MongoDB
@st.cache_resource
def init_connection():
    return MongoClient("mongodb://localhost:27017/")

client = init_connection()
db = client["car_db"]

# Lấy dữ liệu từ collection cars_joined
@st.cache_data
def get_cars_data():
    cars = list(db.cars_joined.find())
    # Chuyển đổi dữ liệu thành DataFrame
    df = pd.json_normalize(cars, 
        meta=[
            'color', 'fuelType', 'price', 'transmission', 'year',
            ['specifications', 'horsepower'],
            ['specifications', 'engineDisplacement'],
            ['specifications', 'torque'],
            ['specifications', 'mileage']
        ],
        record_path='brand',
        record_prefix='brand_'
    )
    return df

df = get_cars_data()

# Sidebar cho bộ lọc
st.sidebar.header("Bộ lọc")
selected_years = st.sidebar.slider(
    "Chọn khoảng năm",
    int(df['year'].min()),
    int(df['year'].max()),
    (int(df['year'].min()), int(df['year'].max()))
)

selected_brands = st.sidebar.multiselect(
    "Chọn hãng xe",
    options=df['brand_name'].unique(),
    default=df['brand_name'].unique()[:5]
)

# Lọc dữ liệu
filtered_df = df[
    (df['year'].between(selected_years[0], selected_years[1])) &
    (df['brand_name'].isin(selected_brands))
]

# Hiển thị thống kê tổng quan
st.header("Thống kê tổng quan")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Tổng số xe", len(filtered_df))
with col2:
    st.metric("Giá trung bình", f"${filtered_df['price'].mean():,.2f}")
with col3:
    st.metric("Công suất trung bình", f"{filtered_df['specifications.horsepower'].mean():,.0f} HP")
with col4:
    st.metric("Số hãng xe", len(filtered_df['brand_name'].unique()))

# Biểu đồ phân bố giá theo hãng xe
st.header("Phân tích giá xe")
fig, ax = plt.subplots(figsize=(12, 6))
sns.boxplot(data=filtered_df, x='brand_name', y='price', ax=ax)
plt.xticks(rotation=45, ha='right')
plt.title("Phân bố giá theo hãng xe")
plt.xlabel("Hãng xe")
plt.ylabel("Giá (USD)")
plt.tight_layout()
st.pyplot(fig)

# Biểu đồ phân bố loại nhiên liệu
col1, col2 = st.columns(2)

with col1:
    st.subheader("Phân bố loại nhiên liệu")
    fuel_counts = filtered_df['fuelType'].value_counts()
    fig, ax = plt.subplots(figsize=(8, 8))
    plt.pie(fuel_counts.values, labels=fuel_counts.index, autopct='%1.1f%%')
    plt.title("Tỷ lệ loại nhiên liệu")
    st.pyplot(fig)

with col2:
    st.subheader("Giá trung bình theo loại nhiên liệu")
    avg_price_fuel = filtered_df.groupby('fuelType')['price'].mean()
    fig, ax = plt.subplots(figsize=(8, 6))
    avg_price_fuel.plot(kind='bar')
    plt.title("Giá trung bình theo loại nhiên liệu")
    plt.xlabel("Loại nhiên liệu")
    plt.ylabel("Giá trung bình (USD)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

# Biểu đồ tương quan giữa các thông số kỹ thuật
st.header("Tương quan giữa các thông số kỹ thuật")
correlation_data = filtered_df[[
    'price', 
    'specifications.horsepower', 
    'specifications.torque', 
    'specifications.engineDisplacement'
]].rename(columns={
    'specifications.horsepower': 'Công suất (HP)',
    'specifications.torque': 'Mô-men xoắn',
    'specifications.engineDisplacement': 'Dung tích động cơ',
    'price': 'Giá'
})

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(correlation_data.corr(), annot=True, cmap='coolwarm', ax=ax)
plt.title("Ma trận tương quan giữa các thông số")
plt.tight_layout()
st.pyplot(fig)

# Biểu đồ scatter plot
st.header("Mối quan hệ giữa công suất và giá")
fig, ax = plt.subplots(figsize=(10, 6))
sns.scatterplot(
    data=filtered_df,
    x='specifications.horsepower',
    y='price',
    hue='brand_name',
    alpha=0.6
)
plt.title("Mối quan hệ giữa công suất và giá xe")
plt.xlabel("Công suất (HP)")
plt.ylabel("Giá (USD)")
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
st.pyplot(fig)

# Bảng dữ liệu chi tiết
st.header("Bảng dữ liệu chi tiết")
display_df = filtered_df[[
    'brand_name', 'year', 'price', 'fuelType',
    'specifications.horsepower', 'specifications.torque',
    'specifications.engineDisplacement', 'specifications.mileage'
]].rename(columns={
    'brand_name': 'Hãng xe',
    'year': 'Năm',
    'price': 'Giá',
    'fuelType': 'Nhiên liệu',
    'specifications.horsepower': 'Công suất (HP)',
    'specifications.torque': 'Mô-men xoắn',
    'specifications.engineDisplacement': 'Dung tích động cơ',
    'specifications.mileage': 'Số km'
})

st.dataframe(
    display_df.style.format({
        'Giá': '${:,.2f}',
        'Công suất (HP)': '{:,.0f}',
        'Mô-men xoắn': '{:,.0f}',
        'Dung tích động cơ': '{:,.2f}',
        'Số km': '{:,.0f}'
    })
) 