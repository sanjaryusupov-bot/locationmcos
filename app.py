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

# CSS для современного дизайна
st.markdown("""
<style>
    /* Главный заголовок */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.8rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
    }
    .main-header p {
        color: rgba(255,255,255,0.9);
        margin: 10px 0 0 0;
    }
    
    /* Карточка информации */
    .info-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .info-card h2 {
        color: #667eea;
        margin-top: 0;
        border-bottom: 2px solid #667eea;
        padding-bottom: 10px;
    }
    .info-detail {
        margin: 15px 0;
        padding: 10px;
        background: white;
        border-radius: 10px;
    }
    .work-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 10px;
        text-align: center;
        font-weight: bold;
        margin-top: 15px;
    }
    .coords-badge {
        background: #e8f5e9;
        padding: 0.5rem;
        border-radius: 10px;
        text-align: center;
        font-size: 12px;
        margin-top: 10px;
        font-family: monospace;
    }
    
    /* Стили для селектора */
    .stSelectbox {
        margin-bottom: 20px;
    }
    .stSelectbox label {
        font-size: 16px;
        font-weight: bold;
        color: #667eea;
    }
    
    /* Адаптивность */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Функция для загрузки данных из Google Sheets
@st.cache_data(ttl=3600)
def load_data_from_gsheet():
    SPREADSHEET_ID = "1hKZ8ggNLW-OY1bV8xAW7PKl50Fof2co86oxGK92YPAA"
    
    try:
        # Пробуем загрузить как CSV
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=683057239"
        df = pd.read_csv(url)
        
        # Проверяем наличие нужных колонок
        required_columns = ['name', 'address', 'latitude', 'longitude']
        if all(col in df.columns for col in required_columns):
            # Очищаем данные
            df = df.dropna(subset=['name', 'latitude', 'longitude'])
            locations = []
            for _, row in df.iterrows():
                loc = {
                    "name": str(row['name']).strip(),
                    "address": str(row['address']).strip() if pd.notna(row['address']) else "Адрес не указан",
                    "lat": float(row['latitude']),
                    "lon": float(row['longitude'])
                }
                # Извлекаем время работы из адреса если есть
                if 'до' in loc['address'] or ':' in loc['address']:
                    import re
                    time_match = re.search(r'(\d{2}:\d{2})\s*[-–]\s*(\d{2}:\d{2})', loc['address'])
                    if time_match:
                        loc['work_time'] = f"{time_match.group(1)}-{time_match.group(2)}"
                    else:
                        loc['work_time'] = "Информация отсутствует"
                else:
                    loc['work_time'] = "Информация отсутствует"
                locations.append(loc)
            return locations
        else:
            st.error(f"Таблица должна содержать колонки: name, address, latitude, longitude")
            return []
            
    except Exception as e:
        st.error(f"Ошибка загрузки: {str(e)}")
        return []

# Функция для создания красивой карты
def create_map(location_data):
    # Карта с красивым стилем
    m = folium.Map(
        location=[location_data["lat"], location_data["lon"]],
        zoom_start=16,
        control_scale=True,
        tiles='CartoDB positron'  # Более красивый стиль карты
    )
    
    # Время работы (если есть)
    work_time_text = location_data.get('work_time', 'Информация отсутствует')
    
    # HTML для всплывающего окна
    popup_html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; min-width: 250px; max-width: 300px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 10px; 
                    border-radius: 10px 10px 0 0;
                    margin: -12px -12px 0 -12px;">
            <h3 style="color: white; margin: 0; font-size: 16px;">
                🏪 {location_data['name']}
            </h3>
        </div>
        <div style="padding: 15px;">
            <div style="margin: 10px 0;">
                <strong>📍 Адрес:</strong><br>
                <span style="color: #555; font-size: 13px;">{location_data['address']}</span>
            </div>
            <div style="margin: 10px 0; background: #f0f0f0; padding: 8px; border-radius: 8px;">
                <strong>🕐 Время работы:</strong><br>
                <span style="color: #4caf50; font-weight: bold;">{work_time_text}</span>
            </div>
            <div style="margin: 10px 0; font-size: 11px; color: #999; text-align: center;">
                📍 Координаты: {location_data['lat']:.4f}, {location_data['lon']:.4f}
            </div>
        </div>
    </div>
    """
    
    # Красивый маркер с иконкой
    folium.Marker(
        location=[location_data["lat"], location_data["lon"]],
        popup=folium.Popup(popup_html, max_width=350),
        tooltip=f"<b>{location_data['name']}</b>",
        icon=folium.Icon(color="red", icon="shop", prefix="glyphicon", icon_color="white")
    ).add_to(m)
    
    # Эффект пульсации (круг)
    folium.CircleMarker(
        radius=25,
        location=[location_data["lat"], location_data["lon"]],
        color="#667eea",
        fill=True,
        fill_color="#667eea",
        fill_opacity=0.1,
        weight=2,
        popup=location_data['name']
    ).add_to(m)
    
    # Добавляем красивый кружок в центре
    folium.CircleMarker(
        radius=8,
        location=[location_data["lat"], location_data["lon"]],
        color="#ff4b4b",
        fill=True,
        fill_color="#ff4b4b",
        fill_opacity=1,
        weight=0
    ).add_to(m)
    
    return m

# Функция для создания карты со всеми точками
def create_map_all(locations):
    # Центр Ташкента
    center_lat = 41.2995
    center_lon = 69.2401
    
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=11,
        control_scale=True,
        tiles='CartoDB positron'
    )
    
    # Добавляем все точки на карту
    for loc in locations:
        work_time_text = loc.get('work_time', 'Информация отсутствует')
        
        popup_html = f"""
        <div style="font-family: 'Segoe UI', Arial, sans-serif; min-width: 200px;">
            <b style="color: #667eea;">🏪 {loc['name']}</b><br>
            <span style="font-size: 12px;">📍 {loc['address'][:100]}</span><br>
            <span style="font-size: 11px; color: #4caf50;">🕐 {work_time_text}</span>
        </div>
        """
        
        folium.Marker(
            location=[loc["lat"], loc["lon"]],
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=loc['name'],
            icon=folium.Icon(color="blue", icon="info-sign", prefix="glyphicon", icon_color="white")
        ).add_to(m)
    
    return m

# Основное приложение
# Заголовок
st.markdown("""
<div class="main-header">
    <h1>🗺️ Интерактивная карта заведений</h1>
    <p>Выберите заведение из списка, чтобы увидеть его на карте</p>
</div>
""", unsafe_allow_html=True)

# Загрузка данных
with st.spinner("📡 Загрузка данных из Google Sheets..."):
    locations = load_data_from_gsheet()

if not locations:
    st.error("❌ Не удалось загрузить данные. Проверьте таблицу.")
    st.stop()

# Вкладки для переключения режимов
tab1, tab2 = st.tabs(["📍 Одно заведение", "🗺️ Все заведения на карте"])

with tab1:
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
    col_info, col_map = st.columns([1, 1.5])
    
    with col_info:
        st.markdown(f"""
        <div class="info-card">
            <h2>📋 {selected_location['name']}</h2>
            <div class="info-detail">
                <strong>📍 Адрес:</strong><br>
                {selected_location['address']}
            </div>
            <div class="work-badge">
                🕐 {selected_location.get('work_time', 'Информация отсутствует')}
            </div>
            <div class="coords-badge">
                📍 Координаты: {selected_location['lat']:.6f}, {selected_location['lon']:.6f}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Статистика
        st.markdown(f"""
        <div style="background: #e8f5e9; padding: 1rem; border-radius: 10px; text-align: center;">
            <span style="font-size: 24px;">🏪</span><br>
            <strong>Всего заведений:</strong> {len(locations)}
        </div>
        """, unsafe_allow_html=True)
    
    with col_map:
        st.markdown("### 🗺️ Местоположение")
        m = create_map(selected_location)
        folium_static(m, width=700, height=500)
    
    # Дополнительная информация о заведении
    with st.expander("📊 Подробная информация"):
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Название", selected_location['name'])
            st.metric("Широта", f"{selected_location['lat']:.6f}")
        with col_b:
            st.metric("Время работы", selected_location.get('work_time', 'Не указано'))
            st.metric("Долгота", f"{selected_location['lon']:.6f}")

with tab2:
    st.markdown("### 🗺️ Все заведения на карте")
    st.info(f"📍 Показано {len(locations)} заведений. Нажмите на маркер, чтобы увидеть информацию.")
    
    m_all = create_map_all(locations)
    folium_static(m_all, width=1100, height=600)

# Фильтрация по району (дополнительная функция)
st.markdown("---")
st.markdown("### 🔍 Быстрый поиск по названию")

search_term = st.text_input("Введите название заведения", placeholder="Например: Ташкент, Новруз...")
if search_term:
    filtered = [loc for loc in locations if search_term.lower() in loc['name'].lower() or search_term.lower() in loc['address'].lower()]
    if filtered:
        st.success(f"Найдено {len(filtered)} заведений:")
        for loc in filtered:
            st.markdown(f"- **{loc['name']}** — {loc['address'][:100]}...")
    else:
        st.warning("Ничего не найдено")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #999; font-size: 12px;">
    🗺️ Карты: OpenStreetMap (CartoDB) | 📍 Данные из Google Sheets | Обновлено: {}
</div>
""".format(pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)
