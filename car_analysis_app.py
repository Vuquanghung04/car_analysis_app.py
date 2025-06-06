import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from pymongo import MongoClient
import pandas as pd
import logging
import traceback
from typing import Tuple, List

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thiết lập giao diện Streamlit
st.set_page_config(page_title="Phân tích dữ liệu xe hơi", layout="wide")
st.title("Phân tích dữ liệu xe hơi")

# Kết nối MongoDB
@st.cache_resource
def init_connection():
    try:
        client = MongoClient("mongodb://localhost:27017/")
        # Test connection
        client.server_info()
        return client
    except Exception as e:
        logger.error(f"Lỗi kết nối MongoDB: {str(e)}")
        st.error("Không thể kết nối đến MongoDB. Vui lòng kiểm tra server.")
        return None

client = init_connection()
if client is None:
    st.stop()
db = client["car_db"]

# Lấy danh sách năm và hãng xe để tạo bộ lọc
@st.cache_data
def get_filter_options() -> Tuple[int, int, List[str]]:
    try:
        logger.info("Đang lấy options cho bộ lọc...")
        pipeline = [
            {
                "$unwind": "$brand"
            },
            {
                "$group": {
                    "_id": None,
                    "years": {"$addToSet": "$year"},
                    "brands": {"$addToSet": "$brand.name"}
                }
            }
        ]
        result = list(db.cars_joined.aggregate(pipeline))
        if not result:
            raise ValueError("Không tìm thấy dữ liệu năm hoặc hãng xe")
            
        years = sorted(result[0]["years"])
        brands = sorted(result[0]["brands"])
        logger.info(f"Tìm thấy {len(years)} năm và {len(brands)} hãng xe")
        return min(years), max(years), brands
    except Exception as e:
        logger.error(f"Lỗi trong get_filter_options: {str(e)}")
        logger.error(traceback.format_exc())
        return 2000, 2023, ["Unknown"]
    
# Hàm lấy thống kê tổng quan
@st.cache_data(hash_funcs={tuple: lambda x: hash(str(x))})
def get_overview_stats(year_range: Tuple[int, int], brands: List[str]) -> dict:
    try:
        logger.info(f"Đang lấy thống kê với năm: {year_range}, brands: {brands}")
        pipeline = [
            {
                "$unwind": "$brand"
            },
            {
                "$match": {
                    "year": {"$gte": year_range[0], "$lte": year_range[1]},
                    "brand.name": {"$in": brands}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_cars": {"$sum": 1},
                    "avg_price": {"$avg": "$price"},
                    "avg_horsepower": {"$avg": "$specifications.horsepower"},
                    "unique_brands": {"$addToSet": "$brand.name"}
                }
            }
        ]
        result = list(db.cars_joined.aggregate(pipeline))
        logger.info(f"Kết quả thống kê: {result}")
        
        if not result:
            return {
                "total_cars": 0,
                "avg_price": 0,
                "avg_horsepower": 0,
                "brand_count": 0
            }
            
        return {
            "total_cars": result[0]["total_cars"],
            "avg_price": result[0]["avg_price"],
            "avg_horsepower": result[0]["avg_horsepower"],
            "brand_count": len(result[0]["unique_brands"])
        }
    except Exception as e:
        logger.error(f"Lỗi trong get_overview_stats: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "total_cars": 0,
            "avg_price": 0,
            "avg_horsepower": 0,
            "brand_count": 0
        }

# Hàm lấy phân bố giá theo hãng xe
@st.cache_data(hash_funcs={tuple: lambda x: hash(str(x))})
def get_price_distribution(year_range: Tuple[int, int], brands: List[str]) -> pd.DataFrame:
    try:
        logger.info(f"Đang lấy phân bố giá với năm: {year_range}, brands: {brands}")
        pipeline = [
            {
                "$unwind": "$brand"
            },
            {
                "$match": {
                    "year": {"$gte": year_range[0], "$lte": year_range[1]},
                    "brand.name": {"$in": brands}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "brand_name": "$brand.name",
                    "price": 1
                }
            }
        ]
        result = list(db.cars_joined.aggregate(pipeline))
        logger.info(f"Tìm thấy {len(result)} bản ghi cho phân bố giá")
        
        if not result:
            return pd.DataFrame(columns=["brand_name", "price"])
            
        return pd.DataFrame(result)
    except Exception as e:
        logger.error(f"Lỗi trong get_price_distribution: {str(e)}")
        logger.error(traceback.format_exc())
        return pd.DataFrame(columns=["brand_name", "price"])
    
# Hàm lấy phân bố loại nhiên liệu
@st.cache_data(hash_funcs={tuple: lambda x: hash(str(x))})
def get_fuel_distribution(year_range: Tuple[int, int], brands: List[str]) -> dict:
    try:
        logger.info(f"Đang lấy phân bố nhiên liệu với năm: {year_range}, brands: {brands}")
        pipeline = [
            {
                "$unwind": "$brand"
            },
            {
                "$match": {
                    "year": {"$gte": year_range[0], "$lte": year_range[1]},
                    "brand.name": {"$in": brands}
                }
            },
            {
                "$group": {
                    "_id": "$fuelType",
                    "count": {"$sum": 1},
                    "total_price": {"$sum": "$price"}
                }
            },
            {
                "$project": {
                    "count": 1,
                    "avg_price": {"$divide": ["$total_price", "$count"]}
                }
            }
        ]
        result = list(db.cars_joined.aggregate(pipeline))
        logger.info(f"Kết quả phân bố nhiên liệu: {result}")
        
        if not result:
            return {
                "fuel_counts": {},
                "avg_prices": {}
            }
            
        return {
            "fuel_counts": {str(r["_id"] or "Unknown"): r["count"] for r in result},
            "avg_prices": {str(r["_id"] or "Unknown"): r["avg_price"] for r in result}
        }
    except Exception as e:
        logger.error(f"Lỗi trong get_fuel_distribution: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "fuel_counts": {},
            "avg_prices": {}
        }
    
# Hàm lấy dữ liệu tương quan
@st.cache_data(hash_funcs={tuple: lambda x: hash(str(x))})
def get_correlation_data(year_range: Tuple[int, int], brands: List[str]) -> pd.DataFrame:
    try:
        logger.info(f"Đang lấy dữ liệu tương quan với năm: {year_range}, brands: {brands}")
        pipeline = [
            {
                "$unwind": "$brand"
                },
            {
                "$match": {
                    "year": {"$gte": year_range[0], "$lte": year_range[1]},
                    "brand.name": {"$in": brands}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "price": 1,
                    "horsepower": "$specifications.horsepower",
                    "torque": "$specifications.torque",
                    "engineDisplacement": "$specifications.engineDisplacement"
                }
            }
        ]
        result = list(db.cars_joined.aggregate(pipeline))
        logger.info(f"Tìm thấy {len(result)} bản ghi cho phân tích tương quan")
        
        if not result:
            return pd.DataFrame()
            
        df = pd.DataFrame(result)
        logger.info(f"Columns in DataFrame: {df.columns.tolist()}")
        return df
    except Exception as e:
        logger.error(f"Lỗi trong get_correlation_data: {str(e)}")
        logger.error(traceback.format_exc())
        return pd.DataFrame()
    
try:
    # Lấy options cho bộ lọc
    min_year, max_year, all_brands = get_filter_options()
    
    # Sidebar cho bộ lọc
    st.sidebar.header("Bộ lọc")
    
    selected_years = tuple(st.sidebar.slider(
        "Chọn khoảng năm",
        min_year,
        max_year,
        (min_year, max_year)
    ))
    
    selected_brands = st.sidebar.multiselect(
        "Chọn hãng xe",
        options=all_brands,
        default=all_brands[:5] if len(all_brands) >= 5 else all_brands
    )
    
    if not selected_brands:
        st.warning("Vui lòng chọn ít nhất một hãng xe")
        st.stop()
    
   

    
   


 # Hiển thị thống kê tổng quan
    st.header("Thống kê tổng quan")
    overview_stats = get_overview_stats(selected_years, selected_brands)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng số xe", overview_stats["total_cars"])
    with col2:
        st.metric("Giá trung bình", f"${overview_stats['avg_price']:,.2f}")
    with col3:
        st.metric("Công suất trung bình", f"{overview_stats['avg_horsepower']:,.0f} HP")
    with col4:
        st.metric("Số hãng xe", overview_stats["brand_count"])


# Biểu đồ phân bố giá theo hãng xe
    st.header("Phân tích giá xe")
    price_dist_df = get_price_distribution(selected_years, selected_brands)
    
    if not price_dist_df.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        sns.boxplot(data=price_dist_df, x='brand_name', y='price', ax=ax)
        plt.xticks(rotation=45, ha='right')
        plt.title("Phân bố giá theo hãng xe")
        plt.xlabel("Hãng xe")
        plt.ylabel("Giá (USD)")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.warning("Không có dữ liệu để hiển thị biểu đồ phân bố giá")

 # Biểu đồ phân bố loại nhiên liệu
    fuel_data = get_fuel_distribution(selected_years, selected_brands)
    
    if fuel_data["fuel_counts"]:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Phân bố loại nhiên liệu")
            fig, ax = plt.subplots(figsize=(8, 8))
            plt.pie(
                list(fuel_data["fuel_counts"].values()),
                labels=list(fuel_data["fuel_counts"].keys()),
                autopct='%1.1f%%'
            )
            plt.title("Tỷ lệ loại nhiên liệu")
            st.pyplot(fig)


        with col2:
            st.subheader("Giá trung bình theo loại nhiên liệu")
            fig, ax = plt.subplots(figsize=(8, 6))
            fuel_types = list(fuel_data["avg_prices"].keys())
            avg_prices = list(fuel_data["avg_prices"].values())
            plt.bar(fuel_types, avg_prices)
            plt.title("Giá trung bình theo loại nhiên liệu")
            plt.xlabel("Loại nhiên liệu")
            plt.ylabel("Giá trung bình (USD)")
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
    else:
        st.warning("Không có dữ liệu để hiển thị biểu đồ nhiên liệu")
    
    # Biểu đồ tương quan
    correlation_df = get_correlation_data(selected_years, selected_brands)
    
    if not correlation_df.empty:
        st.header("Tương quan giữa các thông số kỹ thuật")
        correlation_data = correlation_df[[
            'price',
            'horsepower',
            'torque',
            'engineDisplacement'
        ]].rename(columns={
            'horsepower': 'Công suất (HP)',
            'torque': 'Mô-men xoắn',
            'engineDisplacement': 'Dung tích động cơ',
            'price': 'Giá'
        })
        
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(correlation_data.corr(), annot=True, cmap='coolwarm', ax=ax)
        plt.title("Ma trận tương quan giữa các thông số")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.warning("Không có dữ liệu để hiển thị ma trận tương quan")


except Exception as e:
        logger.error(f"Lỗi chung trong ứng dụng: {str(e)}")
        logger.error(traceback.format_exc())
        st.error(f"Đã xảy ra lỗi: {str(e)}")


