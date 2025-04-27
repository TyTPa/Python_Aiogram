import asyncio
import os
import requests
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters.state import StateFilter
from config import TOKEN, OWM_API_KEY

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Определение состояний
class WeatherStates(StatesGroup):
    waiting_for_period = State()

cities = {
    '/m': 'Moscow',
    '/n': 'Veliky Novgorod',
    '/v': 'Vienna',
    '/s': 'Saint Petersburg'
}

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("Приветики, я бот!")

@dp.message(Command(commands=['help']))
async def help_command(message: Message):
    await message.answer("Этот бот умеет выполнять команды:\n/start\n/help\n /m\n/n\n/s\n/v")


def get_weather(city_name, period='today'):
    base_url = "http://api.openweathermap.org/data/2.5/"
    if period == 'today':
        url = f"{base_url}weather?q={city_name}&appid={OWM_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        if data.get('cod') != 200:
            return "Не удалось получить данные о погоде."

        temp = data['main']['temp']
        description = data['weather'][0]['description']
        return f"Погода в {city_name}: {description}, температура {temp}°C."
    elif period == '7days':
        url = f"{base_url}forecast/daily?q={city_name}&cnt=7&appid={OWM_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        if data.get('cod') != '200':
            return "Не удалось получить данные о погоде."

        forecast = []
        for day in data['list']:
            day_temp = day['temp']['day']
            day_description = day['weather'][0]['description']
            forecast.append(f"{day_temp}°C, {day_description}")
        return f"Прогноз на 8 дней для {city_name}: " + ", ".join(forecast)
@dp.message(Command(commands=['m', 'n', 'v', 's']))
async def start_command(message: Message, state: FSMContext):
    city_command = message.text
    city_name = cities.get(city_command, None)
    if city_name:
        await message.reply(f"Вы хотите получить прогноз погоды для {city_name} на сегодня или на 8 дней? (введите '1' или '8')")
        await state.set_state(WeatherStates.waiting_for_period)
        await state.update_data(city=city_name)
    else:
        await message.reply("Неизвестная команда.")

@dp.message(StateFilter(WeatherStates.waiting_for_period))
async def get_weather_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    city_name = data.get('city')
    period = message.text.lower()

    if period == '1':
        weather_data = get_weather(city_name, 'today')
    elif period == '8':
        weather_data = get_weather(city_name, '7days')
    else:
        await message.reply("Пожалуйста, введите '1' если хотите прогноз на сегодня или '8' если на будущую неделю.")
        return

    await message.reply(weather_data)
    await state.clear()

async def main():
    # Запуск диспетчера
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
