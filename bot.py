from aiogram import Bot, Dispatcher, executor, types
import logging

API_TOKEN = 5033502116:AAEhj3j8rE0gBGmQ0amXH9HEWy10XXF1NvQ

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("سلام! به ربات Hope Games خوش اومدی.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
