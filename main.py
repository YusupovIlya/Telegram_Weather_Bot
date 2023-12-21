import asyncio
import logging
import os

import weather_service
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command, CommandObject
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types.bot_command import BotCommand
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

API_TOKEN = os.getenv("API_TOKEN")

type_location = ["Ввести вручную", "По геоопозиции"]

forecast_length = ['До конца дня', 'На завтра']

commands = [
    BotCommand(command="/start", description="Начать работу с ботом"),
    BotCommand(command="/weather", description="Узнать текущую погоду"),
    BotCommand(command="/forecast", description="Получить прогноз погоды")
]

# Включаем логирование, чтобы не пропустить важные сообщения
logging.basicConfig(level=logging.INFO)
# Объект бота
bot = Bot(token=API_TOKEN)
# Диспетчер
dp = Dispatcher()

class WeatherStates(StatesGroup):
    InputCity = State()
    TypeInput = State()
    InputLocation = State()
    isForecast = State()
    ForecastLength = State()

def make_row_keyboard(items):
    row = [KeyboardButton(text=item) for item in items]
    return ReplyKeyboardMarkup(keyboard=[row], resize_keyboard=True)

# Хэндлер на команду /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(f'Привет {message.from_user.first_name}\nЭто бот для определения погоды.\nИспользуй меню для работы.', reply_markup=ReplyKeyboardRemove())

@dp.message(Command('weather', 'forecast'))
async def ask_type_forecast(message: Message, state: FSMContext, command: CommandObject):
    await state.set_state(WeatherStates.isForecast)
    if(command.command == 'forecast'):
        await state.update_data(isForecast=True)
    else:
        await state.update_data(isForecast=False)
    await message.answer(text="Как определить место?", reply_markup=make_row_keyboard(type_location))
    await state.set_state(WeatherStates.TypeInput)


@dp.message(WeatherStates.TypeInput, F.text.in_(type_location))
async def ask_location(message: Message, state: FSMContext):
    type = message.text.strip()
    await state.update_data(TypeInput=type)
    if(type == 'Ввести вручную'):
        await message.answer(text="Введите название города, страны и т.д.", reply_markup=ReplyKeyboardRemove())
        await state.set_state(WeatherStates.InputCity)
    else:
        keyboard = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Определить местоположение', request_location=True)]], resize_keyboard=True)
        await message.answer("Нажмите кнопку, чтобы отправить геолокацию.", reply_markup=keyboard)
        await state.set_state(WeatherStates.InputLocation)

@dp.message(WeatherStates.TypeInput)
async def error_type_location(message: Message, state: FSMContext):
    type = message.text.strip()
    await message.answer(text=f"Неизвестный тип определения места - {type}", reply_markup=make_row_keyboard(type_location))

@dp.message(WeatherStates.ForecastLength, F.text.in_(forecast_length))
async def get_forecast(message: Message, state: FSMContext):
    data = dict()
    if(message.text == forecast_length[0]):
        data = await state.update_data(ForecastLength="today")
    else:
        data = await state.update_data(ForecastLength="tomorrow")

    if('InputCity' in data):
        weather_data = await weather_service.get_weather_hourly_forecast_by_city(data['InputCity'])
        await message.reply(weather_service.get_info_from_forecast_response(weather_data, data['ForecastLength']), reply_markup=ReplyKeyboardRemove())
    else:
        weather_data = await weather_service.get_weather_hourly_forecast_by_location(data['InputLocation'])
        await message.reply(weather_service.get_info_from_forecast_response(weather_data, data['ForecastLength']), reply_markup=ReplyKeyboardRemove())

    await state.clear()


@dp.message(WeatherStates.ForecastLength)
async def error_forecast_length(message: Message, state: FSMContext):
    type = message.text.strip()
    await message.answer(text=f"Неизвестный тип периода - {type}", reply_markup=make_row_keyboard(forecast_length))

@dp.message(WeatherStates.InputCity)
async def get_weather_city(message: Message, state: FSMContext):
    city = message.text.strip()
    data = await state.update_data(InputCity=city)
    if(data['isForecast'] == True):
        await get_forecast_type(message, state)
    else:
        await state.clear()
        weather_data = await weather_service.get_weather_by_city(city)
        await message.reply(weather_service.get_info_from_current_weather_respone(weather_data), reply_markup=ReplyKeyboardRemove())

@dp.message(WeatherStates.InputLocation)
async def get_weather_location(message: Message, state: FSMContext):
    location = message.location
    data = await state.update_data(InputLocation=location)
    if(data['isForecast'] == True):
        await get_forecast_type(message, state)
    else:
        await state.clear()
        weather_data = await weather_service.get_weather_by_location(location)
        await message.reply(weather_service.get_info_from_current_weather_respone(weather_data), reply_markup=ReplyKeyboardRemove())

async def get_forecast_type(message: types.Message, state: FSMContext):
    await message.answer(text="На какой период прогноз?", reply_markup=make_row_keyboard(forecast_length))
    await state.set_state(WeatherStates.ForecastLength)

async def set_commands():
    await bot.set_my_commands(commands)


# Запуск процесса поллинга новых апдейтов
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_until_complete(set_commands())
    loop.run_forever()
