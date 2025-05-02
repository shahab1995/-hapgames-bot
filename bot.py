import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import pandas as pd
import os

API_TOKEN = '5033502116:AAEhj3j8rE0gBGmQ0amXH9HEWy10XXF1NvQ'
ADMIN_ID = 132035351
data_file = 'orders.xlsx'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- مراحل ربات ---
class Order(StatesGroup):
    order_type = State()
    game = State()
    name = State()
    phone = State()
    address = State()
    photo = State()

# --- کیبوردها ---
main_kb = ReplyKeyboardMarkup(resize_keyboard=True).add("سفارش جدید", "مشکل در سفارش")
cancel_kb = ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف")

games_all = [
    "Unmatched", "Virus", "Masquerade", "You’ve Got Crabs",
    "Downforce", "قهرمانان سرگردان", "Coloretto", "Point Salad", "Antidote",
    "محصولات جانبی"
]
games_available = [
    "Unmatched", "Virus", "Masquerade", "You’ve Got Crabs", "محصولات جانبی"
]

# --- شروع ---
@dp.message_handler(commands='start', state='*')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("سلام! لطفاً نوع درخواست را انتخاب کن:", reply_markup=main_kb)
    await Order.order_type.set()

@dp.message_handler(lambda m: m.text == "انصراف", state='*')
async def cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("لغو شد. برای شروع دوباره /start را بزن", reply_markup=main_kb)

# --- انتخاب نوع سفارش ---
@dp.message_handler(state=Order.order_type)
async def get_type(message: types.Message, state: FSMContext):
    if message.text not in ["سفارش جدید", "مشکل در سفارش"]:
        await message.answer("لطفاً یکی از گزینه‌ها را انتخاب کن.")
        return
    await state.update_data(order_type=message.text)

    games = games_all if message.text == "مشکل در سفارش" else games_available
    game_kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for g in games:
        game_kb.add(KeyboardButton(g))
    game_kb.add(KeyboardButton("انصراف"))

    await message.answer("بازی مورد نظر را انتخاب کن:", reply_markup=game_kb)
    await Order.game.set()

# --- دریافت بازی ---
@dp.message_handler(state=Order.game)
async def get_game(message: types.Message, state: FSMContext):
    await state.update_data(game=message.text)
    await message.answer("نام و نام خانوادگی:", reply_markup=cancel_kb)
    await Order.name.set()

# --- بقیه مراحل ---
@dp.message_handler(state=Order.name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("شماره تماس:")
    await Order.phone.set()

@dp.message_handler(state=Order.phone)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("آدرس کامل:")
    await Order.address.set()

@dp.message_handler(state=Order.address)
async def get_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    data = await state.get_data()
    if data['order_type'] == "مشکل در سفارش":
        await message.answer("لطفاً یک عکس از مشکل ارسال کن:")
        await Order.photo.set()
    else:
        await save_data(message, state)

@dp.message_handler(content_types=types.ContentType.PHOTO, state=Order.photo)
async def get_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await save_data(message, state)

# --- ذخیره اطلاعات ---
async def save_data(message: types.Message, state: FSMContext):
    data = await state.get_data()
    df_row = {
        "نوع": data["order_type"],
        "بازی": data["game"],
        "نام": data["name"],
        "شماره": data["phone"],
        "آدرس": data["address"],
        "عکس": data.get("photo", "")
    }

    df = pd.DataFrame([df_row])
    if os.path.exists(data_file):
        old = pd.read_excel(data_file)
        df = pd.concat([old, df], ignore_index=True)
    df.to_excel(data_file, index=False)

    msg = f"""درخواست جدید:
نوع: {data['order_type']}
بازی: {data['game']}
نام: {data['name']}
شماره: {data['phone']}
آدرس: {data['address']}"""
    await bot.send_message(ADMIN_ID, msg)
    if "photo" in data:
        await bot.send_photo(ADMIN_ID, data["photo"])
    await bot.send_document(ADMIN_ID, InputFile(data_file))

    await message.answer("درخواست ثبت شد. با تشکر!", reply_markup=main_kb)
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
