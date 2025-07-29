#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ESYBOT FINAL WIKI-COMPATIBLE INTERPRETER
✅ Fixed buttons ✅ Fixed Python blocks ✅ 100% Wiki-compatibility
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
    """Final ESYBOT interpreter with full Wiki-compatibility"""
    
    def __init__(self, debug_mode: bool = False, lang: str = 'en'):
        self.debug = debug_mode
        self.lang = lang
        self.bot_token = ""
        self.variables: Dict[str, Any] = {}
        self.handlers: List[Dict] = []
        self.keyboards: Dict[str, Any] = {}
        self.bot: Optional[Bot] = None
        self.dp: Optional[Dispatcher] = None
        
        # Translation dictionary
        self.texts = {
            'en': {
                'parsing_file': "📝 Parsing file: {}",
                'parsing_completed': "✅ Wiki-compatible parsing completed:",
                'handlers_count': "   🎯 Handlers: {}",
                'keyboards_count': "   ⌨️ Keyboards: {}",
                'variables_count': "   📊 Variables: {}",
                'error_parsing': "❌ Parsing error: {}",
                'bot_token_found': "🔑 Bot token found",
                'inline_menu_created': "⌨️ Created inline menu: {}",
                'reply_keyboard_created': "⌨️ Created reply keyboard: {}",
                'handler_created': "🎯 Created handler: {} {}",
                'var_debug': "📊 Variable: {} = {}",
                'error_parsing_var': "⚠️ Error parsing variable: {}",
                'error_parsing_menu': "⚠️ Error parsing menu: {}",
                'button_debug': "   🔘 Button: {} -> {}",
                'python_block_empty': "   ⚠️ Python block is empty, skipping",
                'python_executing': "   🐍 Executing Python code ({} lines)",
                'python_success': "   ✅ Python block executed successfully",
                'python_updated_vars': "      📊 Updated variables: {}",
                'python_new_vars': "      📊 New variables: {}",
                'python_name_error': "❌ Variable not found in Python code: {}",
                'python_syntax_error': "❌ Syntax error in Python code: {}",
                'python_general_error': "❌ Python code execution error: {}",
                'send_command': "   📤 Sent message: {}...",
                'callback_answer': "   📝 Callback answer: {}",
                'callback_handler': "🔥 CALLBACK: {} from user {}, data: '{}'",
                'message_handler': "🔥 MESSAGE: {} from user {}, text: '{}'",
                'handler_error': "❌ Error in {} handler: {}",
                'interpreter_start': "🎯 ESYBOT script running!",
                'handlers_registered': "🔗 Message handlers: {}",
                'callbacks_registered': "🔗 Callback handlers: {}",
                'keyboards_loaded': "⌨️ Keyboards loaded: {}",
                'variables_loaded': "📊 Variables loaded: {}",
                'callback_handlers': "\n🔘 Registered callback handlers:",
                'interpreter_stopped': "⏹️ Interpreter stopped",
                'critical_error': "❌ CRITICAL ERROR: {}",
                'no_token': "❌ NO REAL BOT TOKEN SET!",
                'token_instructions': "   Get token from @BotFather and replace in .esi file",
                'menu_parsing': "🔧 Parsing menu: {}",
                'button_created': "   ✅ {} button: {} -> {}",
                'python_normalized': "   🔧 Python code normalized (removed {}-space indent)",
                'python_functions': "   💡 Available ESYBOT functions:",
                'function_set': "      • esybot_set('var_name', value) - set variable",
                'function_get': "      • esybot_get('var_name') - get variable",
                'function_inc': "      • esybot_increment('var_name') - increment variable",
                'function_dec': "      • esybot_decrement('var_name') - decrement variable",
                'function_send': "      • await esybot_send('text', keyboard='name') - send message",
                'problem_code': "   📝 Problematic code:",
                'line_num': "   {:2d}: {}",
                'error_parsing_handler': "⚠️ Error parsing handler: {}",
                'error_parsing_button': "⚠️ Error parsing button: {}",
                'error_parsing_python': "⚠️ Error parsing Python block: {}",
                'error_normalizing_python': "⚠️ Error normalizing Python code: {}",
                'error_send_command': "❌ Error in send command: {}",
                'error_reply_command': "❌ Error in reply command: {}",
                'error_edit_command': "❌ Error in edit command: {}",
                'error_callback_command': "❌ Error in answer_callback command: {}",
                'error_set_command': "❌ Error in set command: {}",
                'keyboard_used': "   📱 Using keyboard: {}",
            },
            'ru': {
                'parsing_file': "📝 Парсинг файла: {}",
                'parsing_completed': "✅ Wiki-совместимый парсинг завершён:",
                'handlers_count': "   🎯 Обработчиков: {}",
                'keyboards_count': "   ⌨️ Клавиатур: {}",
                'variables_count': "   📊 Переменных: {}",
                'error_parsing': "❌ Ошибка парсинга: {}",
                'bot_token_found': "🔑 Найден токен бота",
                'inline_menu_created': "⌨️ Создано inline меню: {}",
                'reply_keyboard_created': "⌨️ Создана reply клавиатура: {}",
                'handler_created': "🎯 Создан обработчик: {} {}",
                'var_debug': "📊 Переменная: {} = {}",
                'error_parsing_var': "⚠️ Ошибка парсинга переменной: {}",
                'error_parsing_menu': "⚠️ Ошибка парсинга меню: {}",
                'button_debug': "   🔘 Кнопка: {} -> {}",
                'python_block_empty': "   ⚠️ Python блок пустой, пропускаем",
                'python_executing': "   🐍 Выполняем Python код ({} строк)",
                'python_success': "   ✅ Python блок выполнен успешно",
                'python_updated_vars': "      📊 Обновлены переменные: {}",
                'python_new_vars': "      📊 Новые переменные: {}",
                'python_name_error': "❌ Переменная не найдена в Python коде: {}",
                'python_syntax_error': "❌ Синтаксическая ошибка в Python коде: {}",
                'python_general_error': "❌ Ошибка выполнения Python кода: {}",
                'send_command': "   📤 Отправлено сообщение: {}...",
                'callback_answer': "   📝 Callback ответ: {}",
                'callback_handler': "🔥 CALLBACK: {} от пользователя {}, data: '{}'",
                'message_handler': "🔥 MESSAGE: {} от пользователя {}, текст: '{}'",
                'handler_error': "❌ Ошибка в обработчике {}: {}",
                'interpreter_start': "🎯 Esybot скрипт запущен!",
                'handlers_registered': "🔗 Обработчиков сообщений: {}",
                'callbacks_registered': "🔗 Обработчиков callback: {}",
                'keyboards_loaded': "⌨️ Клавиатур: {}",
                'variables_loaded': "📊 Переменных: {}",
                'callback_handlers': "\n🔘 Зарегистрированные callback обработчики:",
                'interpreter_stopped': "⏹️ Интерпретатор остановлен",
                'critical_error': "❌ КРИТИЧЕСКАЯ ОШИБКА: {}",
                'no_token': "❌ УСТАНОВИТЕ РЕАЛЬНЫЙ ТОКЕН БОТА!",
                'token_instructions': "   Получите токен у @BotFather и замените в файле .esi",
                'menu_parsing': "🔧 Парсинг меню: {}",
                'button_created': "   ✅ {} кнопка: {} -> {}",
                'python_normalized': "   🔧 Python код нормализован (убран отступ {} пробелов)",
                'python_functions': "   💡 Доступные ESYBOT функции:",
                'function_set': "      • esybot_set('var_name', value) - установить переменную",
                'function_get': "      • esybot_get('var_name') - получить переменную",
                'function_inc': "      • esybot_increment('var_name') - увеличить переменную",
                'function_dec': "      • esybot_decrement('var_name') - уменьшить переменную",
                'function_send': "      • await esybot_send('text', keyboard='name') - отправить сообщение",
                'problem_code': "   📝 Проблемный код:",
                'line_num': "   {:2d}: {}",
                'error_parsing_handler': "⚠️ Ошибка парсинга обработчика: {}",
                'error_parsing_button': "⚠️ Ошибка парсинга кнопки: {}",
                'error_parsing_python': "⚠️ Ошибка парсинга Python блока: {}",
                'error_normalizing_python': "⚠️ Ошибка нормализации Python кода: {}",
                'error_send_command': "❌ Ошибка команды send: {}",
                'error_reply_command': "❌ Ошибка команды reply: {}",
                'error_edit_command': "❌ Ошибка команды edit: {}",
                'error_callback_command': "❌ Ошибка команды answer_callback: {}",
                'error_set_command': "❌ Ошибка команды set: {}",
                'keyboard_used': "   📱 Используется клавиатура: {}",
            }
        }

    def t(self, key: str, *args) -> str:
        """Get translated string"""
        return self.texts[self.lang].get(key, key).format(*args)
    
    def debug_print(self, message: str) -> None:
        if self.debug:
            print(message)
    
    def parse_file(self, filename: str) -> bool:
        """Wiki-compatible file parsing"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(self.t('parsing_file', filename))
            self._parse_content(content)
            print(self.t('parsing_completed'))
            print(self.t('handlers_count', len(self.handlers)))
            print(self.t('keyboards_count', len(self.keyboards)))
            print(self.t('variables_count', len(self.variables)))
            return True
            
        except Exception as e:
            print(self.t('error_parsing', e))
            return False
    
    def _parse_content(self, content: str) -> None:
        """Wiki-compatible content parsing"""
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
                        print(self.t('inline_menu_created', menu_data['name']))
                    i = next_i
                    continue
                elif line.startswith('keyboard '):
                    keyboard_data, next_i = self._parse_keyboard(lines, i)
                    if keyboard_data:
                        self.keyboards[keyboard_data['name']] = self._create_reply_keyboard(keyboard_data)
                        print(self.t('reply_keyboard_created', keyboard_data['name']))
                    i = next_i
                    continue
                elif line.startswith('on_'):
                    handler_data, next_i = self._parse_handler(lines, i)
                    if handler_data:
                        self.handlers.append(handler_data)
                        print(self.t('handler_created', handler_data['type'], handler_data['arg']))
                    i = next_i
                    continue
                
            except Exception as e:
                print(f"⚠️ Error in line {i+1}: {e}")
            
            i += 1
    
    def _parse_bot_token(self, line: str) -> None:
        """Parse bot token"""
        match = re.search(r'"([^"]*)"', line)
        if match:
            self.bot_token = match.group(1)
            print(self.t('bot_token_found'))
    
    def _parse_variable(self, line: str) -> None:
        """Wiki-compatible variable parsing"""
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
            print(self.t('var_debug', name, value))
            
        except Exception as e:
            print(self.t('error_parsing_var', e))
    
    def _parse_menu(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """Wiki-compatible inline menu parsing"""
        try:
            menu_line = lines[start].strip()
            
            if menu_line.endswith('{'):
                parts = menu_line[:-1].strip().split()
            else:
                parts = menu_line.split()
            
            if len(parts) < 2:
                return None, start + 1
            
            menu_name = parts[1]
            self.debug_print(self.t('menu_parsing', menu_name))
            
            # Find block start
            i = start + 1
            if not menu_line.endswith('{'):
                while i < len(lines) and lines[i].strip() != '{':
                    i += 1
                if i >= len(lines):
                    return None, start + 1
                i += 1
            
            # Parse buttons
            buttons = []
            while i < len(lines) and lines[i].strip() != '}':
                line = lines[i].strip()
                if line.startswith('button '):
                    button_info = self._parse_button(line)
                    if button_info:
                        buttons.append(button_info)
                        self.debug_print(self.t('button_debug', button_info['text'], button_info.get('data', 'N/A')))
                i += 1
            
            menu_data = {
                'type': 'inline',
                'name': menu_name,
                'buttons': buttons
            }
            
            return menu_data, i + 1
            
        except Exception as e:
            print(self.t('error_parsing_menu', e))
            return None, start + 1
    
    def _parse_keyboard(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """Wiki-compatible reply keyboard parsing"""
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
            print(self.t('error_parsing_menu', e))
            return None, start + 1
    
    def _parse_handler(self, lines: List[str], start: int) -> Tuple[Optional[Dict], int]:
        """Wiki-compatible handler parsing"""
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
            
            self.debug_print(f"🔧 Parsing handler: {handler_type} {handler_arg}")
            
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
            print(self.t('error_parsing_handler', e))
            return None, start + 1
    
    def _parse_button(self, line: str) -> Optional[Dict[str, Any]]:
        """FIXED button parsing"""
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
                # Create safe callback_data from button text
                safe_data = quotes[0].lower().replace(' ', '_')
                safe_data = re.sub(r'[🎯🎲🐍🌐📊🆘🏠❓📞📷📄🎤😀]', '', safe_data)
                safe_data = re.sub(r'[^\w_-]', '', safe_data)
                button_info['data'] = safe_data or 'button'
            
            return button_info
            
        except Exception as e:
            print(self.t('error_parsing_button', e))
            return None
    
    def _parse_python_block(self, lines: List[str], start: int) -> Tuple[str, int]:
        """Wiki-compatible smart Python block parsing"""
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
            print(self.t('error_parsing_python', e))
            return "", start + 1

    def _create_inline_keyboard(self, menu_data: Dict) -> InlineKeyboardMarkup:
        """FIXED inline keyboard creation"""
        builder = InlineKeyboardBuilder()
        
        for btn in menu_data['buttons']:
            try:
                if 'url' in btn:
                    builder.button(text=btn['text'], url=btn['url'])
                    self.debug_print(self.t('button_created', 'URL', btn['text'], btn['url']))
                else:
                    callback_data = btn['data']
                    # Limit callback_data to 64 bytes
                    if len(callback_data.encode('utf-8')) > 64:
                        callback_data = callback_data[:60] + str(hash(callback_data) % 1000)
                    
                    builder.button(text=btn['text'], callback_data=callback_data)
                    self.debug_print(self.t('button_created', 'Callback', btn['text'], callback_data))
                
                if btn.get('new_row', False):
                    builder.row()
                    
            except Exception as e:
                print(f"⚠️ Button creation error {btn.get('text', 'N/A')}: {e}")
        
        return builder.as_markup()
    
    def _create_reply_keyboard(self, keyboard_data: Dict) -> ReplyKeyboardMarkup:
        """Wiki-compatible reply keyboard creation"""
        builder = ReplyKeyboardBuilder()
        
        for btn in keyboard_data['buttons']:
            builder.button(text=btn['text'])
            if btn.get('new_row', False):
                builder.row()
        
        return builder.as_markup(resize_keyboard=True)
    
    async def _execute_commands(self, commands: List[Dict], context: Dict[str, Any]) -> None:
        """Wiki-compatible command execution"""
        for cmd in commands:
            try:
                if cmd['type'] == 'python':
                    await self._execute_python_code(cmd['code'], context)
                elif cmd['type'] == 'command':
                    await self._execute_esybot_command(cmd['line'], context)
            except Exception as e:
                print(f"❌ Command execution error: {e}")
    
    async def _execute_python_code(self, code: str, context: Dict[str, Any]) -> None:
        """FIXED Python code execution with ESYBOT functions"""
        try:
            # Normalize Python code indentation
            normalized_code = self._normalize_python_code(code)
            
            if not normalized_code.strip():
                self.debug_print(self.t('python_block_empty'))
                return
            
            line_count = len(normalized_code.split('\n'))
            self.debug_print(self.t('python_executing', line_count))
            
            # KEY FIX: Add ESYBOT functions
            def esybot_set(var_name: str, value: Any) -> None:
                """Set ESYBOT variable"""
                self.variables[var_name] = value
                
            def esybot_get(var_name: str, default: Any = None) -> Any:
                """Get ESYBOT variable"""
                return self.variables.get(var_name, default)
                
            def esybot_increment(var_name: str, amount: int = 1) -> None:
                """Increment ESYBOT variable"""
                if var_name in self.variables:
                    try:
                        self.variables[var_name] += amount
                    except:
                        self.variables[var_name] = amount
                else:
                    self.variables[var_name] = amount
                    
            def esybot_decrement(var_name: str, amount: int = 1) -> None:
                """Decrement ESYBOT variable"""
                if var_name in self.variables:
                    try:
                        self.variables[var_name] -= amount
                    except:
                        self.variables[var_name] = -amount
                else:
                    self.variables[var_name] = -amount
            
            async def esybot_send(text: str, chat_id: int = None, keyboard: str = None, parse_mode: str = None) -> None:
                """Send message from Python block"""
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
            
            # Prepare full environment for Python code
            local_vars = {
                **context,
                **self.variables,
                # Core modules
                'bot': self.bot,
                'random': random,
                'datetime': datetime,
                'json': json,
                'os': os,
                're': re,
                'math': math,
                'time': time,
                # ESYBOT functions
                'esybot_set': esybot_set,
                'esybot_get': esybot_get,
                'esybot_increment': esybot_increment,
                'esybot_decrement': esybot_decrement,
                'esybot_send': esybot_send,
                # Synonyms for convenience
                'set_var': esybot_set,
                'get_var': esybot_get,
            }
            
            # Execute normalized Python code
            exec(normalized_code, {'__builtins__': __builtins__}, local_vars)
            
            # Update ESYBOT variables (in case of direct changes)
            updated_vars = []
            for var_name in list(self.variables.keys()):
                if var_name in local_vars and local_vars[var_name] != self.variables[var_name]:
                    self.variables[var_name] = local_vars[var_name]
                    updated_vars.append(f"{var_name}={local_vars[var_name]}")
            
            # Add new variables
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
            
            self.debug_print(self.t('python_success'))
            if updated_vars:
                self.debug_print(self.t('python_updated_vars', ', '.join(updated_vars)))
            if new_vars:
                self.debug_print(self.t('python_new_vars', ', '.join(new_vars)))
            
        except NameError as e:
            print(self.t('python_name_error', e))
            print(self.t('python_functions'))
            print(self.t('function_set'))
            print(self.t('function_get'))
            print(self.t('function_inc'))
            print(self.t('function_dec'))
            print(self.t('function_send'))
            if self.debug:
                print(self.t('problem_code'))
                for i, line in enumerate(code.split('\n'), 1):
                    print(self.t('line_num', i, line))
        except SyntaxError as e:
            print(self.t('python_syntax_error', e))
            print(f"   📍 Line {e.lineno}: {e.text}")
            if self.debug:
                print(self.t('problem_code'))
                for i, line in enumerate(code.split('\n'), 1):
                    marker = " >>> " if i == e.lineno else "     "
                    print(f"   {i:2d}{marker}{repr(line)}")
        except Exception as e:
            print(self.t('python_general_error', e))
            if self.debug:
                print(self.t('problem_code'))
                for i, line in enumerate(code.split('\n'), 1):
                    print(self.t('line_num', i, repr(line)))
                import traceback
                traceback.print_exc()

    def _normalize_python_code(self, code: str) -> str:
        """Normalize Python code indentation for exec()"""
        try:
            lines = code.split('\n')
            
            # Remove empty lines at start/end
            while lines and not lines[0].strip():
                lines.pop(0)
            while lines and not lines[-1].strip():
                lines.pop()
            
            if not lines:
                return ""
            
            # Find minimum indent among non-empty lines
            min_indent = float('inf')
            for line in lines:
                if line.strip():  # Only non-empty lines
                    indent = len(line) - len(line.lstrip())
                    min_indent = min(min_indent, indent)
            
            # If all lines have no indent, return as is
            if min_indent == 0 or min_indent == float('inf'):
                normalized = '\n'.join(lines)
                self.debug_print("   🔧 Python code already normalized")
                return normalized
            
            # Remove minimal indent from all lines
            normalized_lines = []
            for line in lines:
                if line.strip():  # Non-empty lines
                    normalized_lines.append(line[min_indent:])
                else:  # Empty lines
                    normalized_lines.append("")
            
            result = '\n'.join(normalized_lines)
            
            self.debug_print(self.t('python_normalized', min_indent))
            
            return result
            
        except Exception as e:
            print(self.t('error_normalizing_python', e))
            return code
    
    async def _execute_esybot_command(self, line: str, context: Dict[str, Any]) -> None:
        """Wiki-compatible ESYBOT command execution"""
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
        """FIXED send command execution"""
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
                        self.debug_print(self.t('keyboard_used', kb_name))
            
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
            
            self.debug_print(self.t('send_command', text[:50]))
            
        except Exception as e:
            print(self.t('error_send_command', e))
    
    async def _execute_reply_command(self, line: str, context: Dict[str, Any]) -> None:
        """Reply command execution"""
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
            print(self.t('error_reply_command', e))
    
    async def _execute_edit_command(self, line: str, context: Dict[str, Any]) -> None:
        """FIXED edit command execution"""
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
                self.debug_print(self.t('send_command', text[:50]))
            
        except Exception as e:
            print(self.t('error_edit_command', e))
    
    async def _execute_answer_callback_command(self, line: str, context: Dict[str, Any]) -> None:
        """FIXED answer_callback command execution"""
        try:
            match = re.search(r'"([^"]*)"', line)
            text = match.group(1) if match else ""
            text = self._replace_variables(text, context)
            
            show_alert = 'alert=true' in line
            
            update = context.get('update')
            if update and isinstance(update, CallbackQuery):
                await update.answer(text=text, show_alert=show_alert)
                self.debug_print(self.t('callback_answer', text))
            
        except Exception as e:
            print(self.t('error_callback_command', e))
    
    async def _execute_set_command(self, line: str, context: Dict[str, Any]) -> None:
        """Set command execution"""
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
            print(self.t('error_set_command', e))
    
    def _execute_increment_command(self, line: str) -> None:
        """Increment command execution"""
        parts = line.split()
        if len(parts) > 1:
            var_name = parts[1]
            if var_name in self.variables:
                try:
                    self.variables[var_name] += 1
                except:
                    self.variables[var_name] = 1
    
    def _execute_decrement_command(self, line: str) -> None:
        """Decrement command execution"""
        parts = line.split()
        if len(parts) > 1:
            var_name = parts[1]
            if var_name in self.variables:
                try:
                    self.variables[var_name] -= 1
                except:
                    self.variables[var_name] = -1
    
    def _replace_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Wiki-compatible variable replacement"""
        # Replace ESYBOT variables
        for var_name, var_value in self.variables.items():
            text = text.replace(f'${var_name}', str(var_value))
        
        # Replace system variables
        text = text.replace('$user_id', str(context.get('user_id', 0)))
        text = text.replace('$chat_id', str(context.get('chat_id', 0)))
        text = text.replace('$first_name', str(context.get('first_name', '')))
        text = text.replace('$username', str(context.get('username', '')))
        text = text.replace('$text', str(context.get('text', '')))
        text = text.replace('$data', str(context.get('data', '')))
        
        return text
    
    async def _create_handler(self, handler_data: Dict) -> None:
        """FIXED handler creation"""
        handler_type = handler_data['type']
        handler_arg = handler_data['arg']
        commands = handler_data['commands']
        
        async def handler_func(update: Union[Message, CallbackQuery], state: FSMContext = None):
            try:
                # Correct context definition
                context = {
                    'update': update,
                    'user_id': 0,
                    'first_name': '',
                    'username': '',
                    'text': '',
                    'data': '',
                    'chat_id': 0,
                }
                
                # Determine update type and extract data
                if isinstance(update, CallbackQuery):
                    context.update({
                        'user_id': update.from_user.id,
                        'first_name': update.from_user.first_name or '',
                        'username': f"@{update.from_user.username}" if update.from_user.username else '',
                        'chat_id': update.message.chat.id if update.message else update.from_user.id,
                        'text': update.data or '',
                        'data': update.data or '',
                    })
                    print(self.t('callback_handler', handler_type, context['user_id'], context['data']))
                    
                elif isinstance(update, Message):
                    context.update({
                        'user_id': update.from_user.id if update.from_user else 0,
                        'first_name': update.from_user.first_name or '' if update.from_user else '',
                        'username': f"@{update.from_user.username}" if update.from_user and update.from_user.username else '',
                        'chat_id': update.chat.id,
                        'text': update.text or update.caption or '',
                        'data': '',
                    })
                    print(self.t('message_handler', handler_type, context['user_id'], context['text'][:50]))
                
                # EXECUTE COMMANDS
                await self._execute_commands(commands, context)
                
            except Exception as e:
                print(self.t('handler_error', handler_type, e))
                import traceback
                traceback.print_exc()
        
        # Correct handler registration
        if handler_type == 'on_start':
            self.dp.message.register(handler_func, Command(commands=["start"]))
        elif handler_type == 'on_message':
            if handler_arg == '*':
                # Catch all messages
                self.dp.message.register(handler_func)
            elif handler_arg:
                self.dp.message.register(handler_func, F.text == handler_arg)
            else:
                # Catch all text messages
                self.dp.message.register(handler_func, F.text)
        elif handler_type == 'on_command':
            if handler_arg:
                self.dp.message.register(handler_func, Command(commands=[handler_arg]))
        elif handler_type == 'on_callback':
            # KEY FIX: Proper callback handler registration
            if handler_arg and handler_arg != '*':
                print(self.t('handler_created', 'callback', handler_arg))
                self.dp.callback_query.register(handler_func, F.data == handler_arg)
            else:
                print("🔗 Registering general callback handler")
                self.dp.callback_query.register(handler_func)
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
        """Run final interpreter"""
        if not self.bot_token:
            print("❌ No bot token specified!")
            return
        
        # Create bot and dispatcher
        self.bot = Bot(self.bot_token)
        self.dp = Dispatcher(storage=MemoryStorage())
        
        # Register all handlers
        for handler_data in self.handlers:
            await self._create_handler(handler_data)
        
        print(self.t('interpreter_start'))
        print("=" * 60)
        print(self.t('handlers_registered', len(self.dp.message.handlers)))
        print(self.t('callbacks_registered', len(self.dp.callback_query.handlers)))
        print(self.t('keyboards_loaded', len(self.keyboards)))
        print(self.t('variables_loaded', len(self.variables)))
        
        # Print callback handler info
        if self.dp.callback_query.handlers:
            print(self.t('callback_handlers'))
            for handler in self.handlers:
                if handler['type'] == 'on_callback':
                    print(f"   • {handler['arg']} -> {len(handler['commands'])} commands")
        
        try:
            await self.dp.start_polling(self.bot, skip_updates=True)
        except KeyboardInterrupt:
            print(f"\n{self.t('interpreter_stopped')}")
        finally:
            await self.bot.session.close()

def main():
    """Main function"""
    print("🎯 ESYBOT Language Interpreter")
    print("=" * 70)
    
    debug_mode = '--debug' in sys.argv
    if debug_mode:
        sys.argv.remove('--debug')
    
    lang = 'en'
    if '--lang=ru' in sys.argv:
        lang = 'ru'
        sys.argv.remove('--lang=ru')
    elif '--lang=en' in sys.argv:
        sys.argv.remove('--lang=en')
    
    if len(sys.argv) < 2:
        print("\n📚 Usage: python esybot_interpreter.py <file.esi> [--debug] [--lang=en|ru]")
        print("🔧 --debug - detailed debugging")
        print("🔧 --lang - language selection (en/ru)")
        print("\n   Change log:")
        print("   🐍 Python blocks with functions (esybot_set, esybot_get, esybot_send)")
        print("   📊 All variables and their replacement ($variable)")
        print("   🎯 All handlers (on_start, on_message, on_callback, media)")
        print("   📝 All commands (send, reply, edit, answer_callback)")
        print("   ⌨️ Keyboards with new_row, URL buttons")
        print("   🎨 Parse mode (Markdown, HTML)")
        print("   ⚡ Real-time interpretation")
        return
    
    interpreter = FinalESYBOTInterpreter(debug_mode=debug_mode, lang=lang)
    
    try:
        if not interpreter.parse_file(sys.argv[1]):
            return
        
        if not interpreter.bot_token or interpreter.bot_token == "YOUR_TOKEN_HERE":
            print(interpreter.t('no_token'))
            print(interpreter.t('token_instructions'))
            return
        
        asyncio.run(interpreter.run_interpreter())
        
    except Exception as e:
        print(interpreter.t('critical_error', e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
