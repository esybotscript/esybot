#!/usr/bin/env python3
# esybot_simple.py - Версия с улучшенным Python синтаксисом

import asyncio
import sys
import re
import datetime
from typing import Dict, Any
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.storage.memory import MemoryStorage

class SimpleBotAdvanced:
    def __init__(self):
        self.config = {}
        self.variables = {}
        self.python_globals = {}
        
    def load(self, file_path):
        """Загрузка конфигурации с поддержкой Python блоков"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Парсим Python блоки отдельно
        content = self._parse_python_blocks(content)
        
        lines = content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1]
                if current_section not in self.config:
                    self.config[current_section] = {}
            elif '=' in line and current_section:
                key, value = line.split('=', 1)
                self.config[current_section][key.strip()] = value.strip()
        
        # Инициализация переменных
        if 'VARS' in self.config:
            for key, value in self.config['VARS'].items():
                self.variables[key] = self._parse_value(value)
        
        print(f"✅ Загружен бот: {self.config.get('BOT', {}).get('name', 'Simple Bot')}")
        print(f"📊 Переменных: {len(self.variables)}")
        print(f"🐍 Python блоков: {sum(1 for section in self.config.values() if isinstance(section, dict) and 'python' in section)}")
        
    def _parse_python_blocks(self, content):
        """Парсинг Python блоков с фигурными скобками"""
        def replace_python_block(match):
            python_code = match.group(1)
            # Убираем лишние отступы
            lines = python_code.strip().split('\n')
            cleaned_lines = []
            for line in lines:
                cleaned_lines.append(line.strip())
            
            # Возвращаем в формате python = код (для совместимости с парсером)
            return f"python = {repr('\\n'.join(cleaned_lines))}"
        
        # Ищем блоки вида python { ... }
        pattern = r'python\s*\{([^}]*)\}'
        content = re.sub(pattern, replace_python_block, content, flags=re.DOTALL)
        
        return content
    
    def _parse_value(self, value):
        """Парсинг значений с поддержкой типов"""
        value = value.strip()
        
        # Если это строка Python кода (в кавычках после python =)
        if value.startswith("'") and value.endswith("'"):
            return value[1:-1].replace('\\n', '\n')
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1].replace('\\n', '\n')
        
        # Булевы значения
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
            
        # Числа
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
            
        return value
    
    def replace_variables(self, text, context={}):
        """Замена переменных в тексте"""
        if not text:
            return text
            
        # Системные переменные
        now = datetime.datetime.now()
        system_vars = {
            'user_id': context.get('user_id', 0),
            'chat_id': context.get('chat_id', 0),
            'first_name': context.get('first_name', ''),
            'username': context.get('username', ''),
            'text': context.get('text', ''),
            'date': now.strftime('%Y-%m-%d'),
            'time': now.strftime('%H:%M:%S'),
            'datetime': now.strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        # Замена пользовательских переменных
        for var_name, var_value in self.variables.items():
            text = text.replace(f'${{{var_name}}}', str(var_value))
            text = text.replace(f'${var_name}', str(var_value))
        
        # Замена системных переменных
        for var_name, var_value in system_vars.items():
            text = text.replace(f'${{{var_name}}}', str(var_value))
            text = text.replace(f'${var_name}', str(var_value))
            
        # Замена переменных из Python блоков
        for var_name, var_value in self.python_globals.items():
            if not var_name.startswith('_'):
                text = text.replace(f'${{{var_name}}}', str(var_value))
                text = text.replace(f'${var_name}', str(var_value))
        
        return text
    
    def execute_python(self, code, context={}):
        """Выполнение Python кода с улучшенной обработкой"""
        if not code:
            return
            
        try:
            # Подготавливаем локальные переменные
            local_vars = {
                **self.variables,
                **context,
                **self.python_globals,
                'print': print  # Разрешаем print для отладки
            }
            
            print(f"🐍 Выполняется Python код:")
            for i, line in enumerate(code.split('\n'), 1):
                if line.strip():
                    print(f"   {i}: {line}")
            
            # Выполняем код
            exec(code, {"__builtins__": __builtins__}, local_vars)
            
            # Сохраняем новые переменные
            for key, value in local_vars.items():
                if key in self.variables:
                    self.variables[key] = value
                elif not key.startswith('_') and key not in context and key != 'print':
                    self.python_globals[key] = value
                    print(f"   ✅ Создана переменная: {key} = {value}")
                    
        except Exception as e:
            print(f"❌ Ошибка выполнения Python: {e}")
            import traceback
            traceback.print_exc()
    
    def check_condition(self, condition, context={}):
        """Проверка условий"""
        if not condition:
            return True
            
        # Заменяем переменные в условии
        condition = self.replace_variables(condition, context)
        
        try:
            # Добавляем поддержку переменных из Python блоков
            eval_context = {**self.python_globals}
            result = eval(condition, {"__builtins__": {}}, eval_context)
            print(f"🔍 Условие '{condition}' = {result}")
            return result
        except Exception as e:
            print(f"❌ Ошибка в условии '{condition}': {e}")
            return False
    
    def create_keyboard(self, section, context={}):
        """Создание клавиатуры из секции"""
        builder = InlineKeyboardBuilder()
        
        for key, value in section.items():
            if key.startswith('button'):
                # Заменяем переменные в кнопках
                value = self.replace_variables(value, context)
                
                parts = value.split('|')
                if len(parts) == 2:
                    text, callback = parts[0].strip(), parts[1].strip()
                    builder.button(text=text, callback_data=callback)
                elif len(parts) == 1:
                    text = parts[0].strip()
                    builder.button(text=text, callback_data=f"btn_{key}")
        
        return builder.as_markup() if len(builder.buttons) > 0 else None
    
    def process_effects(self, section, context={}):
        """Обработка эффектов секции"""
        # Выполнение Python кода ПЕРЕД проверкой условий
        if 'python' in section:
            self.execute_python(section['python'], context)
        
        # Проверка условий (теперь с учетом переменных из Python)
        if 'if' in section:
            if not self.check_condition(section['if'], context):
                # Обработка else ветки
                if 'else_text' in section:
                    return {
                        'text': self.replace_variables(section['else_text'], context),
                        'keyboard': self.create_else_keyboard(section, context),
                        'reply': section.get('else_reply', 'OK')
                    }
                return None
        
        # Увеличение переменных
        if 'inc' in section:
            var_name = section['inc']
            if var_name in self.variables:
                self.variables[var_name] += 1
            else:
                self.variables[var_name] = 1
            print(f"📈 Увеличена переменная {var_name} = {self.variables[var_name]}")
        
        # Уменьшение переменных
        if 'dec' in section:
            var_name = section['dec']
            if var_name in self.variables:
                self.variables[var_name] -= 1
            else:
                self.variables[var_name] = -1
            print(f"📉 Уменьшена переменная {var_name} = {self.variables[var_name]}")
        
        # Установка переменных
        if 'set' in section:
            parts = section['set'].split('=', 1)
            if len(parts) == 2:
                var_name, var_value = parts[0].strip(), parts[1].strip()
                self.variables[var_name] = self._parse_value(self.replace_variables(var_value, context))
                print(f"📝 Установлена переменная {var_name} = {self.variables[var_name]}")
        
        return {
            'text': self.replace_variables(section.get('text', ''), context),
            'keyboard': self.create_keyboard(section, context),
            'reply': self.replace_variables(section.get('reply', 'OK'), context)
        }
    
    def create_else_keyboard(self, section, context={}):
        """Создание клавиатуры для else ветки"""
        builder = InlineKeyboardBuilder()
        
        for key, value in section.items():
            if key.startswith('else_button'):
                value = self.replace_variables(value, context)
                parts = value.split('|')
                if len(parts) == 2:
                    text, callback = parts[0].strip(), parts[1].strip()
                    builder.button(text=text, callback_data=callback)
        
        return builder.as_markup() if len(builder.buttons) > 0 else None
        
    async def run(self):
        """Запуск бота"""
        bot = Bot(self.config['BOT']['token'])
        dp = Dispatcher(storage=MemoryStorage())
        
        # Контекст для передачи данных
        def get_context(update):
            if hasattr(update, 'from_user') and update.from_user:
                return {
                    'user_id': update.from_user.id,
                    'chat_id': update.chat.id if hasattr(update, 'chat') and update.chat else update.from_user.id,
                    'first_name': update.from_user.first_name or '',
                    'username': f"@{update.from_user.username}" if update.from_user.username else '',
                    'text': getattr(update, 'text', '') or ''
                }
            return {}
        
        # Обработчик /start
        @dp.message(Command("start"))
        async def start_handler(message: Message):
            if 'START' not in self.config:
                await message.answer("Команда /start не настроена")
                return
                
            context = get_context(message)
            result = self.process_effects(self.config['START'], context)
            
            if result:
                await message.answer(result['text'], reply_markup=result['keyboard'])
        
        # Обработчики кнопок
        for section_name, section_config in self.config.items():
            if section_name not in ['BOT', 'VARS', 'START', 'MESSAGE', 'PHOTO', 'DOCUMENT', 'VOICE']:
                @dp.callback_query(F.data == section_name)
                async def callback_handler(query: CallbackQuery, section=section_config):
                    context = get_context(query)
                    result = self.process_effects(section, context)
                    
                    if result and result['text']:
                        await query.message.edit_text(result['text'], reply_markup=result['keyboard'])
                        await query.answer(result['reply'])
        
        # Остальные обработчики (медиа, сообщения) остаются без изменений...
        
        print(f"🚀 {self.config.get('BOT', {}).get('name', 'Simple Bot')} запущен!")
        await dp.start_polling(bot)

def main():
    if len(sys.argv) < 2:
        print("Использование: python esybot_simple.py bot.simple")
        return
        
    bot = SimpleBotAdvanced()
    bot.load(sys.argv[1])
    asyncio.run(bot.run())

if __name__ == "__main__":
    main()
