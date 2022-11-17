import telegram
import asyncio

# token: 5696001611:AAGeYWR8lY4NxkJgzC4m6mnj62PjEEQQ1Y4


async def main():
    bot = telegram.Bot("5696001611:AAGeYWR8lY4NxkJgzC4m6mnj62PjEEQQ1Y4")
    async with bot:
        print(await bot.get_me())


if __name__ == '__main__':
    asyncio.run(main())

