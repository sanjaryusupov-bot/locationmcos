import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import requests
import time

# Настройка страницы
st.set_page_config(
    page_title="Карта заведений",
    page_icon="🗺️",
    layout="wide"
)

# CSS для улучшения дизайна
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .info-card {
        background: #f8f9fa;
        padding: 1.5rem;
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
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 5px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    div[data-testid="column"] {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

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
                locations.append({
                    "name": name,
                    "address": address,
                    "work_time": work_time
                })
                i += 3
            else:
                i += 1
        
        return locations if locations else get_sample_data()
        
    except Exception as e:
        return get_sample_data()

def get_sample_data():
    """Данные из вашей таблицы"""
    return [
        {
            "name": "Новруз",
            "address": "Чирчик, улица Шарафа Рашидова, 37",
            "work_time": "09:00-20:00"
        },
        {
            "name": "Феруза",
            "address": "Ташкент, Мирзо-Улугбекский район, улица Феруза-1, 32А",
            "work_time": "10:00-23:00"
        },
        {
            "name": "Кургантепа",
            "address": "Ташкент, Янгихаетский район, улица Кургантепа, 11",
            "work_time": "10:00-23:00"
        },
        {
            "name": "Лютфи",
            "address": "Ташкент, Учтепинский район, улица Лутфий, 2-Г",
            "work_time": "10:00-23:00"
        },
        {
            "name": "Бурханов",
            "address": "Ташкент, Мирзо-Улугбекский район, Корасу 2-квартал, 18Д",
            "work_time": "10:00-23:00"
        },
        {
            "name": "Карасу",
            "address": "Ташкент, Мирзо-Улугбекский район, Корасу-6, 7Б",
            "work_time": "10:00-23:00"
        }
    ]

# Функция для геокодирования с несколькими попытками
@st.cache_data(ttl=86400)
def geocode_address(address):
    """Улучшенное геокодирование с несколькими вариантами адреса"""
    
    # Очищаем адрес
    address = address.replace('г.', '').replace('ул.', '').strip()
    
    # Пробуем разные варианты адреса
    variants = [
        address,
        address.replace('район', 'р-н'),
        address.split(',')[0] + ', ' + ','.join(address.split(',')[1:3]) if len(address.split(',')) > 2 else address,
    ]
    
    for variant in variants[:2]:  # Пробуем первые 2 варианта
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": variant + ", Узбекистан",
            "format": "json",
            "limit": 1,
            "accept-language": "ru"
        }
        headers = {
            "User-Agent": "MapApp/1.0"
        }
        
        try:
            time.sleep(0.5)  # Задержка чтобы не заблокировали
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"])
        except:
            continue
    
    # Если не нашли, пробуем поискать только по названию района/города
    parts = address.split(',')
    if len(parts) > 1:
        city = parts[0].strip()
        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": city + ", Узбекистан", "format": "json", "limit": 1}
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
    # Координаты Ташкента
    TASHKENT_COORDS = (41.2995, 69.2401)
    
    if location_data.get("lat") and location_data.get("lon"):
        m = folium.Map(
            location=[location_data["lat"], location_data["lon"]],
            zoom_start=17,
            control_scale=True,
            tiles='OpenStreetMap'
        )
        
        # Стилизованный popup
        popup_html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; min-width: 250px;">
            <h3 style="color: #ff4b4b; margin: 0 0 10px 0; border-bottom: 2px solid #ff4b4b;">
                🏪 {location_data['name']}
            </h3>
            <div style="margin: 10px 0;">
                <strong>📍 Адрес:</strong><br>
                <span style="color: #666;">{location_data['address']}</span>
            </div>
            <div style="margin: 10px 0; background: #f0f0f0; padding: 8px; border-radius: 5px;">
                <strong>🕐 Время работы:</strong><br>
                <span style="color: #4caf50; font-weight: bold;">{location_data['work_time']}</span>
            </div>
        </div>
        """
        
        # Красивый маркер
        folium.Marker(
            location=[location_data["lat"], location_data["lon"]],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=f"<b>{location_data['name']}</b>",
            icon=folium.Icon(color="red", icon="shop", prefix="glyphicon")
        ).add_to(m)
        
        # Добавляем точку с радиусом
        folium.CircleMarker(
            radius=15,
            location=[location_data["lat"], location_data["lon"]],
            color="#ff4b4b",
            fill=True,
            fill_color="#ff4b4b",
            fill_opacity=0.3,
            popup=location_data['name']
        ).add_to(m)
        
    else:
        m = folium.Map(location=TASHKENT_COORDS, zoom_start=12, tiles='OpenStreetMap')
    
    return m

# Основное приложение
# Заголовок
st.markdown("""
<div class="main-header">
    <h1 style="color: white; margin: 0;">🗺️ Интерактивная карта заведений</h1>
    <p style="color: white; margin: 10px 0 0 0;">Выберите заведение и найдите его на карте</p>
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

# Создаем колонки для селектора
col_selector, col_empty = st.columns([2, 1])

with col_selector:
    selected_name = st.selectbox(
        "",
        [loc["name"] for loc in locations],
        format_func=lambda x: f"🏪 {x}",
        label_visibility="collapsed"
    )

# Получаем выбранную локацию
selected_location = next(loc for loc in locations if loc["name"] == selected_name)

# Основной контент
col_info, col_map = st.columns([1, 2])

with col_info:
    st.markdown(f"""
    <div class="info-card">
        <h2 style="color: #ff4b4b; margin-top: 0;">📋 {selected_location['name']}</h2>
        <p><strong>📍 Адрес:</strong><br>{selected_location['address']}</p>
        <div class="work-time">
            🕐 {selected_location['work_time']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Кнопка поиска
    if st.button("📍 Показать на карте", use_container_width=True):
        with st.spinner("🔍 Поиск адреса на карте..."):
            lat, lon = geocode_address(selected_location['address'])
            if lat and lon:
                st.session_state['lat'] = lat
                st.session_state['lon'] = lon
                st.session_state['found'] = True
                st.success("✅ Адрес найден!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Адрес не найден")
                st.info("💡 Попробуйте уточнить адрес или обратитесь к администратору")

with col_map:
    st.markdown("### 🗺️ Карта")
    
    if 'found' in st.session_state and st.session_state.get('found', False):
        location_with_coords = selected_location.copy()
        location_with_coords["lat"] = st.session_state.get('lat')
        location_with_coords["lon"] = st.session_state.get('lon')
        m = create_map(location_with_coords)
        folium_static(m, width=700, height=500)
    else:
        m = create_map({})
        st.info("👆 Нажмите кнопку 'Показать на карте' чтобы увидеть местоположение")
        folium_static(m, width=700, height=500)

# Нижняя часть со списком заведений
st.markdown("---")
st.markdown("### 📋 Все заведения")

# Создаем сетку из заведений
cols = st.columns(3)
for idx, loc in enumerate(locations):
    with cols[idx % 3]:
        st.markdown(f"""
        <div style="
            background: #f8f9fa; 
            padding: 10px; 
            border-radius: 8px; 
            margin: 5px;
            border-left: 3px solid #ff4b4b;
        ">
            <b>{loc['name']}</b><br>
            <span style="font-size: 12px; color: #666;">🕐 {loc['work_time']}</span>
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 12px;">
    🗺️ Карты OpenStreetMap | 📍 Данные из Google Sheets
</div>
""", unsafe_allow_html=True)
