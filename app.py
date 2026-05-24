import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import re
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json

# Настройка страницы
st.set_page_config(page_title="Карта заведений", layout="wide")

# Функция для загрузки данных из Google Sheets
@st.cache_data(ttl=3600)
def load_data_from_gsheet():
    # ID вашей таблицы
    SPREADSHEET_ID = "1hKZ8ggNLW-OY1bV8xAW7PKl50Fof2co86oxGK92YPAA"
    RANGE_NAME = "Лист1!A:A"  # Вкладка "Лист1", колонка A
    
    try:
        # Альтернативный способ: чтение через pandas без авторизации (публичная таблица)
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=683057239"
        df = pd.read_csv(url, header=None)
        
        # Извлекаем данные из колонки A
        data = df[0].dropna().tolist()
        
        # Парсим данные: группируем по 3 строки (название, адрес, время работы)
        locations = []
        for i in range(0, len(data), 3):
            if i + 2 < len(data):
                name = str(data[i]).strip()
                address = str(data[i+1]).strip()
                work_time = str(data[i+2]).strip()
                
                # Пропускаем пустые строки
                if name and address and work_time:
                    locations.append({
                        "name": name,
                        "address": address,
                        "work_time": work_time
                    })
        
        return locations
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {e}")
        return []

# Функция для геокодирования адреса через Nominatim (OpenStreetMap)
def geocode_address(address):
    import requests
    from time import sleep
    
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "accept-language": "ru"
    }
    headers = {
        "User-Agent": "StreamlitMapApp/1.0"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        st.warning(f"Ошибка геокодирования для {address}: {e}")
    
    return None, None

# Функция для создания карты с выбранной локацией
def create_map(location_data):
    if location_data["lat"] is None or location_data["lon"] is None:
        st.error("Не удалось определить координаты адреса")
        return folium.Map(location=[41.2995, 69.2401], zoom_start=12)  # Центр Ташкента
    
    # Создаем карту с центром на выбранной локации
    m = folium.Map(
        location=[location_data["lat"], location_data["lon"]],
        zoom_start=16,
        control_scale=True
    )
    
    # HTML для popup с информацией
    popup_html = f"""
    <div style="font-family: Arial, sans-serif; min-width: 200px;">
        <h4 style="color: #2c3e50; margin-bottom: 10px;">🏪 {location_data['name']}</h4>
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
    
    # Добавляем круг для наглядности
    folium.Circle(
        radius=100,
        location=[location_data["lat"], location_data["lon"]],
        popup=location_data["name"],
        color="#3186cc",
        fill=True,
        fill_color="#3186cc"
    ).add_to(m)
    
    return m

# Основное приложение
st.title("🗺️ Интерактивная карта заведений")
st.markdown("---")

# Загружаем данные
with st.spinner("Загрузка данных из Google Sheets..."):
    locations = load_data_from_gsheet()

if not locations:
    st.error("Не удалось загрузить данные. Проверьте доступ к таблице.")
    st.info("""
    **Инструкция:** 
    1. Убедитесь, что таблица опубликована как CSV или имеет публичный доступ
    2. Проверьте, что данные находятся на вкладке "Лист1" в колонке A
    3. Данные должны быть сгруппированы по 3 строки: название → адрес → время работы
    
    **Альтернативный вариант:** если таблица закрыта, вы можете скопировать данные в локальный CSV файл.
    """)
    st.stop()

# Создаем список названий для выбора
place_names = [loc["name"] for loc in locations]

# Выбор локации
st.subheader("🔍 Выберите заведение")
selected_name = st.selectbox(
    "Нажмите, чтобы выбрать:",
    place_names,
    format_func=lambda x: f"🏪 {x}"
)

# Находим выбранную локацию
selected_location = next((loc for loc in locations if loc["name"] == selected_name), None)

if selected_location:
    # Показываем информацию в две колонки
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"""
        ### 📋 Информация о заведении
        - **Название:** {selected_location['name']}
        - **Адрес:** {selected_location['address']}
        - **Время работы:** {selected_location['work_time']}
        """)
        
        # Кнопка для обновления координат
        if st.button("🔄 Показать на карте", type="primary"):
            with st.spinner("Поиск адреса на карте..."):
                lat, lon = geocode_address(selected_location['address'])
                selected_location["lat"] = lat
                selected_location["lon"] = lon
                
                if lat and lon:
                    st.success("📍 Адрес найден на карте!")
                    st.session_state['lat'] = lat
                    st.session_state['lon'] = lon
                    st.session_state['map_updated'] = True
                else:
                    st.error("❌ Адрес не найден. Проверьте правильность адреса.")
                    st.session_state['map_updated'] = False
            st.rerun()
    
    with col2:
        st.info("""
        💡 **Подсказка:**
        Нажмите кнопку "Показать на карте", чтобы увидеть местоположение
        """)
    
    st.markdown("---")
    
    # Отображаем карту
    st.subheader("🗺️ Карта")
    
    # Проверяем, есть ли координаты в session_state
    if 'map_updated' in st.session_state and st.session_state['map_updated']:
        if 'lat' in st.session_state and 'lon' in st.session_state:
            location_with_coords = selected_location.copy()
            location_with_coords["lat"] = st.session_state['lat']
            location_with_coords["lon"] = st.session_state['lon']
            m = create_map(location_with_coords)
            folium_static(m, width=800, height=500)
        else:
            st.warning("Нажмите кнопку выше, чтобы найти адрес на карте")
    else:
        # Если координат нет, показываем карту с центром на Ташкенте
        m = folium.Map(location=[41.2995, 69.2401], zoom_start=12)
        st.info("👉 Нажмите кнопку 'Показать на карте', чтобы увидеть местоположение выбранного заведения")
        folium_static(m, width=800, height=500)

# Добавляем боковую панель с информацией
with st.sidebar:
    st.markdown("""
    ## 📌 Информация
    
    ### О приложении
    Это приложение отображает заведения из Google Sheets на интерактивной карте.
    
    ### Как пользоваться:
    1. Выберите заведение из списка
    2. Нажмите "Показать на карте"
    3. Дождитесь загрузки карты
    4. Кликните на маркер, чтобы увидеть подробности
    
    ### Технологии:
    - **Streamlit** - веб-интерфейс
    - **Folium** - отображение карт
    - **OpenStreetMap** - геокодирование
    - **Google Sheets API** - данные
    
    ### Данные:
    """)
    
    # Показываем список всех заведений
    st.markdown("**Доступные заведения:**")
    for loc in locations:
        st.markdown(f"- {loc['name']}")

# Добавляем информацию о времени последнего обновления
st.markdown("---")
st.caption("🗺️ Данные загружены из Google Sheets | Карты OpenStreetMap | Обновлено: " + pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))