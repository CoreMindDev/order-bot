import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db import init_db, save_order, get_orders, get_new_orders, set_done, set_in_progress, get_order

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден. Установи переменную окружения.")
ADMIN_ID = 7756350786
MIN_BUDGET = 50

class OrderState(StatesGroup):
    name = State()
    task = State()
    budget = State()

def parse_budget(text: str) -> int | None:
    import re
    match = re.search(r"\d+", text)
    return int(match.group()) if match else None

async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Здравствуйте! Как тебя зовут?")
    await state.set_state(OrderState.name)

async def get_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2:
        await message.answer("Имя слишком короткое. Введи имя ещё раз.")
        return
    await state.update_data(name=name)
    await message.answer(f"Приятно познакомиться, {name}")
    await message.answer("Что тебе нужно сделать?")
    await state.set_state(OrderState.task)

async def get_task(message: Message, state: FSMContext):
    task = message.text.strip()
    if len(task) < 5:
        await message.answer("Опиши задачу чуть подробнее.")
        return
    await state.update_data(task=task)
    await message.answer("💰 Укажи примерный бюджет (например: 50$, 3000₽)")
    await state.set_state(OrderState.budget)

async def get_budget(message: Message, state: FSMContext):
    budget_text = message.text.strip()
    budget_value = parse_budget(budget_text)
    if budget_value is None:
        await message.answer("❌ Укажи бюджет числом (например: 50, 100$)")
        return
    if budget_value < MIN_BUDGET:
        await message.answer(
            f"❌ Минимальный бюджет - эквивалент {MIN_BUDGET}$.\n"
            "К сожалению, мы не сможем взять эту заявку."
        )
        await state.clear()
        return
    data = await state.get_data()
    name = data["name"]
    task = data["task"]
    username = message.from_user.username or "no_username"
    order_id = save_order(
        message.from_user.id,
        username,
        name,
        f"{task}\n\n💰 Бюджет: {budget_text}"
    )
    await message.bot.send_message(
        ADMIN_ID,
        f"📥 Новая заявка\n"
        f"ID: {order_id}\n"
        f"Имя: {name}\n"
        f"Юзер: @{username}\n"
        f"Задача: {task}\n"
        f"💰 Бюджет: {budget_text}"
    )
    await message.answer("✅ Заявка принята. Мы скоро с тобой свяжемся.")
    await state.clear()


async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Диалог отменён. Можешь начать заново командой /start")

async def show_orders(message: Message):
    if message.from_user.id != ADMIN_ID:
            await message.answer("⛔ у тебя нет доступа к этой команде.")
            return
    args = message.text.split()
    if len(args) > 1:
        if args[1] == "all":
            orders = get_orders()
            title = "📋 Все заявки:\n\n"
        elif args[1] == "done":
            orders = get_orders("done")
            title = "✅ Выполненные заявки:\n\n"
        elif args[1] == "work":
            orders = get_orders("in_progress")
            title = "🛠 В работе:\n\n"
        else:
            await message.answer("Используй: /orders | /orders all | /orders done | /orders work")
            return
    else:
        orders = get_new_orders()
        title = "📋 Новые заявки:\n\n"
    if not orders:
        await message.answer("Заявок нет.")
        return
    text = title
    for order_id, user_id, username, name, task, status in orders:
        text += (
            f"#{order_id}\n"
            f"Имя: {name}\n"
            f"Юзер: @{username}\n"
            f"Задача: {task}\n"
            f"Статус: {status}\n\n"
        )
    await message.answer(text)

async def done_order(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ у тебя нет доступа.")
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используй: /done <id>")
        return
    order_id = int(parts[1])
    if not set_done(order_id):
        await message.answer("❌ Заявка не найдена")
        return
    order = get_order(order_id)
    if not order:
        await message.answer("❌ Заявка не найдена")
        return
    user_id, username, name, task, status = order
    await message.bot.send_message(
        user_id,
        "✅ Ваша заявка выполнена.\n"
        "Спасибо за обращение!"
    )
    await message.answer(f"✅ Заявка #{order_id} отмечена как выполненная")

async def take_order(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ нет доступа")
        return
    parts = message.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Используй: /take <id>")
        return
    order_id = int(parts[1])
    if not set_in_progress(order_id):
        await message.answer("❌ Заявка не найдена")
        return
    order = get_order(order_id)
    if not order:
        await message.answer("❌ Заявка не найдена")
        return
    user_id, username, name, task, status = order
    await message.bot.send_message(
        user_id,
        "🛠 Ваша заявка взята в работу.\n"
        "Мы скоро свяжемся с вами."
    )
    await message.answer(f"🛠 Заявка #{order_id} взята в работу")


async def main():
    init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    dp.message.register(start, CommandStart())
    dp.message.register(cancel, Command("cancel"))
    dp.message.register(get_name, OrderState.name)
    dp.message.register(get_task, OrderState.task)
    dp.message.register(get_budget, OrderState.budget)
    dp.message.register(show_orders, Command("orders"))
    dp.message.register(done_order, Command("done"))
    dp.message.register(take_order, Command("take"))

    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())