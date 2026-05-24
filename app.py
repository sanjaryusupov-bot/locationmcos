import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import requests
import json

# Настройка страницы
st.set_page_config(page_title="Карта заведений", layout="wide")

# Функция для загрузки данных из Google Sheets через CSV экспорт
@st.cache_data(ttl=3600)
def load_data_from_gsheet():
    # ID вашей таблицы
    SPREADSHEET_ID = "1hKZ8ggNLW-OY1bV8xAW7PKl50Fof2co86oxGK92YPAA"
    
    try:
        # Прямая ссылка на CSV экспорт
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=683057239"
        
        # Загружаем CSV
        df = pd.read_csv(url, header=None, on_bad_lines='skip')
        
        # Извлекаем данные из колонки A
        data = df[0].dropna().tolist()
        
        # Парсим данные
        locations = []
        i = 0
        while i < len(data):
            # Получаем название
            name = str(data[i]).strip()
            if not name or name == 'nan':
                i += 1
                continue
            
            # Ищем адрес (следующие 1-2 строки)
            address = None
            work_time = None
            
            # Поиск адреса
            for j in range(i+1, min(i+3, len(data))):
                if j < len(data) and data[j] and str(data[j]) != 'nan':
                    text = str(data[j]).lower()
                    if 'адрес' in text or 'г.' in text or 'ул.' in text:
                        address = str(data[j]).strip()
                        # Ищем время работы в следующей строке
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
        st.warning(f"Использую демо-данные. Ошибка: {str(e)[:100]}")
        return get_sample_data()

def get_sample_data():
    """Демо-данные из вашей таблицы"""
    return [
        {
            "name": "Новруз",
            "address": "г.Чирчик, ул.Шарафа Рашидова, д.37",
            "work_time": "09:00-20:00"
        },
        {
            "name": "Феруза",
            "address": "г.Ташкент, Мирзо-Улугбекский р-н, ул.Феруза-1, д.32А",
            "work_time": "10:00-23:00"
        },
        {
            "name": "Кургантепа",
            "address": "г.Ташкент, Янгихаетский р-н, ул.Кургантепа, д.11",
            "work_time": "10:00-23:00"
        },
        {
            "name": "Лютфи",
            "address": "г.Ташкент, Учтепинский р-н, ул.Лутфий, д.2-Г",
            "work_time": "10:00-23:00"
        },
        {
            "name": "Бурханов",
            "address": "г.Ташкент, Мирзо-Улугбекский р-н, Алишер Навои МФЙ, Корасу 2-квартал, д.18Д",
            "work_time": "10:00-23:00"
        },
        {
            "name": "Карасу",
            "address": "г.Ташкент, Мирзо-Улугбекский р-н, Янги Авайхон МФЙ, Корасу-6, д.7Б",
            "work_time": "10:00-23:00"
        }
    ]

# Функция для геокодирования адреса
@st.cache_data(ttl=86400)
def geocode_address(address):
    """Преобразует адрес в координаты через OpenStreetMap"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "accept-language": "ru"
    }
    headers = {
        "User-Agent": "MyMapApp/1.0 (test@example.com)"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        pass
    
    return None, None

# Функция для создания карты
def create_map(location_data):
    # Если координаты есть, центрируем на них
    if location_data.get("lat") and location_data.get("lon"):
        m = folium.Map(
            location=[location_data["lat"], location_data["lon"]],
            zoom_start=16,
            control_scale=True
        )
        
        # Создаем информационное окно
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="color: #2c3e50; margin: 0 0 10px 0;">🏪 {location_data['name']}</h4>
            <hr style="margin: 5px 0;">
            <p style="margin: 5px 0;">
                <strong>📍 Адрес:</strong><br>
                {location_data['address']}
            </p>
            <p style="margin: 5px 0;">
                <strong>🕐 Время работы:</strong><br>
                {location_data['work_time']}
            </p>
        </div>
        """
        
        # Добавляем маркер
        folium.Marker(
            location=[location_data["lat"], location_data["lon"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=location_data["name"],
            icon=folium.Icon(color="red", icon="info-sign", prefix="glyphicon")
        ).add_to(m)
        
        # Добавляем круг
        folium.Circle(
            radius=100,
            location=[location_data["lat"], location_data["lon"]],
            color="#3186cc",
            fill=True,
            fill_color="#3186cc",
            fill_opacity=0.2
        ).add_to(m)
        
    else:
        # Центр Ташкента
        m = folium.Map(location=[41.2995, 69.2401], zoom_start=12)
    
    return m

# Основное приложение
st.title("🗺️ Интерактивная карта заведений")
st.markdown("---")

# Загружаем данные
with st.spinner("Загрузка данных..."):
    locations = load_data_from_gsheet()

if not locations:
    st.error("Не удалось загрузить данные")
    st.stop()

# Выбор заведения
st.subheader("🔍 Выберите заведение")
selected_name = st.selectbox(
    "Список заведений:",
    [loc["name"] for loc in locations],
    format_func=lambda x: f"🏪 {x}"
)

# Получаем выбранную локацию
selected_location = next(loc for loc in locations if loc["name"] == selected_name)

# Отображаем информацию
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown(f"""
    ### 📋 Информация
    - **Название:** {selected_location['name']}
    - **Адрес:** {selected_location['address']}
    - **Время работы:** {selected_location['work_time']}
    """)
    
    if st.button("📍 Показать на карте", type="primary", use_container_width=True):
        with st.spinner("Поиск адреса..."):
            lat, lon = geocode_address(selected_location['address'])
            if lat and lon:
                st.session_state['lat'] = lat
                st.session_state['lon'] = lon
                st.session_state['found'] = True
                st.success("✅ Адрес найден!")
                st.rerun()
            else:
                st.error("❌ Адрес не найден")

with col2:
    st.info("""
    💡 **Как пользоваться:**
    1. Выберите заведение из списка
    2. Нажмите "Показать на карте"
    3. Дождитесь появления маркера
    4. Нажмите на маркер для деталей
    """)

st.markdown("---")
st.subheader("🗺️ Карта")

# Отображаем карту
if 'found' in st.session_state and st.session_state['found']:
    location_with_coords = selected_location.copy()
    location_with_coords["lat"] = st.session_state['lat']
    location_with_coords["lon"] = st.session_state['lon']
    m = create_map(location_with_coords)
    folium_static(m, width=800, height=500)
else:
    m = create_map({})
    st.info("👆 Нажмите кнопку 'Показать на карте'")
    folium_static(m, width=800, height=500)

# Боковая панель
with st.sidebar:
    st.markdown("""
    ## 📌 О приложении
    
    ### Возможности:
    - 📍 Отображение заведений на карте
    - 🕐 Информация о времени работы
    - 🔍 Поиск по адресу
    - 🗺️ OpenStreetMap карты
    
    ### Все заведения:
    """)
    
    for loc in locations:
        st.markdown(f"**{loc['name']}**  \n{loc['work_time']}")

# Footer
st.markdown("---")
st.caption("🗺️ Данные: Google Sheets | Карты: OpenStreetMap")
