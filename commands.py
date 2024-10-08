import discord
from discord.ext import commands
import asyncio
import os
from openai import OpenAI
from ais import initialize_api_clients
import huggingface_hub
from gradio_client import Client
import requests
import sys
from data import save_level_data
import datetime
import config
import data

plugins = data.load_plugins()
user_pairs = data.load_pairs()
huggingface_hub.login(token='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')

previous_requests = {}

def setup_commands(bot, level_data, forbidden_words):
    @bot.command(name='?') 
    async def ask(ctx, *, request):
        global keys_list
        max_tries = 14
        retry_delay = 5 

        for i in range(max_tries): # Цикл для перебора ключей 
            if not keys_list: 
                await ctx.reply(embed=discord.Embed(title='Ошибка', description='Извините, ключи для использования закончились, возвращайтесь завтра.', color=discord.Color.red()))
                return 

            key = keys_list.pop(0) # Берем ключ 
            try:
                client = OpenAI(api_key=key, base_url="https://api.aimlapi.com/")

                previous_requests.append(request)

                messages = [
                    {
                        "role": "system",
                        "content": "You are an AI assistant who knows everything and speaks Russian.",
                    },
                ] + [{ "role": "user", "content": req } for req in previous_requests]

                response = client.chat.completions.create(model="gpt-4o", messages=messages)
                await ctx.defer(ephemeral=True)
                message = response.choices[0].message.content
                # Добавляем URL только если ответ получен успешно
                await ctx.reply(embed=discord.Embed(title="Assistaint", description=message, color=discord.Color.blue()))

                keys_list.append(key)  # Возвращаем ключ в список, если запрос успешен
                break 

            except Exception as e:
                print(f"Ошибка с ключом {key}: {e}")  # Логируем ошибку
                await ctx.reply(embed=discord.Embed(title='Ошибка', description='Ключ закончился.\nЗапрос повторится после замены ключа.\nИдет замена ключа...', color=discord.Color.yellow()))
                if i < max_tries - 1:
                    await asyncio.sleep(retry_delay)

    # @bot.command(name='img', help='Generate an image using Midjourney API')
    # async def generate(ctx, *, prompt):
    #     # Отправляем начальное сообщение с одной точкой
    #     thinking_message = await ctx.send(f'{bot.user.name} Думает...')

    #     try:
    #         # Основная генерация изображения
    #         result = imagine.predict(
    #             prompt=prompt,
    #             negative_prompt="(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime:1.4), text, close up, cropped, out of frame, worst quality, low quality, jpeg artifacts, ugly, duplicate, morbid, mutilated, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, blurry, dehydrated, bad anatomy, bad proportions, extra limbs, cloned face, disfigured, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers, long neck",
    #             use_negative_prompt=True,
    #             style="2560 x 1440",
    #             seed=0,
    #             width=1024,
    #             height=1024,
    #             guidance_scale=6,
    #             randomize_seed=True,
    #             api_name="/run"
    #         )

    #         # Получаем путь к изображению из результата
    #         image_path = result[0][0]['image']
    #         filename = os.path.basename(f"Images/{image_path}")

    #         # Сохраняем изображение в текущей директории"
    #         with open(filename, 'wb') as f:
    #             with open(image_path, 'rb') as img_f:
    #                 f.write(img_f.read())

    #         # Редактируем сообщение, заменяя его на изображение
    #         await thinking_message.edit(content=None, attachments=[discord.File(filename)])

    #         # Удаляем изображение после отправки
    #         os.remove(filename)

    #     except asyncio.CancelledError:
    #         # Игнорируем отмену,
    #         pass

    @bot.command(name='add_key')
    async def add_key(ctx, key: str):
        if len(key) != 32:
            await ctx.reply(embed=discord.Embed(title='Не правильный формат ключа!', description='Используйте **__ПРАВИЛЬНЫЙ__** ключ!', color=discord.Color.red()))
            return
        
        with open('Files/keys.txt', 'a') as f:
            f.write(key + '\n')
        
        # Получаем сервер и роль
        guild_id = 1250073805095698462  # ID сервера
        role_id = 1269935425724616797  # ID роли
        guild = bot.get_guild(guild_id)
        role = guild.get_role(role_id)
        
        # Получаем пользователя на сервере
        member = guild.get_member(ctx.author.id)
        
        # Добавляем роль пользователю
        if member:
            await member.add_roles(role)
            level_data[str(member.id)]["role"] = [role.name for role in member.roles]
        
        await ctx.reply(embed=discord.Embed(title=f'Ключ добавлен успешно!', description=f'API: `{key}`\nРоль на сервере Выдана!', color=discord.Color.green()))
        await ctx.message.delete()

    # @bot.command(name='ai')
    # async def ai(ctx, *, request):
    #     try:
    #         result = gh.predict(
    #             message=request,
    #             system_message="Ты персональный ИИ помощник который знает ВСЁ! и Разговаривает на русском языке.",
    #             max_tokens=512,
    #             temperature=0.5,
    #             top_p=0.95
    #         )
    #         await ctx.reply(embed=discord.Embed(
    #             title="Assistaint",
    #             description=f'{result}',
    #             color=discord.Color.blue()
    #         ))

    #     except Exception as error:
    #         print(f"ошибка: {error}")

    @bot.command()
    async def search_github(ctx, *, query: str):
        url = f"https://api.github.com/search/repositories?q={query}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('items', [])
            
            if results:
                reply = "Найденные репозитории:\n"
                for repo in results[:5]:  # Ограничим вывод до 5 результатов
                    repo_name = repo['name']
                    repo_url = repo['html_url']
                    reply += f"{repo_name}: {repo_url}\n"
            else:
                reply = "К сожалению, по вашему запросу ничего не найдено."
        else:
            reply = "Произошла ошибка при поиске. Попробуйте позже."

        await ctx.reply(embed=discord.Embed(title=reply, description='5 Первых репозиториев', color=discord.Color.dark_gray()))

    @bot.command()
    async def off(ctx):
        ctx.reply('Бот выключается...')
        exit()

    @bot.command(name='restart')
    @commands.has_guild_permissions(administrator=True)
    async def restart(ctx):
        await ctx.reply(embed=discord.Embed(title="Перезапуск", description="Бот перезапускается...", color=0xffa500))
        os.execv(sys.executable, ['python'] + sys.argv)

    @bot.command(name='stat')
    async def stat(ctx, member: discord.Member = None):
        member = member or ctx.author
        if str(member.id) in level_data:
            level_info = level_data[str(member.id)]
            char_count = level_info['characters']
            char_display = f"{char_count / 1000:.1f}K" if char_count >= 1000 else str(char_count)

            await ctx.reply(embed=discord.Embed(
                title=f"Статистика {member}",
                description=(
                    f"Роль: {', '.join(level_info['role'])}\n"
                    f"В чате с: {level_info['joined_at']}\n"
                    f"Последнее сообщение: {level_info['last_message_at']}\n"
                    f"Сообщений: {level_info['messages']}\n"
                    f"Символов: {char_display}\n"
                    f"Пересланных: {level_info['forwarded']}\n"
                    f"Смайлов: {level_info['emojis']}\n"
                    f"Сообщений с матом: {level_info['swear_messages']}\n"
                    f"Уровень: {level_info['level']}"
                ),
                color=0x0000ff
            ))
        else:
            await ctx.reply(embed=discord.Embed(title="Ошибка", description="Нет данных о пользователе.", color=0xff0000))

    @bot.command(name='top')
    async def top(ctx, page: int = 1):
        # Фильтрация записей без необходимых ключей и сортировка
        sorted_data = sorted(
            [(user_id, data) for user_id, data in level_data.items() if 'level' in data and 'messages' in data],
            key=lambda x: (x[1]['level'], x[1]['messages']),
            reverse=True
        )

    @bot.command(name='reset_data')
    async def reset_data(ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        if str(member.id) in level_data:
            level_data[str(member.id)] = {
                "role": [role.name for role in member.roles],
                "joined_at": str(member.joined_at),
                "last_message_at": str(datetime.now()),
                "warnings": 0,
                "messages": 0,
                "characters": 0,
                "forwarded": 0,
                "photos": 0,
                "commands": 0,
                "emojis": 0,
                "swear_messages": 0,
                "level": 0
            }
            save_level_data()
            await ctx.reply(embed=discord.Embed(title="Данные сброшены", description=f"Данные о пользователе {member.mention} были сброшены.", color=0x00ff00))
        else:
            await ctx.reply(embed=discord.Embed(title="Ошибка", description=f"Нет данных о пользователе {member.mention}.", color=0xff0000))

    @bot.command(name='help')
    async def help(ctx, vibor: str = ''):
        if vibor in plugins:
            plugin = plugins[vibor]
            help_embed = discord.Embed(
                title=plugin["title"],
                description=plugin["description"],
                color=plugin["color"]
            )
            for command in plugin["commands"]:
                if command["type"] == "command":
                    help_embed.add_field(name=command["name"], value=command["description"], inline=False)
                elif command["type"] == "text":
                    help_embed.description += f"{command['text']}\n\n"
            await ctx.reply(embed=help_embed)

        elif vibor == '':
            net_vibora = discord.Embed(title="**Выберите категорию:**", color=discord.Color.blue())
            for plugin_name in plugins:
                net_vibora.add_field(
                    name=f"`{plugin_name}`",
                    value=f"Использование: `.help {plugin_name}`\nОтправляет команды для {plugin_name}",
                    inline=False
                )
            await ctx.reply(embed=net_vibora)

        else:
            no_kat = discord.Embed(title="**Неизвестная категория!**", description='Используйте `.help` для просмотра всех категорий', color=discord.Color.red())
            await ctx.reply(embed=no_kat)

    @bot.command(name='start')
    async def send_welcome(ctx):
        await ctx.send("Добро пожаловать в Анонимный чат! Отправьте сообщение /connect, чтобы найти собеседника для общения.")

    @bot.command(name='connect')
    async def connect_users(ctx):
        user_id = ctx.author.id

        if user_id in user_pairs:
            await ctx.send("Вы уже подключены. Отправь /disconnect, чтобы завершить текущий чат.")
            return

        for user in user_pairs:
            if user_pairs[user] is None:
                partner_id = user
                user_pairs[user_id] = partner_id
                user_pairs[partner_id] = user_id

                partner_member = bot.get_user(partner_id)
                if partner_member:
                    await partner_member.send("Вы подключились! Поздоровайтесь.\nОтправь /disconnect чтоб отключиться.")
                await ctx.send("Вы подключились! Поздоровайтесь. Отправь /disconnect чтоб отключиться.")
                return

        user_pairs[user_id] = None
        await ctx.send("Ищем собеседника. Подождите...")
        await asyncio.sleep(1)

    @bot.command(name='disconnect')
    async def disconnect_users(ctx):
        user_id = ctx.author.id

        if user_id not in user_pairs or user_pairs[user_id] is None:
            await ctx.send("Вы ни к кому не подключены.")
            return

        partner_id = user_pairs[user_id]

        if partner_id is not None:
            partner_member = bot.get_user(partner_id)
            if partner_member:
                await partner_member.send("Ваш собеседник отключился :(\nОтправь /connect чтобы найти собеседника.")

        del user_pairs[user_id]
        if partner_id is not None:
            del user_pairs[partner_id]

        await ctx.send("Вы отключились. Отправь /connect чтобы найти собеседника.")

if __name__ == '__main__':
    print('Главный commands')