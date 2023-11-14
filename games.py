import discord
import re

def censor(text: str) -> str:
    pattern = '\|\|.*?\|\|'
    return re.sub(pattern, '||XXXXX||', text)

class RedactedGame():
    def __init__(self, client: discord.Client, message) -> None:
        self.client = client
        self.author = message.author
        self.text = message.content.replace('[','||').replace(']','||')
        self.channel = client.get_partial_messageable(1173828105979318432)
        
    async def update(self, message: discord.Message) -> bool:
        if message.channel.id != self.channel.id:
            return True
        
        words = message.content.split()
        if words[0].lower() == '!game':
            await message.channel.send(censor(self.text))
            return True
        
        if message.author.id == self.author.id:
            return words[0].lower() != '!end'
        
        changes = False
        for word in words:
            to_replace = re.escape(f'||{word}||'.title())
            if re.search(to_replace, self.text, re.IGNORECASE):
               self.text = re.sub(to_replace, word.title(), self.text, flags=re.IGNORECASE)
               changes = True
        if changes:
            await message.channel.send(censor(self.text))
        return '||' in self.text