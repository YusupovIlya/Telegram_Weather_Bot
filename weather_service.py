import datetime
import os
from datetime import date
import math
import aiohttp


WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

async def get_weather_info(url) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data
async def get_weather_by_city(city: str) -> dict:
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru'
    data = await get_weather_info(url)
    return data
async def get_weather_by_location(location) -> dict:
    url = f'http://api.openweathermap.org/data/2.5/weather?lat={location.latitude}&lon={location.longitude}&appid={WEATHER_API_KEY}&units=metric&lang=ru'
    data = await get_weather_info(url)
    return data

async def get_weather_hourly_forecast_by_city(city: str) -> dict:
    url = f'http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru'
    data = await get_weather_info(url)
    return data

async def get_weather_hourly_forecast_by_location(location) -> dict:
    url = f'http://api.openweathermap.org/data/2.5/forecast?lat={location.latitude}&lon={location.longitude}&appid={WEATHER_API_KEY}&units=metric&lang=ru'
    data = await get_weather_info(url)
    return data

def get_info_from_forecast_response(forecast_data: dict, type: str) -> str:
    if(type == "today"):
        need_date = date.today()
        response = f'Прогноз погоды на сегодня - {date.today()}:\n'
    else:
        need_date = date.today() + + datetime.timedelta(days=1)
        response = f'Прогноз погоды на завтра - {need_date}:\n'

    data = filter(lambda x: x['dt_txt'].split()[0] == str(need_date), forecast_data['list'])

    for forecast in data:
        weather_description = forecast["weather"][0]["main"]

        if weather_description in code_to_smile:
            wd = code_to_smile[weather_description]
        else:
            wd = "Посмотри в окно, я не понимаю, что там за погода..."
        time = forecast['dt_txt']
        temp = forecast['main']['temp']
        response += f"{time}: {wd}, Температура: {temp}°C\n"
    return response


def get_info_from_current_weather_respone(data: dict):
    if data['cod'] == 200:
        # получаем значение погоды
        weather_description = data["weather"][0]["main"]

        if weather_description in code_to_smile:
            wd = code_to_smile[weather_description]
        else:
            wd = "Посмотри в окно, я не понимаю, что там за погода..."

        city = data["name"]
        cur_temp = data["main"]["temp"]
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind = data["wind"]["speed"]

        sunrise_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
        sunset_timestamp = datetime.datetime.fromtimestamp(data["sys"]["sunset"])

        # продолжительность дня
        length_of_the_day = datetime.datetime.fromtimestamp(data["sys"]["sunset"]) - datetime.datetime.fromtimestamp(data["sys"]["sunrise"])
        result = f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n" + f"Погода в городе: {city}\nТемпература: {cur_temp}°C {wd}\n" + f"Влажность: {humidity}%\nДавление: {math.ceil(pressure / 1.333)} мм.рт.ст\nВетер: {wind} м/с \n" + f"Восход солнца: {sunrise_timestamp}\nЗакат солнца: {sunset_timestamp}\nПродолжительность дня: {length_of_the_day}\n" + f"Хорошего дня!"
        return result
    else:
        return f"Введенное место не найдено."

code_to_smile = {
     "Clear": "Ясно \U00002600",
     "Clouds": "Облачно \U00002601",
     "Rain": "Дождь \U00002614",
     "Drizzle": "Дождь \U00002614",
     "Thunderstorm": "Гроза \U000026A1",
     "Snow": "Снег \U0001F328",
     "Mist": "Туман \U0001F32B"
}