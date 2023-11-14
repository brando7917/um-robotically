import discord
from games import RedactedGame

with open("discord.token", "r") as token_file:
    token = token_file.read()

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')
        self.games = set()

    async def on_message(self, message):
        print(f'Message from {message.author}: {message.content}')
        if message.author == self.user:
            return
        
        if message.content.startswith('!hello'):
            await message.channel.send('Hello')
            return
        
        if message.channel.type == discord.ChannelType.private:
            # Start a game
            if message.author.id in self.games:
                await message.channel.send('You have a game running')
                return
            self.games.add(RedactedGame(message))
            await message.channel.send('Starting Redacted Game')
            return
        
        print(message.channel.id)
        if message.channel.id == 1173819549326524537: # bot stuff channel
            # Play a game
            for game in self.games:
                await game.update(message)
                

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(token)