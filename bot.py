import logging
import os
import pandas as pd
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = '5033502116:AAEhj3j8rE0gBGmQ0amXH9HEWy10XXF1NvQ'  # توکن واقعی‌ات رو جایگزین کن
ADMIN_ID = 123456789  # آی‌دی تلگرام خودت رو بذار

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

data_file = "data.xlsx"

class OrderState(StatesGroup):
    start = State()
    choose_game = State()
    enter_name = State()
    enter_phone = State()
    enter_city = State()
    enter_postcode = State()
    enter_address = State()
    enter_problem_photo = State()

# Inline keyboard for order type
type_kb = InlineKeyboardMarkup(row_width=2)
type_kb.add(
    InlineKeyboardButton("سفارش جدید", callback_data="type:new"),
    InlineKeyboardButton("مشکل در سفارش", callback_data="type:problem")
)

cancel_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("انصراف"))
main_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("/start"))

@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("به ربات Hope Games خوش آمدید. لطفاً نوع درخواست را انتخاب کنید:", reply_markup=type_kb)
    await OrderState.start.set()

@dp.message_handler(lambda msg: msg.text == "انصراف", state='*')
async def cancel(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("انصراف داده شد. برای شروع دوباره /start را بزنید", reply_markup=main_kb)

@dp.callback_query_handler(lambda c: c.data.startswith("type:"), state=OrderState.start)
async def process_order_type(callback_query: types.CallbackQuery, state: FSMContext):
    order_type = callback_query.data.split(":")[1]
    order_text = "سفارش جدید" if order_type == "new" else "مشکل در سفارش"
    await state.update_data(order_type=order_text)

    games_all = [
        "Unmatched", "Virus", "Masquerade", "You’ve Got Crabs",
        "Downforce", "قهرمانان سرگردان", "Coloretto", "Point Salad", "Antidote",
        "محصولات جانبی"
    ]
    games_available = ["Unmatched", "Virus", "Masquerade", "You’ve Got Crabs", "محصولات جانبی"]
    games = games_all if order_type == "problem" else games_available

    game_kb = InlineKeyboardMarkup(row_width=1)
    for game in games:
        game_kb.add(InlineKeyboardButton(game, callback_data=f"game:{game}"))

    await bot.edit_message_text(
        "لطفاً یکی از بازی‌ها را انتخاب کنید:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        reply_markup=game_kb
    )
    await OrderState.choose_game.set()

@dp.callback_query_handler(lambda c: c.data.startswith("game:"), state=OrderState.choose_game)
async def process_game(callback_query: types.CallbackQuery, state: FSMContext):
    game = callback_query.data.split(":", 1)[1]
    await state.update_data(game=game)

    await bot.edit_message_text(
        "نام و نام خانوادگی را وارد کنید:",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id
    )
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
    await state.update_data(address=message.text)
    
    if data["order_type"] == "مشکل در سفارش":
        await message.answer("لطفاً یک عکس از مشکل ارسال کنید", reply_markup=cancel_kb)
        await OrderState.enter_problem_photo.set()
    else:
        await finish_and_save(message, state)

@dp.message_handler(content_types=types.ContentType.PHOTO, state=OrderState.enter_problem_photo)
async def get_problem_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await finish_and_save(message, state)

@dp.message_handler(state=OrderState.enter_problem_photo)
async def handle_invalid_photo(message: types.Message):
    await message.answer("لطفاً یک عکس ارسال کنید.")

async def finish_and_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    df_data = {
        "نوع": data["order_type"],
        "بازی": data["game"],
        "نام": data["name"],
        "شماره": data["phone"],
        "استان": data["city"],
        "کد پستی": data["postcode"],
        "آدرس": data["address"]
    }
    if "photo" in data:
        df_data["عکس"] = data["photo"]

    df = pd.DataFrame([df_data])
    if os.path.exists(data_file):
        old_df = pd.read_excel(data_file)
        df = pd.concat([old_df, df], ignore_index=True)
    df.to_excel(data_file, index=False)

    admin_text = (
        f"درخواست جدید:\n\n"
        f"نوع: {data['order_type']}\n"
        f"بازی: {data['game']}\n"
        f"نام: {data['name']}\n"
        f"شماره: {data['phone']}\n"
        f"استان: {data['city']}\n"
        f"کد پستی: {data['postcode']}\n"
        f"آدرس: {data['address']}"
    )
    await bot.send_message(ADMIN_ID, admin_text)
    if "photo" in data:
        await bot.send_photo(ADMIN_ID, data["photo"])
    await bot.send_document(ADMIN_ID, InputFile(data_file))

    await message.answer("درخواست شما ثبت شد. با تشکر!", reply_markup=main_kb)
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
