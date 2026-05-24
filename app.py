import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import requests

# Настройка страницы
st.set_page_config(
    page_title="Карта заведений",
    page_icon="🗺️",
    layout="wide"
)

# CSS для дизайна
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .info-card {
        background: #f8f9fa;
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 4px solid #ff4b4b;
        margin-bottom: 1rem;
    }
    .work-time {
        background: #e8f5e9;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
        margin-top: 10px;
    }
    .coordinates {
        background: #e3f2fd;
        padding: 0.5rem;
        border-radius: 5px;
        font-size: 12px;
        text-align: center;
        margin-top: 10px;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# БАЗА КООРДИНАТ ДЛЯ ВАШИХ ЗАВЕДЕНИЙ
# Вы можете добавить или исправить координаты здесь
LOCATIONS_COORDS = {
    "Новруз": {"lat": 41.4712, "lon": 69.5821, "accuracy": "high"},  # Чирчик
    "Феруза": {"lat": 41.2995, "lon": 69.2401, "accuracy": "medium"},  # Ташкент, Мирзо-Улугбекский р-н
    "Кургантепа": {"lat": 41.2500, "lon": 69.2700, "accuracy": "medium"},  # Ташкент, Янгихаетский р-н
    "Лютфи": {"lat": 41.3200, "lon": 69.2200, "accuracy": "medium"},  # Ташкент, Учтепинский р-н
    "Бурханов": {"lat": 41.3100, "lon": 69.2500, "accuracy": "medium"},  # Ташкент, Мирзо-Улугбекский р-н, Корасу
    "Карасу": {"lat": 41.3080, "lon": 69.2600, "accuracy": "medium"},  # Ташкент, Корасу-6
}

# Функция для загрузки данных из Google Sheets
@st.cache_data(ttl=3600)
def load_data_from_gsheet():
    SPREADSHEET_ID = "1hKZ8ggNLW-OY1bV8xAW7PKl50Fof2co86oxGK92YPAA"
    
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=683057239"
        df = pd.read_csv(url, header=None, on_bad_lines='skip')
        data = df[0].dropna().tolist()
        
        locations = []
        i = 0
        while i < len(data):
            name = str(data[i]).strip()
            if not name or name == 'nan':
                i += 1
                continue
            
            address = None
            work_time = None
            
            for j in range(i+1, min(i+3, len(data))):
                if j < len(data) and data[j] and str(data[j]) != 'nan':
                    text = str(data[j]).lower()
                    if 'адрес' in text or 'г.' in text or 'ул.' in text:
                        address = str(data[j]).strip()
                        if j+1 < len(data) and data[j+1] and str(data[j+1]) != 'nan':
                            time_text = str(data[j+1]).lower()
                            if 'время' in time_text or 'работы' in time_text or ':' in time_text:
                                work_time = str(data[j+1]).strip()
                        break
            
            if name and address and work_time:
                # Добавляем координаты из локальной базы
                coords = LOCATIONS_COORDS.get(name, {"lat": None, "lon": None})
                locations.append({
                    "name": name,
                    "address": address,
                    "work_time": work_time,
                    "lat": coords["lat"],
                    "lon": coords["lon"],
                    "accuracy": coords.get("accuracy", "unknown")
                })
                i += 3
            else:
                i += 1
        
        return locations if locations else get_sample_data()
        
    except Exception as e:
        return get_sample_data()

def get_sample_data():
    """Данные с координатами из локальной базы"""
    return [
        {
            "name": "Новруз",
            "address": "г.Чирчик, ул.Шарафа Рашидова, д.37",
            "work_time": "09:00-20:00",
            "lat": 41.4712,
            "lon": 69.5821,
            "accuracy": "high"
        },
        {
            "name": "Феруза",
            "address": "г.Ташкент, Мирзо-Улугбекский р-н, ул.Феруза-1, д.32А",
            "work_time": "10:00-23:00",
            "lat": 41.2995,
            "lon": 69.2401,
            "accuracy": "medium"
        },
        {
            "name": "Кургантепа",
            "address": "г.Ташкент, Янгихаетский р-н, ул.Кургантепа, д.11",
            "work_time": "10:00-23:00",
            "lat": 41.2500,
            "lon": 69.2700,
            "accuracy": "medium"
        },
        {
            "name": "Лютфи",
            "address": "г. Ташкент, Учтепинский р-н, ул.Лутфий, д.2-Г",
            "work_time": "10:00-23:00",
            "lat": 41.3200,
            "lon": 69.2200,
            "accuracy": "medium"
        },
        {
            "name": "Бурханов",
            "address": "г. Ташкент, Мирзо-Улугбекский р-н, Алишер Навои МФЙ, Корасу 2-квартал, д.18Д",
            "work_time": "10:00-23:00",
            "lat": 41.3100,
            "lon": 69.2500,
            "accuracy": "medium"
        },
        {
            "name": "Карасу",
            "address": "г.Ташкент, Мирзо-Улугбекский р-н, Янги Авайхон МФЙ, Корасу-6, д.7Б",
            "work_time": "10:00-23:00",
            "lat": 41.3080,
            "lon": 69.2600,
            "accuracy": "medium"
        }
    ]

# Функция для поиска координат через OpenStreetMap (если нет в базе)
def find_coordinates_online(address):
    """Поиск координат через OpenStreetMap"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": f"{address}, Узбекистан",
        "format": "json",
        "limit": 1,
        "accept-language": "ru"
    }
    headers = {"User-Agent": "MapApp/1.0"}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except:
        pass
    return None, None

# Функция для создания карты
def create_map(location_data):
    # Координаты Ташкента (по умолчанию)
    TASHKENT_COORDS = (41.2995, 69.2401)
    
    # Если есть координаты
    if location_data.get("lat") and location_data.get("lon"):
        m = folium.Map(
            location=[location_data["lat"], location_data["lon"]],
            zoom_start=17 if location_data.get("accuracy") == "high" else 15,
            control_scale=True,
            tiles='OpenStreetMap'
        )
        
        # Информационное окно
        popup_html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; min-width: 250px;">
            <h3 style="color: #ff4b4b; margin: 0 0 10px 0;">
                🏪 {location_data['name']}
            </h3>
            <div style="margin: 10px 0;">
                <strong>📍 Адрес:</strong><br>
                {location_data['address']}
            </div>
            <div style="margin: 10px 0; background: #f0f0f0; padding: 8px; border-radius: 5px;">
                <strong>🕐 Время работы:</strong><br>
                <span style="color: #4caf50; font-weight: bold;">{location_data['work_time']}</span>
            </div>
        </div>
        """
        
        # Маркер
        folium.Marker(
            location=[location_data["lat"], location_data["lon"]],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"<b>{location_data['name']}</b>",
            icon=folium.Icon(color="red", icon="shop", prefix="glyphicon")
        ).add_to(m)
        
        # Круг для выделения
        folium.CircleMarker(
            radius=20,
            location=[location_data["lat"], location_data["lon"]],
            color="#ff4b4b",
            fill=True,
            fill_color="#ff4b4b",
            fill_opacity=0.2,
            weight=2
        ).add_to(m)
        
    else:
        m = folium.Map(location=TASHKENT_COORDS, zoom_start=12, tiles='OpenStreetMap')
    
    return m

# Основное приложение
# Заголовок
st.markdown("""
<div class="main-header">
    <h1 style="color: white; margin: 0;">🗺️ Карта заведений</h1>
    <p style="color: white; margin: 10px 0 0 0;">Выберите заведение из списка</p>
</div>
""", unsafe_allow_html=True)

# Загрузка данных
with st.spinner("📡 Загрузка данных..."):
    locations = load_data_from_gsheet()

if not locations:
    st.error("❌ Не удалось загрузить данные")
    st.stop()

# Выбор заведения
st.markdown("### 🔍 Выберите заведение")

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    selected_name = st.selectbox(
        "",
        [loc["name"] for loc in locations],
        format_func=lambda x: f"🏪 {x}",
        label_visibility="collapsed"
    )

# Получаем выбранную локацию
selected_location = next(loc for loc in locations if loc["name"] == selected_name)

# Информация и карта
col_info, col_map = st.columns([1, 2])

with col_info:
    accuracy_text = {
        "high": "✅ Точное местоположение",
        "medium": "📍 Приблизительное местоположение",
        "unknown": "⚠️ Местоположение уточняется"
    }.get(selected_location.get("accuracy", "unknown"), "📍 На карте")
    
    st.markdown(f"""
    <div class="info-card">
        <h2 style="color: #ff4b4b; margin-top: 0;">📋 {selected_location['name']}</h2>
        <p><strong>📍 Адрес:</strong><br>{selected_location['address']}</p>
        <div class="work-time">
            🕐 Время работы: {selected_location['work_time']}
        </div>
        <div class="coordinates">
            {accuracy_text}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_map:
    st.markdown("### 🗺️ Местоположение на карте")
    m = create_map(selected_location)
    folium_static(m, width=700, height=500)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 12px;">
    🗺️ Карты OpenStreetMap | 📍 Данные из Google Sheets
</div>
""", unsafe_allow_html=True)
