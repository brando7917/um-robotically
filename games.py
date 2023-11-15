import discord
import re
from nltk.stem.snowball import SnowballStemmer

snow_stemmer = SnowballStemmer(language='english')

def censor(text: str) -> str:
    pattern = '\|\|.*?\|\|'
    return re.sub(pattern, '||XXXXX||', text)

class RedactedGame():
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        self.client = client
        self.author = message.author
        self.text = message.content.replace('[','||').replace(']','||')
        self.plain_text = self.text.replace('||', '')
        self.tokens = re.findall('\|\|(.*?)\|\|', self.text)
        self.channel = client.get_partial_messageable(1173828105979318432)
        
    async def update(self, message: discord.Message) -> bool:
        words = message.content.replace(',','').lower().split()
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
        
        changes = False
        for word in words:
            for token in self.tokens:
                if snow_stemmer.stem(word) == snow_stemmer.stem(token):
                    self.text = self.text.replace(f'||{token}||', token)
                    changes = True
        if changes:
            await message.channel.send(censor(self.text))
        return '||' in self.text