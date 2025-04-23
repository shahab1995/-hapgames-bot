import os
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from openpyxl import Workbook, load_workbook

# بارگذاری توکن از متغیر محیطی
API_TOKEN = os.getenv("7895495605:AAFxv2IAfDEJnor0U5KZ3i7qn5R4XNPeiFk")
if not API_TOKEN:
    raise RuntimeError("لطفاً متغیر محیطی BOT_API_TOKEN را ست کنید!")

# شناسهٔ ادمین
ADMIN_ID = int(os.getenv("ADMIN_ID", "132035351"))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# لیست بازی‌ها
available_games = ["Unmatched", "Virus", "Masquerade", "You’ve Got Crabs", "محصولات جانبی"]
all_games = ["Unmatched", "Virus", "Masquerade", "You’ve Got Crabs",
             "Downforce", "قهرمانان سرگردان", "Coloretto", "Point Salad",
             "Antidote", "محصولات جانبی"]

class OrderForm(StatesGroup):
    choosing_type = State()
    choosing_game = State()
    entering_name = State()
    entering_phone = State()
    entering_province = State()
    entering_city = State()
    entering_postal_code = State()
    entering_address = State()
    sending_photo = State()

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message, state: FSMContext):
    await state.finish()
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("سفارش جدید", "گزارش مشکل")
    await message.answer(
        "به ربات هُپ گیمز خوش اومدی!\nیکی از گزینه‌ها رو انتخاب کن:",
        reply_markup=kb
    )
    await OrderForm.choosing_type.set()

@dp.message_handler(lambda m: m.text in ["سفارش جدید", "گزارش مشکل"], state=OrderForm.choosing_type)
async def choose_type(message: types.Message, state: FSMContext):
    await state.update_data(order_type=message.text)
    games = available_games if message.text == "سفارش جدید" else all_games
    kb = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.add(*games).add("انصراف")
    await message.answer("بازی مورد نظر رو انتخاب کن:", reply_markup=kb)
    await OrderForm.choosing_game.set()

@dp.message_handler(lambda m: m.text in available_games + all_games, state=OrderForm.choosing_game)
async def choose_game(message: types.Message, state: FSMContext):
    await state.update_data(game=message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف")
    await message.answer("نام و نام خانوادگی:", reply_markup=kb)
    await OrderForm.entering_name.set()

@dp.message_handler(state=OrderForm.entering_name)
async def enter_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف")
    await message.answer("شماره تماس:", reply_markup=kb)
    await OrderForm.entering_phone.set()

@dp.message_handler(state=OrderForm.entering_phone)
async def enter_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف")
    await message.answer("استان:", reply_markup=kb)
    await OrderForm.entering_province.set()

@dp.message_handler(state=OrderForm.entering_province)
async def enter_province(message: types.Message, state: FSMContext):
    await state.update_data(province=message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف")
    await message.answer("شهر:", reply_markup=kb)
    await OrderForm.entering_city.set()

@dp.message_handler(state=OrderForm.entering_city)
async def enter_city(message: types.Message, state: FSMContext):
    await state.update_data(city=message.text)
    data = await state.get_data()
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف")
    if data.get("order_type") == "گزارش مشکل":
        # مستقیم به ارسال عکس می‌رود
        await message.answer("در صورت وجود عکس از مشکل، لطفاً ارسال کن یا بزن روی انصراف.", reply_markup=kb)
        await OrderForm.sending_photo.set()
    else:
        await message.answer("کد پستی:", reply_markup=kb)
        await OrderForm.entering_postal_code.set()

@dp.message_handler(state=OrderForm.entering_postal_code)
async def enter_postal_code(message: types.Message, state: FSMContext):
    await state.update_data(postal_code=message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف")
    await message.answer("آدرس کامل:", reply_markup=kb)
    await OrderForm.entering_address.set()

@dp.message_handler(state=OrderForm.entering_address)
async def enter_address(message: types.Message, state: FSMContext):
    await state.update_data(address=message.text)
    kb = ReplyKeyboardMarkup(resize_keyboard=True).add("انصراف")
    await message.answer("در صورت وجود عکس از مشکل، لطفاً ارسال کن یا بزن روی انصراف.", reply_markup=kb)
    await OrderForm.sending_photo.set()

@dp.message_handler(content_types=['photo'], state=OrderForm.sending_photo)
async def get_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    file_id = message.photo[-1].file_id
    # ارسال پیام و عکس به ادمین
    await bot.send_photo(ADMIN_ID, file_id, caption=f"درخواست جدید:\n{data}")
    # ارسال فایل Excel به ادمین
    save_to_excel(data)
    await bot.send_document(ADMIN_ID, InputFile("orders.xlsx"))
    await message.answer("درخواست ثبت شد! ممنون از شما.", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

@dp.message_handler(lambda m: m.text == "انصراف", state="*")
async def cancel_handler(message: types.Message, state: FSMContext):
    await message.answer("فرآیند لغو شد. برای شروع دوباره /start رو بزن.", reply_markup=types.ReplyKeyboardRemove())
    await state.finish()

def save_to_excel(data: dict):
    """ذخیرهٔ اطلاعات در orders.xlsx"""
    file_path = "orders.xlsx"
    if os.path.exists(file_path):
        wb = load_workbook(file_path)
        ws = wb.active
    else:
        wb =
