import logging
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = ' 5033502116:AAEhj3j8rE0gBGmQ0amXH9HEWy10XXF1NvQ'
ADMIN_ID =  132035351

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

data_file = "data.xlsx"

class OrderState(StatesGroup):
    start = State()
    choose_type = State()
    choose_game = State()
    choose_additional = State()
    enter_name = State()
    enter_phone = State()
    enter_city = State()
    enter_postcode = State()
    enter_address = State()
    enter_problem_photo = State()
    confirm = State()

main_kb = ReplyKeyboardMarkup(resize_keyboard=True)
main_kb.add(KeyboardButton("سفارش جدید"), KeyboardButton("مشکل در سفارش"))

cancel_kb = ReplyKeyboardMarkup(resize_keyboard=True)
cancel_kb.add(KeyboardButton("انصراف"))

@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("به ربات Hope Games خوش آمدید. لطفاً یکی از گزینه‌ها را انتخاب کنید:", reply_markup=main_kb)
    await OrderState.start.set()

@dp.message_handler(lambda msg: msg.text == "انصراف", state='*')
async def cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("انصراف داده شد. برای شروع دوباره /start را بزنید", reply_markup=main_kb)

@dp.message_handler(state=OrderState.start)
async def choose_type(message: types.Message, state: FSMContext):
    if message.text not in ["سفارش جدید", "مشکل در سفارش"]:
        await message.answer("لطفاً یکی از گزینه‌ها را انتخاب کنید.")
        return
    await state.update_data(order_type=message.text)

    game_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    games_all = [
        "Unmatched", "Virus", "Masquerade", "You’ve Got Crabs",
        "Downforce", "قهرمانان سرگردان", "Coloretto", "Point Salad", "Antidote",
        "محصولات جانبی"
    ]
    games_available = ["Unmatched", "Virus", "Masquerade", "You’ve Got Crabs", "محصولات جانبی"]

    games = games_all if message.text == "مشکل در سفارش" else games_available

    for g in games:
        game_kb.add(KeyboardButton(g))
    game_kb.add(KeyboardButton("انصراف"))

    await message.answer("لطفاً بازی را انتخاب کنید:", reply_markup=game_kb)
    await OrderState.choose_game.set()

@dp.message_handler(state=OrderState.choose_game)
async def get_game(message: types.Message, state: FSMContext):
    await state.update_data(game=message.text)
    await message.answer("نام و نام خانوادگی:", reply_markup=cancel_kb)
    await OrderState.enter_name.set()

@dp.message_handler(state=OrderState.enter_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("شماره تماس:", reply_markup=cancel_kb)
    await OrderState.enter_phone.set()

@dp.message_handler(state=OrderState.enter_phone)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer("استان:", reply_markup=cancel_kb)
    await OrderState.enter_city.set()

@dp.message_handler(state=OrderState.enter_city)
async def get_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("کد پستی:", reply_markup=cancel_kb)
    await OrderState.enter_postcode.set()

@dp.message_handler(state=OrderState.enter_postcode)
async def get_postcode(message: types.Message, state: FSMContext):
    await state.update_data(postcode=message.text)
    await message.answer("آدرس کامل:", reply_markup=cancel_kb)
    await OrderState.enter_address.set()

@dp.message_handler(state=OrderState.enter_address)
async def get_address(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if data["order_type"] == "مشکل در سفارش":
        await message.answer("لطفاً یک عکس از مشکل ارسال کنید", reply_markup=cancel_kb)
        await state.update_data(address=message.text)
        await OrderState.enter_problem_photo.set()
    else:
        await state.update_data(address=message.text)
        await finish_and_save(message, state)

@dp.message_handler(content_types=types.ContentType.PHOTO, state=OrderState.enter_problem_photo)
async def get_problem_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await finish_and_save(message, state)

async def finish_and_save(message: types.Message, state: FSMContext):
    data = await state.get_data()

    # ذخیره در اکسل
    df = pd.DataFrame([{
        "نوع": data["order_type"],
        "بازی": data["game"],
        "نام": data["name"],
        "شماره": data["phone"],
        "استان": data["city"],
        "کد پستی": data["postcode"],
        "آدرس": data["address"]
    }])

    if os.path.exists(data_file):
        old = pd.read_excel(data_file)
        df = pd.concat([old, df], ignore_index=True)

    df.to_excel(data_file, index=False)

    # ارسال به ادمین
    await bot.send_message(ADMIN_ID, f"درخواست جدید:\n\n{data}")
    if "photo" in data:
        await bot.send_photo(ADMIN_ID, data["photo"])

    await bot.send_document(ADMIN_ID, InputFile(data_file))
    await message.answer("درخواست ثبت شد. ممنون از شما", reply_markup=main_kb)
    await state.finish()

if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
