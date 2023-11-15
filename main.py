import discord
from games import RedactedGame, TwentyQuestionsGame

BOT_STUFF_ID = 1173819549326524537

async def async_update_message(iterable, message: discord.Message):
    for item in iterable:
        should_yield = await item.update_message(message)
        if should_yield:
            yield item

async def async_update_reaction(iterable, reaction_event: discord.RawReactionActionEvent):
    for item in iterable:
        should_yield = await item.update_reaction(reaction_event)
        if should_yield:
            yield item

with open("discord.token", "r") as token_file:
    token = token_file.read()

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.games = set()
        
    async def on_raw_reaction_add(self, reaction_event: discord.RawReactionActionEvent):
        # Play each game, removing games that return False (done)
        self.games = {game async for game in async_update_reaction(self.games, reaction_event)}

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        
        if message.content.startswith('!hello'):
            await message.channel.send('Hello')
            return
        
        if message.content.startswith('!20q'):
            # Start a game
            if any(message.author.id == game.author.id for game in self.games):
                await message.channel.send('You have a game running')
                return
            if any(isinstance(game, TwentyQuestionsGame) for game in self.games):
                await message.channel.send('There is a game of this type running')
                return
            self.games.add(TwentyQuestionsGame(self, message))
            await message.channel.send('Starting 20 questions')
            return
        
        if message.channel.type == discord.ChannelType.private:
            # Start a game
            if any(message.author.id == game.author.id for game in self.games):
                await message.channel.send('You have a game running')
                return
            if any(isinstance(game, RedactedGame) for game in self.games):
                await message.channel.send('There is a game of this type running')
                return
            self.games.add(RedactedGame(self, message))
            await message.channel.send('Starting Redacted Game')
            return
        
        # Play each game, removing games that return False (done)
        self.games = {game async for game in async_update_message(self.games, message)}
                

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(token)