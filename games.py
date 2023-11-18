import discord
import re
from nltk.stem.snowball import SnowballStemmer

snow_stemmer = SnowballStemmer(language='english')

def censor(text: str) -> str:
    pattern = '\|\|.*?\|\|'
    return re.sub(pattern, '||XXX||', text)

class TwentyQuestionsGame():
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        self.client = client
        self.author = message.author
        self.channel = message.channel
        self.questions = []
        self.reacts = ['✅', '❌', '❓', '⚔️']
        self.custom_reacts = ['fifty']
        self.win_reacts = ['👑']
    
    async def update_message(self, message: discord.Message) -> bool:
        if message.channel.id != self.channel.id:
            return True
        
        if message.content.startswith('!game'):
            await message.channel.send(self.status())
            return True
        
        if message.content.startswith('!end'):
            await message.channel.send('Ending Twenty Questions')
            return False
        return True
    
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> bool:
        if reaction_event.user_id != self.author.id:
            return True
        if reaction_event.channel_id != self.channel.id:
            return True
        message = await self.channel.fetch_message(reaction_event.message_id)
        if reaction_event.emoji.name in self.custom_reacts:
            self.questions.append(f'{message.content} <:{reaction_event.emoji.name}:{reaction_event.emoji.id}>')
            await self.channel.send(f'{len(self.questions)} Question(s) Asked')
            return True
        if reaction_event.emoji.name in self.reacts:
            self.questions.append(f'{message.content} {reaction_event.emoji.name}')
            await self.channel.send(f'{len(self.questions)} Question(s) Asked')
            return True
        if reaction_event.emoji.name in self.win_reacts:
            await self.channel.send(f'Congrats! You found the answer in {len(self.questions)} questions.')
            return False
        return True
            
    def status(self) -> str:
        return 'Twenty Questions:\n' + '\n'.join(self.questions)
            

class RedactedGame():
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        self.client = client
        self.author = message.author
        self.text = message.content.replace('[','||').replace(']','||')
        self.plain_text = self.text.replace('||', '')
        self.tokens = set(re.findall('\|\|(.*?)\|\|', self.text))
        self.channel = client.get_partial_messageable(1173828105979318432)
        
    async def update_message(self, message: discord.Message) -> bool:
        words = message.content.replace(',','').lower().split()
        if len(words) == 0:
            return True
        if message.author.id == self.author.id:
            if words[0] == '!reveal':
                await message.channel.send(self.plain_text)
                return False
            if words[0] == '!end':
                await message.channel.send('Game Canceled')
                return False
            
        if message.channel.id != self.channel.id:
            return True
        
        if words[0] == '!game':
            await message.channel.send(censor(self.text))
            return True
        
        if message.author.id == self.author.id:
            return True
        
        to_remove = set()
        for word in words:
            for token in self.tokens:
                if snow_stemmer.stem(word) == snow_stemmer.stem(token):
                    self.text = self.text.replace(f'||{token}||', token)
                    to_remove.add(token)
        self.tokens = self.tokens.difference(to_remove)
        if to_remove:
            await message.channel.send(censor(self.text))
        return '||' in self.text
    
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> bool:
        return True # No-op on reactions