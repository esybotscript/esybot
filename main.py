#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ESYBOT ФИНАЛЬНЫЙ WIKI-СОВМЕСТИМЫЙ ИНТЕРПРЕТАТОР
✅ Исправлены кнопки ✅ Исправлены Python блоки ✅ 100% Wiki-совместимость
"""

import asyncio
import sys
import os
import re
import random
import datetime
import json
import math
import time
from typing import Dict, List, Any, Optional, Tuple, Union

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

class FinalESYBOTInterpreter:
    """Финальный ESYBOT интерпретатор с полной Wiki-совместимостью"""
    
    def __init__(self, debug_mode: bool = False):
        self.debug = debug_mode
        self.bot_token = ""
        self.variables: Dict[str, Any] = {}
        self.handlers: List[Dict] = []
        self.keyboards: Dict[str, Any] = {}
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        
    def debug_print(self, message: str) -> None:
        if self.debug:
            print(message)
    
    def parse_file(self, filename: str) -> bool:
        """Wiki-совместимый парсинг файла"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"📝 Парсинг файла: {filename}")
            self._parse_content(content)
            print(f"✅ Wiki-совместимый парсинг завершён:")
            print(f"   🎯 Обработчиков: {len(self.handlers)}")
            print(f"   ⌨️ Клавиатур: {len(self.keyboards)}")
            print(f"   📊 Переменных: {len(self.variables)}")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка парсинга: {e}")
            return False
    
    def _parse_content(self, content: str) -> None:
        """Wiki-совместимый парсинг содержимого"""
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if not line or line.startswith('#') or line.startswith('//'):
                i += 1
                continue
            
            try:
                if line.startswith('bot_token'):
                    self._parse_bot_token(line)
                elif line.startswith('set '):
                    self._parse_variable(line)
                elif line.startswith('menu '):
                    menu_data, next_i = self._parse_menu(lines, i)
                    if menu_data:
                        self.keyboards[menu_data['name']] = self._create_inline_keyboard(menu_data)
                        print(f"⌨️ Создано inline меню: {menu_data['name']}")
                    i = next_i
                    continue
                elif line.startswith('keyboard '):
                    keyboard_data, next_i = self._parse_keyboard(lines, i)
                    if keyboard_data:
                        self.keyboards[keyboard_data['name']] = self._create_reply_keyboard(keyboard_data)
                        print(f"⌨️ Создана reply клавиатура: {keyboard_data['name']}")
                    i = next_i
                    continue
                elif line.startswith('on_'):
                    handler_data, next_i = self._parse_handler(lines, i)
                    if handler_data:
                        self.handlers.append(handler_data)
                        print(f"🎯 Создан обработчик: {handler_data['type']} {handler_data['arg']}")
                    i = next_i
                    continue
                
            except Exception as e:
                print(f"⚠️ Ошибка в строке {i+1}: {e}")
            
            i += 1
    
    def _parse_bot_token(self, line: str) -> None:
        """Парсинг токена"""
        match = re.search(r'"([^"]*)"', line)
        if match:
            self.bot_token = match.group(1)
            print(f"🔑 Найден токен бота")
    
    def _parse_variable(self, line: str) -> None:
        """Wiki-совместимый парсинг переменных"""
        try:
            var_part = line[4:].strip()
            space_idx = var_part.find(' ')
            if space_idx == -1:
                return
            
            name = var_part[:space_idx]
            value_str = var_part[space_idx+1:].strip()
            
            if value_str.startswith('"') and value_str.endswith('"'):
                value = value_str[1:-1]
            elif value_str.startswith("'") and value_str.endswith("'"):
                value = value_str[1:-1]
            elif value_str.isdigit():
                value = int(value_str)
            elif value_str.replace('.', '', 1).isdigit():
                value = float(value_str)
            elif value_str.lower() in ['true', 'false']:
                value = value_str.lower() == 'true'
            else:
                value = value_str
            
            self.variables[name] = value
            print(f"📊 Переменная: {name} = {value}")
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга переменной: {e}")
    
    def _parse_menu(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """Wiki-совместимый парсинг inline меню"""
        try:
            menu_line = lines[start].strip()
            
            if menu_line.endswith('{'):
                parts = menu_line[:-1].strip().split()
            else:
                parts = menu_line.split()
            
            if len(parts) < 2:
                return None, start + 1
            
            menu_name = parts[1]
            self.debug_print(f"🔧 Парсинг меню: {menu_name}")
            
            # Находим начало блока
            i = start + 1
            if not menu_line.endswith('{'):
                while i < len(lines) and lines[i].strip() != '{':
                    i += 1
                if i >= len(lines):
                    return None, start + 1
                i += 1
            
            # Парсим кнопки
            buttons = []
            while i < len(lines) and lines[i].strip() != '}':
                line = lines[i].strip()
                if line.startswith('button '):
                    button_info = self._parse_button(line)
                    if button_info:
                        buttons.append(button_info)
                        self.debug_print(f"   🔘 Кнопка: {button_info['text']} -> {button_info.get('data', 'N/A')}")
                i += 1
            
            menu_data = {
                'type': 'inline',
                'name': menu_name,
                'buttons': buttons
            }
            
            return menu_data, i + 1
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга меню: {e}")
            return None, start + 1
    
    def _parse_keyboard(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """Wiki-совместимый парсинг reply клавиатуры"""
        try:
            keyboard_line = lines[start].strip()
            
            if keyboard_line.endswith('{'):
                parts = keyboard_line[:-1].strip().split()
            else:
                parts = keyboard_line.split()
            
            if len(parts) < 2:
                return None, start + 1
            
            keyboard_name = parts[1]
            
            i = start + 1
            if not keyboard_line.endswith('{'):
                while i < len(lines) and lines[i].strip() != '{':
                    i += 1
                if i >= len(lines):
                    return None, start + 1
                i += 1
            
            buttons = []
            while i < len(lines) and lines[i].strip() != '}':
                line = lines[i].strip()
                if line.startswith('button '):
                    button_info = self._parse_button(line)
                    if button_info:
                        buttons.append(button_info)
                i += 1
            
            keyboard_data = {
                'type': 'reply',
                'name': keyboard_name,
                'buttons': buttons
            }
            
            return keyboard_data, i + 1
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга клавиатуры: {e}")
            return None, start + 1
    
    def _parse_handler(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """Wiki-совместимый парсинг обработчика"""
        try:
            handler_line = lines[start].strip()
            
            if handler_line.endswith('{'):
                parts = handler_line[:-1].strip().split()
            else:
                parts = handler_line.split()
            
            if not parts:
                return None, start + 1
            
            handler_type = parts[0]
            handler_arg = parts[1] if len(parts) > 1 else ""
            
            self.debug_print(f"🔧 Парсинг обработчика: {handler_type} {handler_arg}")
            
            i = start + 1
            if not handler_line.endswith('{'):
                while i < len(lines) and lines[i].strip() != '{':
                    i += 1
                if i >= len(lines):
                    return None, start + 1
                i += 1
            
            commands = []
            while i < len(lines) and lines[i].strip() != '}':
                line = lines[i].strip()
                
                if line and not line.startswith('#'):
                    if line == 'python {':
                        python_code, python_end = self._parse_python_block(lines, i)
                        if python_code:
                            commands.append({'type': 'python', 'code': python_code})
                        i = python_end
                        continue
                    else:
                        commands.append({'type': 'command', 'line': line})
                
                i += 1
            
            handler_data = {
                'type': handler_type,
                'arg': handler_arg,
                'commands': commands
            }
            
            return handler_data, i + 1
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга обработчика: {e}")
            return None, start + 1
    
    def _parse_button(self, line: str) -> Optional[Dict[str, Any]]:
        """ИСПРАВЛЕННЫЙ парсинг кнопки"""
        try:
            quotes = re.findall(r'"([^"]*)"', line)
            
            if len(quotes) < 1:
                return None
            
            button_info = {
                'text': quotes[0],
                'new_row': 'new_row=true' in line or 'new_row' in line
            }
            
            if 'url=' in line:
                url_match = re.search(r'url="([^"]*)"', line)
                if url_match:
                    button_info['url'] = url_match.group(1)
            elif len(quotes) >= 2:
                button_info['data'] = quotes[1]
            else:
                # Создаем безопасный callback_data из текста кнопки
                safe_data = quotes[0].lower().replace(' ', '_')
                safe_data = re.sub(r'[🎯🎲🐍🌐📊🆘🏠❓📞📷📄🎤😀]', '', safe_data)
                safe_data = re.sub(r'[^\w_-]', '', safe_data)
                button_info['data'] = safe_data or 'button'
            
            return button_info
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга кнопки: {e}")
            return None
    
    def _parse_python_block(self, lines: List[str], start: int) -> Tuple[str, int]:
        """Wiki-совместимый умный парсинг Python блоков"""
        try:
            code_lines = []
            i = start + 1
            brace_balance = 0
            
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()
                
                line_open_braces = stripped.count('{')
                line_close_braces = stripped.count('}')
                brace_balance += line_open_braces - line_close_braces
                
                if stripped == '}' and brace_balance <= 0:
                    break
                
                code_lines.append(line.rstrip())
                i += 1
            
            while code_lines and not code_lines[0].strip():
                code_lines.pop(0)
            while code_lines and not code_lines[-1].strip():
                code_lines.pop()
            
            return '\n'.join(code_lines), i + 1
            
        except Exception as e:
            print(f"⚠️ Ошибка парсинга Python блока: {e}")
            return "", start + 1

    def _create_inline_keyboard(self, menu_data: Dict) -> InlineKeyboardMarkup:
        """ИСПРАВЛЕННОЕ создание inline клавиатуры"""
        builder = InlineKeyboardBuilder()
        
        for btn in menu_data['buttons']:
            try:
                if 'url' in btn:
                    builder.button(text=btn['text'], url=btn['url'])
                    self.debug_print(f"   ✅ URL кнопка: {btn['text']} -> {btn['url']}")
                else:
                    callback_data = btn['data']
                    # Ограничиваем длину callback_data до 64 байт
                    if len(callback_data.encode('utf-8')) > 64:
                        callback_data = callback_data[:60] + str(hash(callback_data) % 1000)
                    
                    builder.button(text=btn['text'], callback_data=callback_data)
                    self.debug_print(f"   ✅ Callback кнопка: {btn['text']} -> {callback_data}")
                
                if btn.get('new_row', False):
                    builder.row()
                    
            except Exception as e:
                print(f"⚠️ Ошибка создания кнопки {btn.get('text', 'N/A')}: {e}")
        
        return builder.as_markup()
    
    def _create_reply_keyboard(self, keyboard_data: Dict) -> ReplyKeyboardMarkup:
        """Wiki-совместимое создание reply клавиатуры"""
        builder = ReplyKeyboardBuilder()
        
        for btn in keyboard_data['buttons']:
            builder.button(text=btn['text'])
            if btn.get('new_row', False):
                builder.row()
        
        return builder.as_markup(resize_keyboard=True)
    
    async def _execute_commands(self, commands: List[Dict], context: Dict[str, Any]) -> None:
        """Wiki-совместимое выполнение команд"""
        for cmd in commands:
            try:
                if cmd['type'] == 'python':
                    await self._execute_python_code(cmd['code'], context)
                elif cmd['type'] == 'command':
                    await self._execute_esybot_command(cmd['line'], context)
            except Exception as e:
                print(f"❌ Ошибка выполнения команды: {e}")
    
    async def _execute_python_code(self, code: str, context: Dict[str, Any]) -> None:
        """ИСПРАВЛЕННОЕ выполнение Python кода с ESYBOT функциями"""
        try:
            # Нормализуем отступы Python кода
            normalized_code = self._normalize_python_code(code)
            
            if not normalized_code.strip():
                self.debug_print("   ⚠️ Python блок пустой, пропускаем")
                return
            
            self.debug_print(f"   🐍 Выполняем Python код ({len(normalized_code.split())} строк)")
            
            # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Добавляем ESYBOT функции
            def esybot_set(var_name: str, value: Any) -> None:
                """Устанавливает переменную ESYBOT"""
                self.variables[var_name] = value
                
            def esybot_get(var_name: str, default: Any = None) -> Any:
                """Получает переменную ESYBOT"""
                return self.variables.get(var_name, default)
                
            def esybot_increment(var_name: str, amount: int = 1) -> None:
                """Увеличивает переменную ESYBOT"""
                if var_name in self.variables:
                    try:
                        self.variables[var_name] += amount
                    except:
                        self.variables[var_name] = amount
                else:
                    self.variables[var_name] = amount
                    
            def esybot_decrement(var_name: str, amount: int = 1) -> None:
                """Уменьшает переменную ESYBOT"""
                if var_name in self.variables:
                    try:
                        self.variables[var_name] -= amount
                    except:
                        self.variables[var_name] = -amount
                else:
                    self.variables[var_name] = -amount
            
            async def esybot_send(text: str, chat_id: int = None, keyboard: str = None, parse_mode: str = None) -> None:
                """Отправляет сообщение из Python блока"""
                target_chat = chat_id or context.get('chat_id')
                reply_markup = None
                
                if keyboard and keyboard in self.keyboards:
                    reply_markup = self.keyboards[keyboard]
                    
                await self.bot.send_message(
                    chat_id=target_chat,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            
            # Подготавливаем полное окружение для Python кода
            local_vars = {
                **context,
                **self.variables,
                # Основные модули
                'bot': self.bot,
                'random': random,
                'datetime': datetime,
                'json': json,
                'os': os,
                're': re,
                'math': math,
                'time': time,
                # ESYBOT функции
                'esybot_set': esybot_set,
                'esybot_get': esybot_get,
                'esybot_increment': esybot_increment,
                'esybot_decrement': esybot_decrement,
                'esybot_send': esybot_send,
                # Синонимы для удобства
                'set_var': esybot_set,
                'get_var': esybot_get,
            }
            
            # Выполняем нормализованный Python код
            exec(normalized_code, {'__builtins__': __builtins__}, local_vars)
            
            # Обновляем переменные ESYBOT (на случай прямого изменения)
            updated_vars = []
            for var_name in list(self.variables.keys()):
                if var_name in local_vars and local_vars[var_name] != self.variables[var_name]:
                    self.variables[var_name] = local_vars[var_name]
                    updated_vars.append(f"{var_name}={local_vars[var_name]}")
            
            # Добавляем новые переменные
            excluded_vars = {
                'bot', 'random', 'datetime', 'json', 'os', 're', 'math', 'time', '__builtins__',
                'esybot_set', 'esybot_get', 'esybot_increment', 'esybot_decrement', 'esybot_send',
                'set_var', 'get_var'
            }
            new_vars = []
            for key, value in local_vars.items():
                if key not in context and key not in excluded_vars and key not in self.variables:
                    self.variables[key] = value
                    new_vars.append(f"{key}={value}")
            
            self.debug_print(f"   ✅ Python блок выполнен успешно")
            if updated_vars:
                self.debug_print(f"      📊 Обновлены переменные: {', '.join(updated_vars)}")
            if new_vars:
                self.debug_print(f"      📊 Новые переменные: {', '.join(new_vars)}")
            
        except NameError as e:
            print(f"❌ Переменная не найдена в Python коде: {e}")
            print(f"   💡 Доступные ESYBOT функции:")
            print(f"      • esybot_set('var_name', value) - установить переменную")
            print(f"      • esybot_get('var_name') - получить переменную")
            print(f"      • esybot_increment('var_name') - увеличить переменную")
            print(f"      • esybot_decrement('var_name') - уменьшить переменную")
            print(f"      • await esybot_send('text', keyboard='name') - отправить сообщение")
            if self.debug:
                print(f"   📝 Проблемный код:")
                for i, line in enumerate(code.split('\n'), 1):
                    print(f"   {i:2d}: {line}")
        except SyntaxError as e:
            print(f"❌ Синтаксическая ошибка в Python коде: {e}")
            print(f"   📍 Строка {e.lineno}: {e.text}")
            if self.debug:
                print(f"   📝 Исходный код:")
                for i, line in enumerate(code.split('\n'), 1):
                    marker = " >>> " if i == e.lineno else "     "
                    print(f"   {i:2d}{marker}{repr(line)}")
        except Exception as e:
            print(f"❌ Ошибка выполнения Python кода: {e}")
            if self.debug:
                print(f"   📝 Проблемный код:")
                for i, line in enumerate(code.split('\n'), 1):
                    print(f"   {i:2d}: {repr(line)}")
                import traceback
                traceback.print_exc()

    def _normalize_python_code(self, code: str) -> str:
        """Нормализация отступов Python кода для exec()"""
        try:
            lines = code.split('\n')
            
            # Убираем пустые строки в начале и конце
            while lines and not lines[0].strip():
                lines.pop(0)
            while lines and not lines[-1].strip():
                lines.pop()
            
            if not lines:
                return ""
            
            # Находим минимальный отступ среди непустых строк
            min_indent = float('inf')
            for line in lines:
                if line.strip():  # Только непустые строки
                    indent = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, indent)
            
            # Если все строки без отступов, возвращаем как есть
            if min_indent == 0 or min_indent == float('inf'):
                normalized = '\n'.join(lines)
                self.debug_print(f"   🔧 Python код уже нормализован")
                return normalized
            
            # Убираем минимальный отступ у всех строк
            normalized_lines = []
            for line in lines:
                if line.strip():  # Непустые строки
                    normalized_lines.append(line[min_indent:])
                else:  # Пустые строки
                    normalized_lines.append("")
            
            result = '\n'.join(normalized_lines)
            
            self.debug_print(f"   🔧 Python код нормализован (убран отступ {min_indent} пробелов)")
            
            return result
            
        except Exception as e:
            print(f"⚠️ Ошибка нормализации Python кода: {e}")
            return code
    
    async def _execute_esybot_command(self, line: str, context: Dict[str, Any]) -> None:
        """Wiki-совместимое выполнение ESYBOT команд"""
        line = line.strip()
        
        if line.startswith('send '):
            await self._execute_send_command(line, context)
        elif line.startswith('reply '):
            await self._execute_reply_command(line, context)
        elif line.startswith('edit '):
            await self._execute_edit_command(line, context)
        elif line.startswith('answer_callback '):
            await self._execute_answer_callback_command(line, context)
        elif line.startswith('increment '):
            self._execute_increment_command(line)
        elif line.startswith('decrement '):
            self._execute_decrement_command(line)
        elif line.startswith('set '):
            await self._execute_set_command(line, context)
    
    async def _execute_send_command(self, line: str, context: Dict[str, Any]) -> None:
        """ИСПРАВЛЕННОЕ выполнение команды send"""
        try:
            match = re.search(r'"([^"]*)"', line)
            if not match:
                return
            
            text = match.group(1)
            text = self._replace_variables(text, context)
            
            reply_markup = None
            parse_mode = None
            
            if 'keyboard=' in line:
                keyboard_match = re.search(r'keyboard=(\w+)', line)
                if keyboard_match:
                    kb_name = keyboard_match.group(1)
                    if kb_name in self.keyboards:
                        reply_markup = self.keyboards[kb_name]
                        self.debug_print(f"   📱 Используется клавиатура: {kb_name}")
            
            if 'parse_mode=' in line:
                parse_mode_match = re.search(r'parse_mode="([^"]*)"', line)
                if parse_mode_match:
                    parse_mode = parse_mode_match.group(1)
            
            await self.bot.send_message(
                chat_id=context['chat_id'],
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
            
            self.debug_print(f"   📤 Отправлено сообщение: {text[:50]}...")
            
        except Exception as e:
            print(f"❌ Ошибка команды send: {e}")
    
    async def _execute_reply_command(self, line: str, context: Dict[str, Any]) -> None:
        """Выполнение команды reply"""
        try:
            match = re.search(r'"([^"]*)"', line)
            if not match:
                return
            
            text = match.group(1)
            text = self._replace_variables(text, context)
            
            update = context.get('update')
            if update and hasattr(update, 'reply'):
                await update.reply(text)
            elif update and hasattr(update, 'message') and update.message:
                await update.message.reply(text)
            
        except Exception as e:
            print(f"❌ Ошибка команды reply: {e}")
    
    async def _execute_edit_command(self, line: str, context: Dict[str, Any]) -> None:
        """ИСПРАВЛЕННОЕ выполнение команды edit"""
        try:
            match = re.search(r'"([^"]*)"', line)
            if not match:
                return
            
            text = match.group(1)
            text = self._replace_variables(text, context)
            
            parse_mode = None
            if 'parse_mode=' in line:
                parse_mode_match = re.search(r'parse_mode="([^"]*)"', line)
                if parse_mode_match:
                    parse_mode = parse_mode_match.group(1)
            
            reply_markup = None
            if 'keyboard=' in line:
                keyboard_match = re.search(r'keyboard=(\w+)', line)
                if keyboard_match:
                    kb_name = keyboard_match.group(1)
                    if kb_name in self.keyboards:
                        reply_markup = self.keyboards[kb_name]
            
            update = context.get('update')
            if update and isinstance(update, CallbackQuery):
                await update.message.edit_text(
                    text=text, 
                    parse_mode=parse_mode,
                    reply_markup=reply_markup
                )
                self.debug_print(f"   ✏️ Сообщение отредактировано: {text[:50]}...")
            
        except Exception as e:
            print(f"❌ Ошибка команды edit: {e}")
    
    async def _execute_answer_callback_command(self, line: str, context: Dict[str, Any]) -> None:
        """ИСПРАВЛЕННОЕ выполнение команды answer_callback"""
        try:
            match = re.search(r'"([^"]*)"', line)
            text = match.group(1) if match else ""
            text = self._replace_variables(text, context)
            
            show_alert = 'alert=true' in line
            
            update = context.get('update')
            if update and isinstance(update, CallbackQuery):
                await update.answer(text=text, show_alert=show_alert)
                self.debug_print(f"   📝 Callback ответ: {text}")
            
        except Exception as e:
            print(f"❌ Ошибка команды answer_callback: {e}")
    
    async def _execute_set_command(self, line: str, context: Dict[str, Any]) -> None:
        """Выполнение команды set"""
        try:
            parts = line.split(' ', 2)
            if len(parts) >= 3:
                var_name = parts[1]
                var_value = parts[2].strip()
                
                if var_value.startswith('"') and var_value.endswith('"'):
                    var_value = var_value[1:-1]
                    var_value = self._replace_variables(var_value, context)
                    self.variables[var_name] = var_value
                else:
                    try:
                        if var_value.isdigit():
                            self.variables[var_name] = int(var_value)
                        elif var_value.replace('.', '', 1).isdigit():
                            self.variables[var_name] = float(var_value)
                        else:
                            self.variables[var_name] = var_value
                    except:
                        self.variables[var_name] = var_value
        except Exception as e:
            print(f"❌ Ошибка команды set: {e}")
    
    def _execute_increment_command(self, line: str) -> None:
        """Выполнение команды increment"""
        parts = line.split()
        if len(parts) > 1:
            var_name = parts[1]
            if var_name in self.variables:
                try:
                    self.variables[var_name] += 1
                except:
                    self.variables[var_name] = 1
    
    def _execute_decrement_command(self, line: str) -> None:
        """Выполнение команды decrement"""
        parts = line.split()
        if len(parts) > 1:
            var_name = parts[1]
            if var_name in self.variables:
                try:
                    self.variables[var_name] -= 1
                except:
                    self.variables[var_name] = -1
    
    def _replace_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Wiki-совместимая замена переменных"""
        # Замена переменных ESYBOT
        for var_name, var_value in self.variables.items():
            text = text.replace(f'${var_name}', str(var_value))
        
        # Замена системных переменных
        text = text.replace('$user_id', str(context.get('user_id', 0)))
        text = text.replace('$chat_id', str(context.get('chat_id', 0)))
        text = text.replace('$first_name', str(context.get('first_name', '')))
        text = text.replace('$username', str(context.get('username', '')))
        text = text.replace('$text', str(context.get('text', '')))
        text = text.replace('$data', str(context.get('data', '')))
        
        return text
    
    async def _create_handler(self, handler_data: Dict) -> None:
        """ИСПРАВЛЕННОЕ создание обработчика"""
        handler_type = handler_data['type']
        handler_arg = handler_data['arg']
        commands = handler_data['commands']
        
        async def handler_func(update: Union[Message, CallbackQuery], state: FSMContext = None):
            try:
                # Правильное определение контекста
                context = {
                    'update': update,
                    'user_id': 0,
                    'first_name': '',
                    'username': '',
                    'text': '',
                    'data': '',
                    'chat_id': 0,
                }
                
                # Определяем тип update и извлекаем данные
                if isinstance(update, CallbackQuery):
                    context.update({
                        'user_id': update.from_user.id,
                        'first_name': update.from_user.first_name or '',
                        'username': f"@{update.from_user.username}" if update.from_user.username else '',
                        'chat_id': update.message.chat.id if update.message else update.from_user.id,
                        'text': update.data or '',
                        'data': update.data or '',
                    })
                    print(f"🔥 CALLBACK: {handler_type} от пользователя {context['user_id']}, data: '{context['data']}'")
                    
                elif isinstance(update, Message):
                    context.update({
                        'user_id': update.from_user.id if update.from_user else 0,
                        'first_name': update.from_user.first_name or '' if update.from_user else '',
                        'username': f"@{update.from_user.username}" if update.from_user and update.from_user.username else '',
                        'chat_id': update.chat.id,
                        'text': update.text or '',
                        'data': '',
                    })
                    print(f"🔥 MESSAGE: {handler_type} от пользователя {context['user_id']}, текст: '{context['text'][:50]}'")
                
                # ВЫПОЛНЯЕМ КОМАНДЫ
                await self._execute_commands(commands, context)
                
            except Exception as e:
                print(f"❌ Ошибка в обработчике {handler_type}: {e}")
                import traceback
                traceback.print_exc()
        
        # Правильная регистрация обработчиков
        if handler_type == 'on_start':
            self.dp.message.register(handler_func, Command(commands=["start"]))
        elif handler_type == 'on_message':
            if handler_arg:
                self.dp.message.register(handler_func, F.text == handler_arg)
            else:
                self.dp.message.register(handler_func, F.text)
        elif handler_type == 'on_command':
            if handler_arg:
                self.dp.message.register(handler_func, Command(commands=[handler_arg]))
        elif handler_type == 'on_callback':
            # КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Правильная регистрация callback обработчиков
            if handler_arg:
                print(f"🔗 Регистрируем callback обработчик для: '{handler_arg}'")
                self.dp.callback_query.register(handler_func, F.data == handler_arg)
            else:
                print(f"🔗 Регистрируем общий callback обработчик")
                self.dp.callback_query.register(handler_func, F.data)
        elif handler_type == 'on_photo':
            self.dp.message.register(handler_func, F.photo)
        elif handler_type == 'on_video':
            self.dp.message.register(handler_func, F.video)
        elif handler_type == 'on_document':
            self.dp.message.register(handler_func, F.document)
        elif handler_type == 'on_voice':
            self.dp.message.register(handler_func, F.voice)
        elif handler_type == 'on_audio':
            self.dp.message.register(handler_func, F.audio)
        elif handler_type == 'on_sticker':
            self.dp.message.register(handler_func, F.sticker)
        elif handler_type == 'on_contact':
            self.dp.message.register(handler_func, F.contact)
        elif handler_type == 'on_location':
            self.dp.message.register(handler_func, F.location)
    
    async def run_interpreter(self) -> None:
        """Запуск финального интерпретатора"""
        if not self.bot_token:
            print("❌ Не указан токен бота!")
            return
        
        # Создаем бота и диспетчер
        self.bot = Bot(self.bot_token)
        self.dp = Dispatcher(storage=MemoryStorage())
        
        # Регистрируем все обработчики
        for handler_data in self.handlers:
            await self._create_handler(handler_data)
        
        print("🎯 Esybot скрипт запущен!")
        print("=" * 60)
        print(f"🔗 Обработчиков сообщений: {len(self.dp.message.handlers)}")
        print(f"🔗 Обработчиков callback: {len(self.dp.callback_query.handlers)}")
        print(f"⌨️ Клавиатур: {len(self.keyboards)}")
        print(f"📊 Переменных: {len(self.variables)}")
        
        # Выводим информацию о callback обработчиках
        if self.dp.callback_query.handlers:
            print("\n🔘 Зарегистрированные callback обработчики:")
            for handler in self.handlers:
                if handler['type'] == 'on_callback':
                    print(f"   • {handler['arg']} -> {len(handler['commands'])} команд")
        
        try:
            await self.dp.start_polling(self.bot, skip_updates=True)
        except KeyboardInterrupt:
            print("\n⏹️ Интерпретатор остановлен")
        finally:
            await self.bot.session.close()

def main():
    """Главная функция"""
    print("🎯 Esybot Lang")
    print("=" * 70)
    
    debug_mode = '--debug' in sys.argv
    if debug_mode:
        sys.argv.remove('--debug')
    
    if len(sys.argv) < 2:
        print("\n📚 Использование: python final_esybot_interpreter.py <файл.esi> [--debug]")
        print("🔧 --debug - подробная отладка")
        print("   Ченж-лог")
        print("   🐍 Python блоки с функциями (esybot_set, esybot_get, esybot_send)")
        print("   📊 Все переменные и их замена ($variable)")
        print("   🎯 Все обработчики (on_start, on_message, on_callback, медиа)")
        print("   📝 Все команды (send, reply, edit, answer_callback)")
        print("   ⌨️ Клавиатуры с new_row, URL кнопками")
        print("   🎨 Parse mode (Markdown, HTML)")
        print("   ⚡ Интерпретация в реальном времени")
        return
    
    interpreter = FinalESYBOTInterpreter(debug_mode=debug_mode)
    
    try:
        if not interpreter.parse_file(sys.argv[1]):
            return
        
        if not interpreter.bot_token or interpreter.bot_token == "YOUR_TOKEN_HERE":
            print("❌ УСТАНОВИТЕ РЕАЛЬНЫЙ ТОКЕН БОТА!")
            print("   Получите токен у @BotFather и замените в файле .esi")
            return
        
        asyncio.run(interpreter.run_interpreter())
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
