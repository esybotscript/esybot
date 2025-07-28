#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import re
import sys
import json
import os
import importlib
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import traceback

# Aiogram imports для версии 3.21.0 - ИСПРАВЛЕНО
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, 
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InputFile, BufferedInputFile, FSInputFile,
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent,
    PreCheckoutQuery, ShippingQuery, ShippingOption, LabeledPrice,
    WebAppInfo, MenuButton, BotCommand, BotCommandScope,
    ChatMemberUpdated, PollAnswer, Poll, Dice,
    Sticker, Animation, Audio, Document, Video, VideoNote, Voice, 
    Contact, Location, Venue, PhotoSize
)
# УБРАН Text - он больше не существует в aiogram 3.21.0
from aiogram.filters import Command, StateFilter, ChatMemberUpdatedFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram.client.session.aiohttp import AiohttpSession

class CommandType(Enum):
    """Типы команд ESYBOT"""
    BOT_CONFIG = "bot_config"
    HANDLER = "handler"
    RESPONSE = "response"
    BUTTON = "button"
    MENU = "menu"
    STATE = "state"
    VARIABLE = "variable"
    CONDITION = "condition"
    LOOP = "loop"
    API_CALL = "api_call"
    PYTHON_CODE = "python_code"
    MIDDLEWARE = "middleware"
    DATABASE = "database"
    WEBHOOK = "webhook"
    PAYMENT = "payment"
    INLINE = "inline"

@dataclass
class ESYBOTCommand:
    """Команда языка ESYBOT"""
    type: CommandType
    name: str
    args: List[str]
    kwargs: Dict[str, Any] = field(default_factory=dict)
    line_number: int = 0
    raw_line: str = ""
    block_content: List['ESYBOTCommand'] = field(default_factory=list)
    python_code: str = ""

class ESYBOTStates(StatesGroup):
    """Динамически создаваемые состояния"""
    pass

class ESYBOTInterpreter:
    """Расширенный интерпретатор языка ESYBOT для создания Telegram ботов"""
    
    def __init__(self):
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        self.token: str = ""
        self.commands: List[ESYBOTCommand] = []
        self.variables: Dict[str, Any] = {}
        self.python_globals: Dict[str, Any] = {}
        self.handlers: Dict[str, Callable] = {}
        self.keyboards: Dict[str, Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = {}
        self.states: Dict[str, State] = {}
        self.middlewares: List[Callable] = []
        self.routers: Dict[str, Router] = {}
        self.databases: Dict[str, Any] = {}
        self.current_state_group: Optional[StatesGroup] = None
        
        # Настройка Python окружения для блоков кода
        self._setup_python_environment()
        
    def _setup_python_environment(self):
        """Настройка окружения для выполнения Python кода"""
        self.python_globals = {
            '__builtins__': __builtins__,
            'print': print,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'range': range,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'sum': sum,
            'max': max,
            'min': min,
            'abs': abs,
            'round': round,
            'json': json,
            'os': os,
            're': re,
            'asyncio': asyncio,
            # Добавляем переменные ESYBOT
            'esybot_vars': self.variables,
            'esybot_set': self._python_set_variable,
            'esybot_get': self._python_get_variable,
        }
    
    def _python_set_variable(self, name: str, value: Any):
        """Установка переменной ESYBOT из Python кода"""
        self.variables[name] = value
    
    def _python_get_variable(self, name: str, default: Any = None) -> Any:
        """Получение переменной ESYBOT в Python коде"""
        return self.variables.get(name, default)
        
    def parse_file(self, filename: str) -> bool:
        """Парсинг файла ESYBOT"""
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()
        except FileNotFoundError:
            print(f"❌ Ошибка: Файл '{filename}' не найден")
            return False
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return False
        
        self.commands = self._parse_content(content)
        return True
    
    def _parse_content(self, content: str) -> List[ESYBOTCommand]:
        """Парсинг содержимого файла"""
        lines = content.split('\n')
        commands = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Пропускаем пустые строки и комментарии
            if not line or line.startswith('#') or line.startswith('//'):
                i += 1
                continue
            
            # Специальная обработка Python блоков
            if line.startswith('python {') or line == 'python {':
                command, next_i = self._parse_python_block(lines, i)
                if command:
                    commands.append(command)
                i = next_i
                continue
            
            # Парсим обычную команду и возможный блок
            command, next_i = self._parse_command_block(lines, i)
            if command:
                commands.append(command)
            i = next_i
        
        return commands
    
    def _parse_python_block(self, lines: List[str], start_index: int) -> tuple[Optional[ESYBOTCommand], int]:
        """Парсинг блока Python кода"""
        python_code = ""
        next_index = start_index + 1
        brace_count = 1
        
        # Проверяем, есть ли открывающая скобка в той же строке
        first_line = lines[start_index].strip()
        if not first_line.endswith('{'):
            # Ищем открывающую скобку
            while next_index < len(lines) and lines[next_index].strip() != '{':
                next_index += 1
            if next_index < len(lines):
                next_index += 1
        
        # Собираем код до закрывающей скобки
        while next_index < len(lines) and brace_count > 0:
            line = lines[next_index]
            
            # Подсчитываем скобки только в строках без отступов (не внутри Python кода)
            stripped_line = line.strip()
            if not line.startswith('    ') and not line.startswith('\t'):
                if stripped_line == '{':
                    brace_count += 1
                elif stripped_line == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        break
            
            if brace_count > 0:
                python_code += line + '\n'
            
            next_index += 1
        
        command = ESYBOTCommand(
            type=CommandType.PYTHON_CODE,
            name='python',
            args=[],
            line_number=start_index + 1,
            raw_line=lines[start_index],
            python_code=python_code.strip()
        )
        
        return command, next_index + 1
    
    def _parse_command_block(self, lines: List[str], start_index: int) -> tuple[Optional[ESYBOTCommand], int]:
        """Парсинг команды с возможным блоком кода"""
        line = lines[start_index].strip()
        
        # Определяем тип команды и её параметры
        command = self._parse_single_line(line, start_index + 1)
        if not command:
            return None, start_index + 1
        
        # Проверяем, есть ли блок кода после команды
        next_index = start_index + 1
        if next_index < len(lines) and lines[next_index].strip() == '{':
            # Находим конец блока
            block_content = []
            next_index += 1
            brace_count = 1
            
            while next_index < len(lines) and brace_count > 0:
                block_line_raw = lines[next_index]
                block_line = block_line_raw.strip()
                
                if block_line == '{':
                    brace_count += 1
                elif block_line == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        break
                
                if brace_count > 0:
                    if block_line and not block_line.startswith('#'):
                        # Проверяем на Python блок
                        if block_line.startswith('python {') or block_line == 'python {':
                            py_cmd, py_next = self._parse_python_block(lines, next_index)
                            if py_cmd:
                                block_content.append(py_cmd)
                            next_index = py_next - 1  # -1 потому что будет +1 в конце цикла
                        else:
                            block_cmd = self._parse_single_line(block_line, next_index + 1)
                            if block_cmd:
                                block_content.append(block_cmd)
                
                next_index += 1
            
            command.block_content = block_content
            next_index += 1
        
        return command, next_index
    
    def _parse_single_line(self, line: str, line_number: int) -> Optional[ESYBOTCommand]:
        """Парсинг одной строки команды"""
        # Удаляем комментарии
        if '#' in line:
            line = line.split('#')[0].strip()
        if '//' in line:
            line = line.split('//')[0].strip()
        
        if not line:
            return None
        
        # Парсим команду и аргументы
        parts = self._split_command_line(line)
        if not parts:
            return None
        
        cmd_name = parts[0].lower()
        args = parts[1:]
        
        # Определяем тип команды
        command_type = self._get_command_type(cmd_name)
        
        # Парсим kwargs из аргументов
        kwargs = {}
        clean_args = []
        
        for arg in args:
            if '=' in arg:
                key, value = arg.split('=', 1)
                kwargs[key.strip()] = self._parse_value(value.strip())
            else:
                clean_args.append(self._parse_value(arg))
        
        return ESYBOTCommand(
            type=command_type,
            name=cmd_name,
            args=clean_args,
            kwargs=kwargs,
            line_number=line_number,
            raw_line=line
        )
    
    def _split_command_line(self, line: str) -> List[str]:
        """Разбивка строки команды на части с учётом кавычек"""
        parts = []
        current_part = ""
        in_quotes = False
        quote_char = None
        
        i = 0
        while i < len(line):
            char = line[i]
            
            if not in_quotes and char in ['"', "'"]:
                in_quotes = True
                quote_char = char
            elif in_quotes and char == quote_char:
                in_quotes = False
                quote_char = None
            elif not in_quotes and char.isspace():
                if current_part:
                    parts.append(current_part)
                    current_part = ""
                i += 1
                continue
            
            current_part += char
            i += 1
        
        if current_part:
            parts.append(current_part)
        
        return parts
    
    def _get_command_type(self, cmd_name: str) -> CommandType:
        """Определение типа команды"""
        type_mapping = {
            # Конфигурация бота
            'bot_token': CommandType.BOT_CONFIG,
            'bot_name': CommandType.BOT_CONFIG,
            'bot_description': CommandType.BOT_CONFIG,
            'bot_commands': CommandType.BOT_CONFIG,
            
            # Обработчики событий
            'on_start': CommandType.HANDLER,
            'on_message': CommandType.HANDLER,
            'on_command': CommandType.HANDLER,
            'on_callback': CommandType.HANDLER,
            'on_inline': CommandType.HANDLER,
            'on_photo': CommandType.HANDLER,
            'on_video': CommandType.HANDLER,
            'on_audio': CommandType.HANDLER,
            'on_document': CommandType.HANDLER,
            'on_sticker': CommandType.HANDLER,
            'on_voice': CommandType.HANDLER,
            'on_contact': CommandType.HANDLER,
            'on_location': CommandType.HANDLER,
            'on_poll': CommandType.HANDLER,
            'on_dice': CommandType.HANDLER,
            'on_payment': CommandType.HANDLER,
            'on_member_join': CommandType.HANDLER,
            'on_member_leave': CommandType.HANDLER,
            
            # Ответы и действия
            'send': CommandType.RESPONSE,
            'reply': CommandType.RESPONSE,
            'edit': CommandType.RESPONSE,
            'delete': CommandType.RESPONSE,
            'forward': CommandType.RESPONSE,
            'copy': CommandType.RESPONSE,
            'send_photo': CommandType.RESPONSE,
            'send_video': CommandType.RESPONSE,
            'send_audio': CommandType.RESPONSE,
            'send_document': CommandType.RESPONSE,
            'send_sticker': CommandType.RESPONSE,
            'send_voice': CommandType.RESPONSE,
            'send_media_group': CommandType.RESPONSE,
            'send_location': CommandType.RESPONSE,
            'send_contact': CommandType.RESPONSE,
            'send_poll': CommandType.RESPONSE,
            'send_dice': CommandType.RESPONSE,
            'answer_callback': CommandType.RESPONSE,
            'answer_inline': CommandType.RESPONSE,
            
            # Кнопки и меню
            'button': CommandType.BUTTON,
            'menu': CommandType.MENU,
            'keyboard': CommandType.MENU,
            'remove_keyboard': CommandType.MENU,
            
            # Состояния
            'set_state': CommandType.STATE,
            'get_state': CommandType.STATE,
            'clear_state': CommandType.STATE,
            'state_group': CommandType.STATE,
            
            # Переменные
            'set': CommandType.VARIABLE,
            'get': CommandType.VARIABLE,
            'increment': CommandType.VARIABLE,
            'decrement': CommandType.VARIABLE,
            
            # Условия и циклы
            'if': CommandType.CONDITION,
            'else': CommandType.CONDITION,
            'elif': CommandType.CONDITION,
            'for': CommandType.LOOP,
            'while': CommandType.LOOP,
            'break': CommandType.LOOP,
            'continue': CommandType.LOOP,
            
            # API и внешние вызовы
            'api_call': CommandType.API_CALL,
            'http_get': CommandType.API_CALL,
            'http_post': CommandType.API_CALL,
            
            # Python код
            'python': CommandType.PYTHON_CODE,
            'exec': CommandType.PYTHON_CODE,
            'eval': CommandType.PYTHON_CODE,
            
            # Middleware и роутеры
            'middleware': CommandType.MIDDLEWARE,
            'router': CommandType.MIDDLEWARE,
            
            # База данных
            'db_connect': CommandType.DATABASE,
            'db_query': CommandType.DATABASE,
            'db_insert': CommandType.DATABASE,
            'db_update': CommandType.DATABASE,
            'db_delete': CommandType.DATABASE,
            
            # Webhook и платежи
            'webhook': CommandType.WEBHOOK,
            'payment': CommandType.PAYMENT,
            'invoice': CommandType.PAYMENT,
            
            # Inline режим
            'inline_result': CommandType.INLINE,
        }
        return type_mapping.get(cmd_name, CommandType.RESPONSE)
    
    def _parse_value(self, value: str) -> Any:
        """Парсинг значения с автоматическим определением типа"""
        value = value.strip()
        
        # Строки в кавычках
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        
        # Числа
        if value.isdigit():
            return int(value)
        if re.match(r'^\d+\.\d+$', value):
            return float(value)
        
        # Булевы значения
        if value.lower() in ['true', 'да', 'yes']:
            return True
        if value.lower() in ['false', 'нет', 'no']:
            return False
        
        # Null/None
        if value.lower() in ['null', 'none', 'nil']:
            return None
        
        # Массивы [1,2,3]
        if value.startswith('[') and value.endswith(']'):
            try:
                return json.loads(value)
            except:
                pass
        
        # Объекты {"key": "value"}
        if value.startswith('{') and value.endswith('}'):
            try:
                return json.loads(value)
            except:
                pass
        
        # Переменные (начинаются с $)
        if value.startswith('$'):
            return value
        
        return value
    
    async def run(self) -> None:
        """Запуск интерпретатора и бота"""
        print("🚀 Запуск расширенного ESYBOT интерпретатора...")
        
        # Инициализация бота
        if not await self._initialize_bot():
            return
        
        # Обработка команд
        await self._process_commands()
        
        # Запуск бота
        print("✅ Бот запущен! Нажмите Ctrl+C для остановки.")
        try:
            await self.dp.start_polling(self.bot)
        except KeyboardInterrupt:
            print("\n⏹️ Бот остановлен пользователем")
        finally:
            await self.bot.session.close()
    
    async def _initialize_bot(self) -> bool:
        """Инициализация бота"""
        # Ищем токен в командах
        for cmd in self.commands:
            if cmd.type == CommandType.BOT_CONFIG and cmd.name == 'bot_token':
                if cmd.args:
                    self.token = str(cmd.args[0])
                    break
        
        if not self.token:
            print("❌ Ошибка: Не указан токен бота. Используйте команду: bot_token \"YOUR_TOKEN\"")
            return False
        
        try:
            self.bot = Bot(token=self.token)
            self.dp = Dispatcher(storage=MemoryStorage())
            
            # Устанавливаем команды бота
            await self._setup_bot_commands()
            
            print("✅ Бот инициализирован")
            return True
        except Exception as e:
            print(f"❌ Ошибка инициализации бота: {e}")
            return False
    
    async def _setup_bot_commands(self):
        """Настройка команд бота"""
        bot_commands = []
        for cmd in self.commands:
            if cmd.type == CommandType.BOT_CONFIG and cmd.name == 'bot_commands':
                for block_cmd in cmd.block_content:
                    if len(block_cmd.args) >= 2:
                        command = BotCommand(
                            command=block_cmd.args[0],
                            description=block_cmd.args[1]
                        )
                        bot_commands.append(command)
        
        if bot_commands:
            await self.bot.set_my_commands(bot_commands)
    
    async def _process_commands(self) -> None:
        """Обработка команд ESYBOT"""
        for cmd in self.commands:
            await self._execute_command(cmd)
    
    async def _execute_command(self, cmd: ESYBOTCommand) -> None:
        """Выполнение отдельной команды"""
        try:
            if cmd.type == CommandType.HANDLER:
                await self._handle_handler_command(cmd)
            elif cmd.type == CommandType.BUTTON:
                await self._handle_button_command(cmd)
            elif cmd.type == CommandType.MENU:
                await self._handle_menu_command(cmd)
            elif cmd.type == CommandType.VARIABLE:
                await self._handle_variable_command(cmd)
            elif cmd.type == CommandType.PYTHON_CODE:
                await self._handle_python_command(cmd)
        except Exception as e:
            print(f"❌ Ошибка выполнения команды '{cmd.name}' на строке {cmd.line_number}: {e}")
            traceback.print_exc()
    
    async def _handle_python_command(self, cmd: ESYBOTCommand, context: Dict[str, Any] = None) -> Any:
        """Выполнение Python кода"""
        try:
            # Подготавливаем локальные переменные
            local_vars = self.python_globals.copy()
            if context:
                local_vars.update(context)
                local_vars['update'] = context.get('update')
                local_vars['message'] = context.get('update')
                local_vars['bot'] = self.bot
                local_vars['user_id'] = context.get('user_id')
                local_vars['chat_id'] = context.get('chat_id')
                local_vars['text'] = context.get('text', '')
            
            # Синхронизируем переменные ESYBOT с Python
            local_vars['esybot_vars'] = self.variables
            
            # Выполняем код
            if cmd.python_code.strip():
                # Определяем, это выражение или блок кода
                lines = cmd.python_code.strip().split('\n')
                if len(lines) == 1 and not any(keyword in lines[0] for keyword in ['def ', 'class ', 'if ', 'for ', 'while ', 'try:', 'with ']):
                    # Простое выражение - используем eval
                    result = eval(cmd.python_code.strip(), local_vars)
                    return result
                else:
                    # Блок кода - используем exec
                    exec(cmd.python_code, local_vars)
                    
                    # Синхронизируем изменения переменных обратно
                    if 'esybot_vars' in local_vars:
                        self.variables.update(local_vars['esybot_vars'])
            
        except Exception as e:
            print(f"❌ Ошибка выполнения Python кода на строке {cmd.line_number}: {e}")
            traceback.print_exc()
            return None
    
    async def _handle_handler_command(self, cmd: ESYBOTCommand) -> None:
        """Обработка команд-хендлеров - ИСПРАВЛЕНО для aiogram 3.21.0"""
        async def handler_func(update: Union[Message, CallbackQuery, InlineQuery], state: FSMContext = None):
            # Определяем тип обновления и контекст
            context = await self._build_context(update, state)
            
            # Выполняем команды в блоке
            for block_cmd in cmd.block_content:
                await self._execute_block_command(block_cmd, context)
        
        # Регистрируем хендлер в зависимости от типа
        if cmd.name == 'on_start':
            self.dp.message.register(handler_func, Command(commands=['start']))
        elif cmd.name == 'on_message':
            if cmd.args:
                # Фильтр по тексту или регулярному выражению
                text_filter = cmd.args[0]
                if text_filter.startswith('/') and text_filter.endswith('/'):
                    # Регулярное выражение
                    pattern = text_filter[1:-1]
                    self.dp.message.register(handler_func, F.text.regexp(pattern))
                else:
                    # Точное совпадение - ИСПРАВЛЕНО: используем F.text вместо Text
                    self.dp.message.register(handler_func, F.text == text_filter)
            else:
                # Все текстовые сообщения - ИСПРАВЛЕНО: используем F.text
                self.dp.message.register(handler_func, F.text)
        elif cmd.name == 'on_command':
            if cmd.args:
                commands = [cmd.args[0]] if isinstance(cmd.args[0], str) else cmd.args
                self.dp.message.register(handler_func, Command(commands=commands))
        elif cmd.name == 'on_callback':
            if cmd.args:
                callback_data = cmd.args[0]
                if callback_data.startswith('/') and callback_data.endswith('/'):
                    # Регулярное выражение
                    pattern = callback_data[1:-1]
                    self.dp.callback_query.register(handler_func, F.data.regexp(pattern))
                else:
                    self.dp.callback_query.register(handler_func, F.data == callback_data)
            else:
                self.dp.callback_query.register(handler_func)
        elif cmd.name == 'on_photo':
            self.dp.message.register(handler_func, F.photo)
        elif cmd.name == 'on_video':
            self.dp.message.register(handler_func, F.video)
        elif cmd.name == 'on_audio':
            self.dp.message.register(handler_func, F.audio)
        elif cmd.name == 'on_document':
            self.dp.message.register(handler_func, F.document)
        elif cmd.name == 'on_sticker':
            self.dp.message.register(handler_func, F.sticker)
        elif cmd.name == 'on_voice':
            self.dp.message.register(handler_func, F.voice)
        elif cmd.name == 'on_contact':
            self.dp.message.register(handler_func, F.contact)
        elif cmd.name == 'on_location':
            self.dp.message.register(handler_func, F.location)
        elif cmd.name == 'on_inline':
            self.dp.inline_query.register(handler_func)
    
    async def _build_context(self, update: Union[Message, CallbackQuery, InlineQuery], state: FSMContext = None) -> Dict[str, Any]:
        """Построение контекста для выполнения команд"""
        context = {
            'update': update,
            'state': state,
            'bot': self.bot,
        }
        
        if isinstance(update, Message):
            context.update({
                'message': update,
                'user_id': update.from_user.id,
                'chat_id': update.chat.id,
                'text': update.text or '',
                'photo': update.photo or [],  # Список PhotoSize объектов
                'video': update.video,
                'audio': update.audio,
                'document': update.document,
                'sticker': update.sticker,
                'voice': update.voice,
                'contact': update.contact,
                'location': update.location,
            })
        elif isinstance(update, CallbackQuery):
            context.update({
                'callback_query': update,
                'user_id': update.from_user.id,
                'chat_id': update.message.chat.id if update.message else None,
                'message_id': update.message.message_id if update.message else None,
                'data': update.data,
                'text': update.data or '',
            })
        elif isinstance(update, InlineQuery):
            context.update({
                'inline_query': update,
                'user_id': update.from_user.id,
                'query': update.query,
                'text': update.query,
            })
        
        return context
    
    async def _execute_block_command(self, cmd: ESYBOTCommand, context: Dict[str, Any]) -> None:
        """Выполнение команды внутри блока хендлера"""
        if cmd.type == CommandType.RESPONSE:
            await self._handle_response_command(cmd, context)
        elif cmd.type == CommandType.VARIABLE:
            await self._handle_variable_command(cmd, context)
        elif cmd.type == CommandType.CONDITION:
            await self._handle_condition_command(cmd, context)
        elif cmd.type == CommandType.STATE:
            await self._handle_state_command(cmd, context)
        elif cmd.type == CommandType.PYTHON_CODE:
            await self._handle_python_command(cmd, context)
        elif cmd.type == CommandType.API_CALL:
            await self._handle_api_command(cmd, context)
    
    async def _handle_response_command(self, cmd: ESYBOTCommand, context: Dict[str, Any]) -> None:
        """Обработка команд ответа"""
        try:
            if cmd.name == 'send':
                await self._handle_send_command(cmd, context)
            elif cmd.name == 'reply':
                await self._handle_reply_command(cmd, context)
            elif cmd.name == 'edit':
                await self._handle_edit_command(cmd, context)
            elif cmd.name == 'delete':
                await self._handle_delete_command(cmd, context)
            elif cmd.name.startswith('send_'):
                await self._handle_media_command(cmd, context)
            elif cmd.name == 'answer_callback':
                await self._handle_answer_callback_command(cmd, context)
            elif cmd.name == 'answer_inline':
                await self._handle_answer_inline_command(cmd, context)
        except Exception as e:
            print(f"❌ Ошибка ответа: {e}")
    
    async def _handle_send_command(self, cmd: ESYBOTCommand, context: Dict[str, Any]) -> None:
        """Обработка команды send"""
        text = self._resolve_variables(cmd.args[0] if cmd.args else "Сообщение", context)
        chat_id = context.get('chat_id')
        
        # Получаем параметры
        keyboard = self._get_keyboard_from_kwargs(cmd.kwargs)
        parse_mode = cmd.kwargs.get('parse_mode', None)
        disable_notification = cmd.kwargs.get('silent', False)
        
        await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode,
            disable_notification=disable_notification
        )
    
    async def _handle_reply_command(self, cmd: ESYBOTCommand, context: Dict[str, Any]) -> None:
        """Обработка команды reply"""
        text = self._resolve_variables(cmd.args[0] if cmd.args else "Ответ", context)
        message = context.get('message')
        
        if message:
            keyboard = self._get_keyboard_from_kwargs(cmd.kwargs)
            parse_mode = cmd.kwargs.get('parse_mode', None)
            
            await message.reply(
                text=text,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
    
    async def _handle_edit_command(self, cmd: ESYBOTCommand, context: Dict[str, Any]) -> None:
        """Обработка команды edit"""
        text = self._resolve_variables(cmd.args[0] if cmd.args else "Изменённое сообщение", context)
        
        if 'callback_query' in context:
            callback_query = context['callback_query']
            keyboard = self._get_keyboard_from_kwargs(cmd.kwargs)
            parse_mode = cmd.kwargs.get('parse_mode', None)
            
            await callback_query.message.edit_text(
                text=text,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
        elif 'message' in context:
            # Редактирование собственного сообщения
            message = context['message']
            keyboard = self._get_keyboard_from_kwargs(cmd.kwargs)
            
            await self.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=text,
                reply_markup=keyboard
            )
    
    async def _handle_delete_command(self, cmd: ESYBOTCommand, context: Dict[str, Any]) -> None:
        """Обработка команды delete"""
        if 'callback_query' in context:
            callback_query = context['callback_query']
            await callback_query.message.delete()
        elif 'message' in context:
            message = context['message']
            await message.delete()
    
    async def _handle_media_command(self, cmd: ESYBOTCommand, context: Dict[str, Any]) -> None:
        """Обработка команд отправки медиа"""
        chat_id = context.get('chat_id')
        if not chat_id:
            return
        
        file_path = self._resolve_variables(cmd.args[0] if cmd.args else "", context)
        caption = self._resolve_variables(cmd.kwargs.get('caption', ''), context) if cmd.kwargs.get('caption') else None
        keyboard = self._get_keyboard_from_kwargs(cmd.kwargs)
        
        try:
            if cmd.name == 'send_photo':
                if file_path.startswith('http'):
                    await self.bot.send_photo(chat_id, file_path, caption=caption, reply_markup=keyboard)
                else:
                    await self.bot.send_photo(chat_id, FSInputFile(file_path), caption=caption, reply_markup=keyboard)
            elif cmd.name == 'send_video':
                if file_path.startswith('http'):
                    await self.bot.send_video(chat_id, file_path, caption=caption, reply_markup=keyboard)
                else:
                    await self.bot.send_video(chat_id, FSInputFile(file_path), caption=caption, reply_markup=keyboard)
            elif cmd.name == 'send_audio':
                if file_path.startswith('http'):
                    await self.bot.send_audio(chat_id, file_path, caption=caption, reply_markup=keyboard)
                else:
                    await self.bot.send_audio(chat_id, FSInputFile(file_path), caption=caption, reply_markup=keyboard)
            elif cmd.name == 'send_document':
                if file_path.startswith('http'):
                    await self.bot.send_document(chat_id, file_path, caption=caption, reply_markup=keyboard)
                else:
                    await self.bot.send_document(chat_id, FSInputFile(file_path), caption=caption, reply_markup=keyboard)
        except Exception as e:
            print(f"❌ Ошибка отправки медиа: {e}")
    
    def _get_keyboard_from_kwargs(self, kwargs: Dict[str, Any]) -> Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]]:
        """Получение клавиатуры из параметров команды"""
        keyboard_name = kwargs.get('keyboard')
        if keyboard_name and keyboard_name in self.keyboards:
            return self.keyboards[keyboard_name]
        return None
    
    async def _handle_button_command(self, cmd: ESYBOTCommand) -> None:
        """Обработка команд кнопок"""
        # Кнопки создаются в контексте меню
        pass
    
    async def _handle_menu_command(self, cmd: ESYBOTCommand) -> None:
        """Обработка команд меню/клавиатуры"""
        menu_name = cmd.args[0] if cmd.args else "default_menu"
        
        if cmd.name == 'keyboard':
            # Обычная клавиатура
            builder = ReplyKeyboardBuilder()
            
            current_row = []
            for block_cmd in cmd.block_content:
                if block_cmd.type == CommandType.BUTTON and len(block_cmd.args) >= 1:
                    button = KeyboardButton(text=block_cmd.args[0])
                    current_row.append(button)
                    
                    # Проверяем, нужно ли начать новую строку
                    if 'new_row' in block_cmd.kwargs or len(current_row) >= 3:
                        builder.row(*current_row)
                        current_row = []
            
            # Добавляем оставшиеся кнопки
            if current_row:
                builder.row(*current_row)
            
            keyboard = builder.as_markup(resize_keyboard=True)
            self.keyboards[menu_name] = keyboard
        
        elif cmd.name == 'menu':
            # Inline клавиатура
            builder = InlineKeyboardBuilder()
            
            current_row = []
            for block_cmd in cmd.block_content:
                if block_cmd.type == CommandType.BUTTON and len(block_cmd.args) >= 2:
                    button_text = block_cmd.args[0]
                    
                    # Определяем тип кнопки
                    if 'url' in block_cmd.kwargs:
                        button = InlineKeyboardButton(text=button_text, url=block_cmd.kwargs['url'])
                    elif 'web_app' in block_cmd.kwargs:
                        button = InlineKeyboardButton(text=button_text, web_app=WebAppInfo(url=block_cmd.kwargs['web_app']))
                    else:
                        callback_data = block_cmd.args[1]
                        button = InlineKeyboardButton(text=button_text, callback_data=callback_data)
                    
                    current_row.append(button)
                    
                    # Проверяем, нужно ли начать новую строку
                    if 'new_row' in block_cmd.kwargs or len(current_row) >= 3:
                        builder.row(*current_row)
                        current_row = []
            
            # Добавляем оставшиеся кнопки
            if current_row:
                builder.row(*current_row)
            
            keyboard = builder.as_markup()
            self.keyboards[menu_name] = keyboard
        
        elif cmd.name == 'remove_keyboard':
            self.keyboards[menu_name] = ReplyKeyboardRemove()
    
    async def _handle_variable_command(self, cmd: ESYBOTCommand, context: Dict[str, Any] = None) -> None:
        """Обработка команд переменных"""
        if cmd.name == 'set' and len(cmd.args) >= 2:
            var_name = cmd.args[0]
            var_value = self._resolve_variables(cmd.args[1], context or {})
            self.variables[var_name] = var_value
        elif cmd.name == 'get' and cmd.args:
            var_name = cmd.args[0]
            return self.variables.get(var_name)
        elif cmd.name == 'increment' and cmd.args:
            var_name = cmd.args[0]
            current_value = self.variables.get(var_name, 0)
            self.variables[var_name] = current_value + 1
        elif cmd.name == 'decrement' and cmd.args:
            var_name = cmd.args[0]
            current_value = self.variables.get(var_name, 0)
            self.variables[var_name] = current_value - 1
    
    async def _handle_condition_command(self, cmd: ESYBOTCommand, context: Dict[str, Any]) -> None:
        """Обработка условных команд"""
        if cmd.name == 'if' and len(cmd.args) >= 3:
            left = self._resolve_variables(cmd.args[0], context)
            operator = cmd.args[1]
            right = self._resolve_variables(cmd.args[2], context)
            
            condition_result = self._evaluate_condition(left, operator, right)
            
            if condition_result:
                for block_cmd in cmd.block_content:
                    await self._execute_block_command(block_cmd, context)
    
    async def _handle_state_command(self, cmd: ESYBOTCommand, context: Dict[str, Any]) -> None:
        """Обработка команд состояний"""
        state = context.get('state')
        if not state:
            return
        
        if cmd.name == 'set_state' and cmd.args:
            state_name = cmd.args[0]
            # Устанавливаем состояние
            await state.set_state(state_name)
        elif cmd.name == 'clear_state':
            await state.clear()
        elif cmd.name == 'get_state':
            current_state = await state.get_state()
            return current_state
    
    async def _handle_api_command(self, cmd: ESYBOTCommand, context: Dict[str, Any]) -> None:
        """Обработка API команд"""
        # Здесь можно добавить HTTP запросы и другие API вызовы
        pass
    
    async def _handle_answer_callback_command(self, cmd: ESYBOTCommand, context: Dict[str, Any]) -> None:
        """Обработка ответа на callback query"""
        callback_query = context.get('callback_query')
        if callback_query:
            text = self._resolve_variables(cmd.args[0] if cmd.args else "", context)
            show_alert = cmd.kwargs.get('alert', False)
            
            await callback_query.answer(text=text, show_alert=show_alert)
    
    async def _handle_answer_inline_command(self, cmd: ESYBOTCommand, context: Dict[str, Any]) -> None:
        """Обработка ответа на inline query"""
        inline_query = context.get('inline_query')
        if inline_query:
            results = []
            
            # Создаём результаты из блока команд
            for i, block_cmd in enumerate(cmd.block_content):
                if block_cmd.name == 'inline_result' and len(block_cmd.args) >= 2:
                    title = self._resolve_variables(block_cmd.args[0], context)
                    description = self._resolve_variables(block_cmd.args[1], context)
                    content = self._resolve_variables(block_cmd.args[2] if len(block_cmd.args) > 2 else title, context)
                    
                    result = InlineQueryResultArticle(
                        id=str(i),
                        title=title,
                        description=description,
                        input_message_content=InputTextMessageContent(message_text=content)
                    )
                    results.append(result)
            
            await inline_query.answer(results, cache_time=cmd.kwargs.get('cache_time', 300))
    
    def _resolve_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Разрешение переменных в тексте"""
        if not isinstance(text, str):
            return str(text)
        
        # Замена переменных ESYBOT ($variable)
        for var_name, var_value in self.variables.items():
            text = text.replace(f'${var_name}', str(var_value))
        
        # Замена контекстных переменных
        text = text.replace('$user_id', str(context.get('user_id', '')))
        text = text.replace('$chat_id', str(context.get('chat_id', '')))
        text = text.replace('$text', str(context.get('text', '')))
        text = text.replace('$query', str(context.get('query', '')))
        text = text.replace('$data', str(context.get('data', '')))
        
        # Информация о пользователе
        update = context.get('update')
        if update and hasattr(update, 'from_user') and update.from_user:
            user = update.from_user
            text = text.replace('$first_name', str(user.first_name or ''))
            text = text.replace('$last_name', str(user.last_name or ''))
            text = text.replace('$username', f"@{user.username}" if user.username else '')
        
        # Информация о фотографиях
        photo_list = context.get('photo', [])
        if photo_list:
            text = text.replace('$photo', f"{len(photo_list)} размеров")
        
        return text
    
    def _evaluate_condition(self, left: Any, operator: str, right: Any) -> bool:
        """Вычисление логического условия"""
        try:
            if operator == '==':
                return left == right
            elif operator == '!=':
                return left != right  
            elif operator == '>':
                return float(left) > float(right)
            elif operator == '<':
                return float(left) < float(right)
            elif operator == '>=':
                return float(left) >= float(right)
            elif operator == '<=':
                return float(left) <= float(right)
            elif operator == 'in':
                return str(left) in str(right)
            elif operator == 'not_in':
                return str(left) not in str(right)
            elif operator == 'contains':
                return str(right) in str(left)
        except (ValueError, TypeError) as e:
            print(f"❌ Ошибка в условии: {e}")
        
        return False

# Создание расширенного примера
def create_advanced_example():
    """Создание расширенного примера файла ESYBOT"""
    example_content = '''# ESYBOT - Расширенный пример бота с Python интеграцией
# Конфигурация бота
bot_token "YOUR_BOT_TOKEN_HERE"
bot_name "AdvancedESYBot"
bot_description "Продвинутый бот на ESYBOT"

# Команды бота
bot_commands {
    start "Запустить бота"
    help "Получить справку"
    stats "Статистика"
    calc "Калькулятор"
    weather "Погода"
}

# Переменные
set welcome_text "🚀 Добро пожаловать в продвинутый ESYBOT!"
set admin_id 123456789
set user_count 0
set bot_version "2.0"

# Python блок для инициализации
python {
    import random
    import datetime
    
    # Устанавливаем начальные значения
    esybot_set('start_time', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    esybot_set('random_fact', f"Случайное число: {random.randint(1, 100)}")
    
    print("🐍 Python инициализация завершена!")
}

# Главное меню
menu main_menu {
    button "📊 Статистика" stats_callback
    button "🧮 Калькулятор" calc_callback new_row=true
    button "🌤️ Погода" weather_callback
    button "🎲 Случайность" random_callback new_row=true
}

# Обычная клавиатура
keyboard reply_keyboard {
    button "🚀 Старт"
    button "❓ Помощь" new_row=true
    button "📞 Контакты"
}

# Обработчик старта
on_start {
    increment user_count
    
    python {
        # Логирование пользователя
        user_id = locals().get('user_id')
        count = esybot_get('user_count')
        print(f"👤 Новый пользователь: {user_id}, всего: {count}")
        
        # Персонализированное приветствие
        greetings = [
            "Привет! Рад тебя видеть! 👋",
            "Добро пожаловать в будущее ботов! 🤖",
            "Готов к невероятным возможностям? ⚡",
        ]
        esybot_set('personal_greeting', random.choice(greetings))
    }
    
    send $personal_greeting keyboard=reply_keyboard
    send "Выберите действие из меню:" keyboard=main_menu
}

# Обработчик команды help
on_command help {
    python {
        help_text = f"""
🤖 **ESYBOT v{esybot_get('bot_version')} - Справка**

📋 **Основные команды:**
• /start - Запуск бота
• /help - Эта справка  
• /stats - Статистика использования

🕐 **Время запуска бота:** {esybot_get('start_time')}
👥 **Пользователей:** {esybot_get('user_count')}

🐍 **Python интеграция включена!**
        """
        esybot_set('help_message', help_text.strip())
    }
    
    send $help_message parse_mode="Markdown"
}

# Обработчик статистики
on_callback stats_callback {
    python {
        stats_text = f"""
📊 **Статистика бота**

👥 **Пользователи:** {esybot_get('user_count')}
🕐 **Запущен:** {esybot_get('start_time')}
🐍 **Python:** Активен

{esybot_get('random_fact')}
        """
        esybot_set('stats_message', stats_text.strip())
    }
    
    edit $stats_message parse_mode="Markdown"
    answer_callback "Статистика обновлена!" alert=false
}

# Калькулятор
on_callback calc_callback {
    edit "🧮 Калькулятор\\nВведите выражение (например: 2+2*3):"
    set_state waiting_calc
}

# Обработка выражений калькулятора
on_message ".*[0-9+\\-*/()\\s]+.*" {
    if $state == "waiting_calc" {
        python {
            expression = locals().get('text', '').strip()
            try:
                # Безопасное вычисление
                allowed_chars = set('0123456789+-*/().,. ')
                if all(c in allowed_chars for c in expression):
                    result = eval(expression)
                    calc_result = f"🧮 **Результат:**\\n`{expression}` = **{result}**"
                else:
                    calc_result = "❌ Недопустимые символы в выражении!"
            except Exception as e:
                calc_result = f"❌ Ошибка вычисления: {str(e)}"
            
            esybot_set('calc_result', calc_result)
        }
        
        reply $calc_result parse_mode="Markdown"
        clear_state
    }
}

# Обработка фото с анализом
on_photo {
    python {
        # Имитация анализа фото
        import random
        
        photo_analysis = [
            "🖼️ Красивое фото!",
            "📸 Отличное качество изображения!",
            "🎨 Интересная композиция!",
            "🌈 Яркие цвета на фото!",
            "🔍 Много деталей для изучения!"
        ]
        
        analysis = random.choice(photo_analysis)
        esybot_set('photo_response', analysis)
    }
    
    reply $photo_response
    reply "Размер фото: $photo файлов"
}

# Обработка неизвестных команд
on_message {
    python {
        # Анализ сообщения
        message_text = locals().get('text', '').lower()
        
        responses = {
            'привет': '👋 Привет! Как дела?',
            'пока': '👋 До свидания!',
            'спасибо': '😊 Пожалуйста!',
            'как дела': '🤖 У меня всё отлично! А у вас?',
        }
        
        response = None
        for keyword, reply_text in responses.items():
            if keyword in message_text:
                response = reply_text
                break
        
        if not response:
            response = f"🤔 Не понимаю сообщение: '{locals().get('text', '')}'\\nИспользуйте /help для справки"
        
        esybot_set('auto_response', response)
    }
    
    reply $auto_response
}
'''
    
    with open('advanced_bot.esi', 'w', encoding='utf-8') as f:
        f.write(example_content)
    print("📝 Создан расширенный пример: advanced_bot.esi")

# Основная функция
async def main():
    """Главная функция запуска интерпретатора"""
    if len(sys.argv) < 2:
        print("📖 Использование: python esybot_advanced.py <файл.esi>")
        print("📝 Создать пример: python esybot_advanced.py --example")
        return
    
    if sys.argv[1] == '--example':
        create_advanced_example()
        return
    
    filename = sys.argv[1]
    interpreter = ESYBOTInterpreter()
    
    if interpreter.parse_file(filename):
        await interpreter.run()
    else:
        print("❌ Не удалось загрузить файл")

if __name__ == "__main__":
    asyncio.run(main())

