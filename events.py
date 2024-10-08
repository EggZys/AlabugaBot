import discord
from discord.ext import commands
from datetime import datetime, date
import emoji
from data import save_level_data
from config import PAIRS

user_pairs = PAIRS

def setup_events(bot, level_data, forbidden_words):
    @bot.event
    async def on_ready():
        print(f'Бот подключился к Дискорду как {bot.user} - {bot.user.id}')
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=".help"))

    @bot.event
    async def on_member_join(member):
        # Отправляем личное сообщение пользователю
        try:
            embed = discord.Embed(title='Добро пожаловать!', description='Это описание', color=discord.Color.green())
            embed.add_field(name='Привествуем тебя на нашем сервере!', value='Спасибо, что решил к нам присоедениться', inline=False)
            embed.add_field(name='Пожалуйста, прочитай правила данного сервера', value='Чтобы не случалось плохих инцидентов', inline=True)
            embed.add_field(name='Также просим:', value='Измени свой никнейм на твое реальное имя, чтобы с тобой Было удобно взаимодействовать!', inline=False)
            embed.add_field(name='Спасибо большое', value='И приятного времени припровождения!', inline=False)
            await member.send(embed=embed)
        except discord.Forbidden:
            print(f'Не удалось отправить сообщение пользователю {member.mention}')
        with open(f"Logs_{datetime.date.today().isoformat()}.txt", "a", encoding="utf-8") as f:
            f.write(f"Пользователь  {member.mention} присоединился к серверу.\n")

    @bot.event
    async def on_message(message):
        if message.guild is None and message.author != bot.user:
            if message.author.id in user_pairs and user_pairs[message.author.id] is not None:
                if message.content.startswith(bot.command_prefix):
                    # Обработка команды
                    await bot.process_commands(message)
                    return
                partner_id = user_pairs[message.author.id]
                partner_member = bot.get_user(partner_id)
                if partner_member:
                    uncipher_message=message
                    await partner_member.send(embed=discord.Embed(title=message.author.name, description=uncipher_message, color=discord.Color.green()))
            else:
                await message.author.send("Вы не подключены к собеседнику. Отправьте /connect, чтобы найти собеседника.")
        else:
            member = message.guild.get_member(message.author.id)
            # Update the role data
            if str(member.id) in level_data:
                level_data[str(member.id)]["role"] = [role.name for role in member.roles]

            # Проверка и обновление данных пользователя
            if str(message.author.id) not in level_data:
                level_data[str(message.author.id)] = {
                    "role": [role.name for role in message.author.roles],
                    "joined_at": str(message.author.joined_at),
                    "last_message_at": str(datetime.now()),
                    "messages": 0,
                    "characters": 0,
                    "forwarded": 0,
                    "emojis": 0,
                    "swear_messages": 0,
                    "level": 0
                }

            level_data[str(message.author.id)]["messages"] += 1
            level_data[str(message.author.id)]["characters"] += len(message.content)
            level_data[str(message.author.id)]["emojis"] += emoji.emoji_count(message.content)
            level_data[str(message.author.id)]["last_message_at"] = str(datetime.now())

            if any(word in message.content.lower() for word in forbidden_words):
                level_data[str(message.author.id)]["swear_messages"] += 1
                print(f"[{datetime.now()}] ({message.channel}) [МАТ] {message.author} > {message.content}")
            else:
                print(f"[{datetime.now()}] ({message.channel}) [CHAT] {message.author} > {message.content}")

            # Save message log to file
            with open(f"Logs {date.today().isoformat()}.txt", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] ({message.channel}) {message.author} > {message.content}\n")

            # Проверка и повышение уровня
            if level_data[str(message.author.id)]["messages"] % 100 == 0:
                level_data[str(message.author.id)]["level"] += 1
                await message.channel.send(embed=discord.Embed(
                    title="Новый уровень!",
                    description=f"{message.author.mention}, теперь у тебя уровень: {level_data[str(message.author.id)]['level']}!",
                    color=0x00ff00
                ))

            save_level_data()
            await bot.process_commands(message)

if __name__ == '__main__':
    print('Главный events')