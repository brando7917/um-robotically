import discord
import re
import difflib

def censor(text: str) -> str:
    pattern = '\|\|.*?\|\|'
    return re.sub(pattern, '||XXXXX||', text)

class RedactedGame():
    def __init__(self, client: discord.Client, message) -> None:
        self.client = client
        self.author = message.author
        self.text = message.content.replace('[','||').replace(']','||')
        self.plain_text = self.text.replace('||', '')
        self.channel = client.get_partial_messageable(1173828105979318432)
        
    async def update(self, message: discord.Message) -> bool:
        words = message.content.split()
        if message.author.id == self.author.id:
            if words[0].lower() == '!reveal':
                await message.channel.send(self.plain_text)
                return False
            if words[0].lower() == '!end':
                return False
            
        if message.channel.id != self.channel.id:
            return True
        
        if words[0].lower() == '!game':
            await message.channel.send(censor(self.text))
            return True
        
        if message.author.id == self.author.id:
            return True
        
        changes = False
        for word in words:
            to_replace = re.escape(f'||{word}||'.title())
            if re.search(to_replace, self.text, re.IGNORECASE):
                self.text = re.sub(to_replace, word.title(), self.text, flags=re.IGNORECASE)
                changes = True
        if changes:
            await message.channel.send(censor(self.text))
        return '||' in self.text