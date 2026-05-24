import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import requests
from time import sleep

# Настройка страницы
st.set_page_config(page_title="Карта заведений", layout="wide")

# Функция для загрузки данных из Google Sheets
@st.cache_data(ttl=3600)
def load_data_from_gsheet():
    # ID вашей таблицы
    SPREADSHEET_ID = "1hKZ8ggNLW-OY1bV8xAW7PKl50Fof2co86oxGK92YPAA"
    
    try:
        # Пробуем загрузить как CSV с указанием GID
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv&gid=683057239"
        
        # Добавляем заголовки для корректной загрузки
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Сохраняем содержимое в файл для pandas
        with open('temp.csv', 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        df = pd.read_csv('temp.csv', header=None, encoding='utf-8')
        
        # Извлекаем данные из колонки A
        data = df[0].dropna().tolist()
        
        # Парсим данные: группируем по 3 строки (название, адрес, время работы)
        locations = []
        i = 0
        while i < len(data):
            # Пропускаем пустые или невалидные строки
            if pd.isna(data[i]) or str(data[i]).strip() == '':
                i += 1
                continue
                
            name = str(data[i]).strip()
            
            # Ищем следующие строки для адреса и времени
            address = None
            work_time = None
            
            # Ищем адрес (должен содержать "Адрес:")
            for j in range(i+1, min(i+5, len(data))):
                if j < len(data) and data[j] and 'адрес' in str(data[j]).lower():
                    address = str(data[j]).strip()
                    # Ищем время работы после адреса
                    for k in range(j+1, min(j+3, len(data))):
                        if k < len(data) and data[k] and ('время' in str(data[k]).lower() or 'работы' in str(data[k]).lower()):
                            work_time = str(data[k]).strip()
                            break
                    break
            
            if name and address and work_time:
                locations.append({
                    "name": name,
                    "address": address,
                    "work_time": work_time
                })
                i = i + 3
            else:
                i += 1
        
        return locations
        
    except Exception as e:
        st.error(f"Ошибка загрузки данных: {str(e)}")
        # Возвращаем тестовые данные для демонстрации
        return get_sample_data()

def get_sample_data():
    """Тестовые данные на случай ошибки загрузки"""
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
            "address": "г. Ташкент, Учтепинский р-н, ул.Лутфий, д.2-Г",
            "work_time": "10:00-23:00"
        },
        {
            "name": "Бурханов",
            "address": "г. Ташкент, Мирзо-Улугбекский р-н, Алишер Навои МФЙ, Корасу 2-квартал, д.18Д",
            "work_time": "10:00-23:00"
        },
        {
            "name": "Карасу",
            "address": "г.Ташкент, Мирзо-Улугбекский р-н, Янги Авайхон МФЙ, Корасу-6, д.7Б",
            "work_time": "10:00-23:00"
        }
    ]

# Функция для геокодирования адреса через Nominatim (OpenStreetMap)
@st.cache_data(ttl=86400)
def geocode_address(address):
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
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception as e:
        st.warning(f"Ошибка геокодирования: {str(e)}")
    
    return None, None

# Функция для создания карты с выбранной локацией
def create_map(location_data):
    if location_data.get("lat") is None or location_data.get("lon") is None:
        # Центр Ташкента
        return folium.Map(location=[41.2995, 69.2401], zoom_start=12)
    
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
        fill_color="#3186cc",
        fill_opacity=0.3
    ).add_to(m)
    
    return m

# Основное приложение
st.title("🗺️ Интерактивная карта заведений")
st.markdown("---")

# Загружаем данные
with st.spinner("Загрузка данных из Google Sheets..."):
    locations = load_data_from_gsheet()

if not locations:
    st.error("Не удалось загрузить данные.")
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
    # Инициализируем координаты в session_state
    if 'coordinates' not in st.session_state:
        st.session_state.coordinates = {}
    
    # Показываем информацию в две колонки
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown(f"""
        ### 📋 Информация о заведении
        - **Название:** {selected_location['name']}
        - **Адрес:** {selected_location['address']}
        - **Время работы:** {selected_location['work_time']}
        """)
        
        # Кнопка для поиска на карте
        if st.button("🔍 Найти на карте", type="primary"):
            with st.spinner("Поиск адреса..."):
                lat, lon = geocode_address(selected_location['address'])
                if lat and lon:
                    st.session_state.coordinates[selected_name] = (lat, lon)
                    st.success("✅ Адрес найден!")
                    st.rerun()
                else:
                    st.error("❌ Адрес не найден. Попробуйте уточнить адрес.")
    
    with col2:
        st.info("""
        💡 **Инструкция:**
        1. Нажмите кнопку **"Найти на карте"**
        2. Дождитесь поиска адреса
        3. На карте появится маркер с информацией
        """)
    
    st.markdown("---")
    
    # Отображаем карту
    st.subheader("🗺️ Карта")
    
    # Проверяем, есть ли координаты для выбранного заведения
    if selected_name in st.session_state.coordinates:
        location_with_coords = selected_location.copy()
        location_with_coords["lat"], location_with_coords["lon"] = st.session_state.coordinates[selected_name]
        m = create_map(location_with_coords)
        folium_static(m, width=800, height=500)
    else:
        # Показываем карту с центром на Ташкенте
        m = folium.Map(location=[41.2995, 69.2401], zoom_start=12)
        st.info("👆 Нажмите кнопку **'Найти на карте'** выше, чтобы увидеть местоположение")
        folium_static(m, width=800, height=500)

# Добавляем боковую панель с информацией
with st.sidebar:
    st.markdown("""
    ## 📌 Информация
    
    ### О приложении
    Это приложение отображает заведения из Google Sheets на интерактивной карте.
    
    ### Как пользоваться:
    1. Выберите заведение из списка
    2. Нажмите **"Найти на карте"**
    3. Дождитесь загрузки карты
    4. Кликните на маркер, чтобы увидеть подробности
    
    ### Технологии:
    - **Streamlit** - веб-интерфейс
    - **Folium** - отображение карт
    - **OpenStreetMap** - геокодирование
    """)
    
    st.markdown("---")
    st.markdown("**📋 Список заведений:**")
    for loc in locations:
        st.markdown(f"- {loc['name']}")

# Footer
st.markdown("---")
st.caption(f"🗺️ Данные загружены | Карты OpenStreetMap | Обновлено: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
