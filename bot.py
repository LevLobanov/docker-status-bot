import datetime
from typing import Any
from aiogram import Bot, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import (Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton)
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from loguru import logger
from config import BOT_TOKEN, ADMIN_TG_ID
from dockerCommands import DokerCommandRunner
import textwrap


# Bot


bot = Bot(BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# Funcs


def parse_state(container_state: str) -> str:
    match container_state:
        case 'created':
            premoji = '⚒'
        case 'running':
            premoji = '🟢'
        case 'paused':
            premoji = '⏸'
        case 'restarting':
            premoji = '🟡'
        case 'removing':
            premoji = '🗑'
        case 'exited' | 'dead':
            premoji = '🔴'
        case _:
            premoji = '❔'
    return premoji + ' ' + container_state


def escape_markdown_v2(text: Any) -> str:
    escape_chars = r'*_[]()~`>#+-=|{}.!'
    return ''.join(f'\\{char}' if char in escape_chars else char for char in str(text))


# Keyboards


menu_kb = ReplyKeyboardMarkup(row_width=1)
menu_containers_btn = KeyboardButton(text="Containers")
menu_kb.add(menu_containers_btn)


def construct_container_menu_kb(container_id: str, container_state: str, docker_compose: bool) -> InlineKeyboardMarkup:
    container_menu_kb = InlineKeyboardMarkup(row_width=1)
    container_menu_kb.add(InlineKeyboardButton(text="📫 View logs", callback_data=f"Show_logs_{container_id}"))
    if container_state in ['dead', 'exited', 'created']:
        if docker_compose:
            container_menu_kb.add(InlineKeyboardButton(text="🟩 Start docker compose", callback_data=f"Manipulate_docker_compose_{container_id}_Start"))
        container_menu_kb.add(InlineKeyboardButton(text="🟩 Start", callback_data=f"Manipulate_container_{container_id}_Start"))
    elif container_state == 'running':
        container_menu_kb.add(InlineKeyboardButton(text="🟥 Stop", callback_data=f"Manipulate_container_{container_id}_Stop"))
        container_menu_kb.add(InlineKeyboardButton(text="⏸ Pause", callback_data=f"Manipulate_container_{container_id}_Pause"))
    elif container_state == 'paused':
        container_menu_kb.add(InlineKeyboardButton(text="🟥 Stop", callback_data=f"Manipulate_container_{container_id}_Stop"))
        container_menu_kb.add(InlineKeyboardButton(text="⏯ Unpause", callback_data=f"Manipulate_container_{container_id}_Unpause"))
    container_menu_kb.add(InlineKeyboardButton("🔄 Refresh", callback_data=f"Refresh_{container_id}"))
    return container_menu_kb


def construct_back_container_kb(container_id: str) -> InlineKeyboardMarkup:
    back_container_kb = InlineKeyboardMarkup(row_width=1)
    back_container_kb.add(InlineKeyboardButton(text="Back to container", callback_data=f"Container_{container_id}"))
    return back_container_kb
    

# Handlers


async def on_startup(_):
    logger.info("running...")
    await bot.send_message(ADMIN_TG_ID, "Im Running\n\n/start")


async def on_shutdown(_):
    logger.info("shutting down...")


@dp.message_handler(commands=["start"], state="*", user_id=ADMIN_TG_ID)
async def on_start(message: Message, state: FSMContext):
    await message.answer(f"Docker info panel, welcome {message.from_user.full_name}!", reply_markup=menu_kb)
    await state.finish()


@dp.message_handler(text=["Containers", "New list of containers"], user_id=ADMIN_TG_ID)
async def list_containers(message: Message):
    containers = await DokerCommandRunner.list_containers()
    containers_inline_kb = InlineKeyboardMarkup(width=1)
    for container in containers:
        containers_inline_kb.add(InlineKeyboardButton(
            text=f"{parse_state(container.State)} | {container.Names}",
            callback_data=f"Container_{container.ID}"
        ))
    await message.answer("Containers", reply_markup=containers_inline_kb)


@dp.callback_query_handler(text_startswith="Container_", user_id=ADMIN_TG_ID)
async def container_info(callback: CallbackQuery):
    container = [container for container in await DokerCommandRunner.list_containers() if container.ID == callback.data[10:]]
    if container:
        container = container[0]
        networks = "\n\t".join(container.Networks) if container.Networks else "NO NETWORKS"
        ports = "\n\t".join(container.Ports) if container.Ports else "NO PORT MAPPINGS"
        mounts = "\n\t".join(container.Mounts) if container.Mounts else "NO VOLUMES"
        await bot.send_message(chat_id=callback.from_user.id,
                                text=textwrap.dedent(f'''
                                    📦 Container\t*{escape_markdown_v2(container.Names)}* \\({container.ID}\\)

                                    {parse_state(container.State)} \\| {escape_markdown_v2(container.Status)}
                                
                                    💾 Image: *{escape_markdown_v2(container.Image)}*
                                    🕸 Networks: {escape_markdown_v2(networks)}
                                    🔌 Ports: {escape_markdown_v2(ports)}
                                    ⌚ Running for: {escape_markdown_v2(container.RunningFor)}
                                    💽 Size: {escape_markdown_v2(container.Size)}
                                    🗂 Mounts: {escape_markdown_v2(mounts)}
                                    🗃 Docker compose: {'*' + escape_markdown_v2(container.Labels.get('com.docker.compose.project')) + '*'
                                                        if container.Compose
                                                        else "NOT IN DOCKER COMPOSE"}
                                '''),
                                parse_mode='MarkdownV2',
                                reply_markup=construct_container_menu_kb(container.ID, container.State, container.Compose))
    else:
        await bot.send_message(chat_id=callback.from_user.id,
                               text="No container with given ID has been found!")
    await callback.answer()


@dp.callback_query_handler(text_startswith="Show_logs_", user_id=ADMIN_TG_ID)
async def show_logs(callback: CallbackQuery):
    logs = await DokerCommandRunner.show_container_logs(callback.data[10:])
    if logs:
        await bot.send_message(callback.from_user.id,
                               f"Last 25 lines of logs:\n\n{logs}",
                               reply_markup=construct_back_container_kb(callback.data[10:]))
    elif logs is not None:
        await bot.send_message(callback.from_user.id,
                               f"Last 25 lines of logs:\n\n_Empty_",
                               parse_mode="MarkdownV2",
                               reply_markup=construct_back_container_kb(callback.data[10:]))
    else:
        await bot.send_message(callback.from_user.id,
                               "No container with given ID has been found!")
    await callback.answer()


@dp.callback_query_handler(text_startswith="Refresh_", user_id=ADMIN_TG_ID)
async def refresh_container_info(callback: CallbackQuery):
    message = callback.message
    container = [container for container in await DokerCommandRunner.list_containers() if container.ID == callback.data[8:]]
    if container:
        container = container[0]
        networks = "\n\t".join(container.Networks) if container.Networks else "NO NETWORKS"
        ports = "\n\t".join(container.Ports) if container.Ports else "NO PORT MAPPINGS"
        mounts = "\n\t".join(container.Mounts) if container.Mounts else "NO VOLUMES"
        if container.State != message.text.split("\n\n")[1].split(" ")[1]:
            await message.edit_text(text=textwrap.dedent(f'''
                                        📦 Container\t*{escape_markdown_v2(container.Names)}* \\({container.ID}\\)

                                        {parse_state(container.State)} \\| {escape_markdown_v2(container.Status)}
                                    
                                        💾 Image: *{escape_markdown_v2(container.Image)}*
                                        🕸 Networks: {escape_markdown_v2(networks)}
                                        🔌 Ports: {escape_markdown_v2(ports)}
                                        ⌚ Running for: {escape_markdown_v2(container.RunningFor)}
                                        💽 Size: {escape_markdown_v2(container.Size)}
                                        🗂 Mounts: {escape_markdown_v2(mounts)}
                                        🗃 Docker compose: {'*' + escape_markdown_v2(container.Labels.get('com.docker.compose.project')) + '*'
                                                            if container.Compose
                                                            else "NOT IN DOCKER COMPOSE"}
                                    '''),
                                    parse_mode='MarkdownV2',
                                    reply_markup=construct_container_menu_kb(container.ID, container.State, container.Compose))
            await callback.answer()
        else:
            await callback.answer("Nothing changed")
    else:
        await message.edit_text("No container with given ID has been found! Seems it has been deleted...")
        await callback.answer()


@dp.callback_query_handler(text_startswith="Manipulate_container_", user_id=ADMIN_TG_ID)
async def manipulate_container(callback: CallbackQuery):
    timer_start = datetime.datetime.now()
    container_id, operation = callback.data.split("_")[-2:]
    message = await bot.send_message(callback.from_user.id, "Executing...\tThis may take some time")
    match operation:
        case 'Start':
            await DokerCommandRunner.up_container(container_id)
        case 'Stop':
            await DokerCommandRunner.stop_container(container_id)
        case 'Pause':
            await DokerCommandRunner.pause_container(container_id)
        case 'Unpause':
            await DokerCommandRunner.unpause_container(container_id)
    time_took = datetime.datetime.now() - timer_start
    await message.edit_text(f"{operation} *{escape_markdown_v2(container_id)}* Complete in *{escape_markdown_v2(time_took.seconds)}s*",
                            parse_mode="MarkdownV2")
    callback.data = "Refresh_" + container_id
    await refresh_container_info(callback)


@dp.callback_query_handler(text_startswith="Manipulate_docker_compose_", user_id=ADMIN_TG_ID)
async def manipulate_docker_compose(callback: CallbackQuery):
    timer_start = datetime.datetime.now()
    container_id, operation = callback.data.split("_")[-2:]
    print(container_id)
    message = await bot.send_message(callback.from_user.id, "Executing...\tThis may take some time")
    match operation:
        case 'Start':
            await DokerCommandRunner.docker_compose_up(container_id)
    time_took = datetime.datetime.now() - timer_start
    await message.edit_text(f"Docker compose {operation} *{escape_markdown_v2(container_id)}* Complete in *{escape_markdown_v2(time_took.seconds)}s*",
                            parse_mode="MarkdownV2")
    await bot.send_message(callback.from_user.id,
                           "Docker compose operations might change ID of container\n\nButtons on old messages might not work",
                           reply_markup=ReplyKeyboardMarkup().add(KeyboardButton(text="New list of containers")))
    callback.data = "Refresh_" + container_id
    await refresh_container_info(callback)
