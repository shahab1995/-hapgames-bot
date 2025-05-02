import logging
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = '7984419385:AAHCEermgzxAHRRHPsLvDUIu7iYoe2NHtxI'
ADMIN_ID = 132035351  # آیدی عددی ادمین (ربات باید قبلاً بهش پیام داده باشه)

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

data_file = "orders.xlsx"

# حالت‌های سفارش
class OrderState(StatesGroup):
    start = State()
    choose_type = State()
    choose_game = State()
    enter_name = State()
    enter_phone = State()
    enter_city = State()
    enter_postcode = State()
    enter_address = State()
    enter_photo = State()

# کیبوردها
main_kb = ReplyKeyboardMarkup(resize_keyboard=True).add("سفارش جدید", "مشکل در سفارش")
cancel_kb = ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف")

@dp.message_handler(commands=['start'], state='*')
async def start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("به ربات Hope Games خوش آمدید. یکی از گزینه‌ها را انتخاب کنید:", reply_markup=main_kb)
    await OrderState.start.set()

@dp.message_handler(lambda m: m.text == "انصراف", state='*')
async def cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("انصراف داده شد. برای شروع دوباره /start را بزنید", reply_markup=main_kb)

@dp.message_handler(state=OrderState.start)
async def choose_type(message: types.Message, state: FSMContext):
    if message.text not in ["سفارش جدید", "مشکل در سفارش"]:
        return await message.answer("لطفاً یکی از گزینه‌ها را انتخاب کنید.")
    
    await state.update_data(order_type=message.text)

    all_games = [
        "Unmatched", "Virus", "Masquerade", "You’ve Got Crabs", "Downforce",
        "قهرمانان سرگردان", "Coloretto", "Point Salad", "Antidote", "محصولات جانبی"
    ]
    available_games = ["Unmatched", "Virus", "Masquerade", "You’ve Got Crabs", "محصولات جانبی"]

    games = all_games if message.text == "مشکل در سفارش" else available_games

    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for g in games:
        kb.add(KeyboardButton(g))
    kb.add(KeyboardButton("انصراف"))

    await message.answer("بازی مورد نظر را انتخاب کنید:", reply_markup=kb)
    await OrderState.choose_game.set()

@dp.message_handler(state=OrderState.choose_game)
async def get_game(message: types.Message, state: FSMContext):
    data = await state.get_data()
    games = (
        ["Unmatched", "Virus", "Masquerade", "You’ve Got Crabs", "Downforce",
         "قهرمانان سرگردان", "Coloretto", "Point Salad", "Antidote", "محصولات جانبی"]
        if data["order_type"] == "مشکل در سفارش"
        else ["Unmatched", "Virus", "Masquerade", "You’ve Got Crabs", "محصولات جانبی"]
    )
    if message.text not in games:
        return await message.answer("لطفاً یکی از بازی‌های موجود را انتخاب کنید.")

    await state.update_data(game=message.text)
    await message.answer("نام و نام خانوادگی:", reply_markup=cancel_kb)
    await OrderState.enter_name.set()

@dp.message_handler(state=OrderState.enter_name)
async def get_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("شماره تماس:", reply_markup=cancel_kb)
    await OrderState.enter_phone.set()

@dp.message_handler(state=OrderState.enter_phone)
async def get_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text.strip())
    await message.answer("استان:", reply_markup=cancel_kb)
    await OrderState.enter_city.set()

@dp.message_handler(state=OrderState.enter_city)
async def get_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text.strip())
    await message.answer("کد پستی:", reply_markup=cancel_kb)
    await OrderState.enter_postcode.set()

@dp.message_handler(state=OrderState.enter_postcode)
async def get_postcode(message: types.Message, state: FSMContext):
    await state.update_data(postcode=message.text.strip())
    await message.answer("آدرس کامل:", reply_markup=cancel_kb)
    await OrderState.enter_address.set()

@dp.message_handler(state=OrderState.enter_address)
async def get_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    data = await state.get_data()
    if data["order_type"] == "مشکل در سفارش":
        await message.answer("لطفاً یک عکس از مشکل ارسال کنید.", reply_markup=cancel_kb)
        await OrderState.enter_photo.set()
    else:
        await finish_order(message, state)

@dp.message_handler(content_types=types.ContentType.PHOTO, state=OrderState.enter_photo)
async def get_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await finish_order(message, state)

@dp.message_handler(state=OrderState.enter_photo)
async def photo_required(message: types.Message):
    await message.answer("لطفاً فقط عکس ارسال کنید.")

async def finish_order(message: types.Message, state: FSMContext):
    data = await state.get_data()
    df_data = {
        "نوع": data["order_type"],
        "بازی": data["game"],
        "نام": data["name"],
        "شماره": data["phone"],
        "استان": data["city"],
        "کد پستی": data["postcode"],
        "آدرس": data["address"],
        "عکس": data.get("photo", "")
    }

    df = pd.DataFrame([df_data])
    if os.path.exists(data_file):
        old_df = pd.read_excel(data_file)
        df = pd.concat([old_df, df], ignore_index=True)
    df.to_excel(data_file, index=False)

    # ارسال برای ادمین
    try:
        text = "\n".join(f"{k}: {v}" for k, v in df_data.items() if k != "عکس")
        await bot.send_message(ADMIN_ID, f"درخواست جدید:\n\n{text}")
        if "photo" in data:
            await bot.send_photo(ADMIN_ID, data["photo"])
        await bot.send_document(ADMIN_ID, InputFile(data_file))
    except Exception as e:
        await message.answer("ارسال به ادمین با خطا مواجه شد.")

    await message.answer("درخواست شما با موفقیت ثبت شد. با تشکر!", reply_markup=main_kb)
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
