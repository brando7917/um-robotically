import discord
import io
import re
import os
from nltk.stem.snowball import SnowballStemmer
from PIL import Image

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
        if message.attachments:
            self.image_embed = discord.Embed().set_image(url=message.attachments[0].url)
        else:
            self.image_embed = None
    
    async def update_message(self, message: discord.Message) -> bool:
        if message.channel.id != self.channel.id:
            return True
        
        if message.content.startswith('!game'):
            await message.channel.send(self.status(), embed=self.image_embed)
            return True
        
        if (message.author.id == self.author.id or any(role.id == 1173817341876903956 for role in message.author.roles)):
            if message.content.startswith('!end'):
                await message.channel.send('Ending Twenty Questions')
                return False
            if message.content.startswith('!delete'):
                await message.channel.send(f'Deleted {self.questions.pop()}')
                return True
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
        messageContent = message.content[message.content.find('\n')+1:]
        
        if message.content.startswith('!manualredact'): #manual censoring
            pass
        else: #auto censoring
            newContent = ''
            for line in messageContent.split('\n'):
                colonIndex = line.find(':')+1
                if colonIndex != -1:
                    prefix = line[:colonIndex]
                    body = line[colonIndex:]
                    if prefix and prefix != 'Hint:':
                        body = re.sub(r"([\w']+)", r'||\1||', body)
                    newContent += prefix + body + '\n'
                else:
                    newContent += line + '\n'
            messageContent = newContent
        
        self.text = messageContent.replace('[','||').replace(']','||').replace('||||','')
        self.plain_text = self.text.replace('||', '')
        self.tokens = set(re.findall('\|\|(.*?)\|\|', self.text))
        
        
        self.channel = client.get_partial_messageable(1173828105979318432)
        
    async def update_message(self, message: discord.Message) -> bool:
        words = message.content.replace(',','').lower().split()
        if len(words) == 0:
            return True
        if message.author.id == self.author.id or any(role.id == 1173817341876903956 for role in message.author.roles):
            if words[0] == '!reveal':
                await message.channel.send(self.plain_text)
                return False
            if words[0] == '!end':
                await message.channel.send('Game Canceled')
                return False
        
        if words[0] == '!game' and isinstance(message.channel, discord.DMChannel) and message.author.id == self.author.id:
            await message.channel.send(censor(self.text))
            return True
            
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
                if snow_stemmer.stem(re.sub('\W', '', word)) == snow_stemmer.stem(re.sub('\W', '', token)):
                    self.text = self.text.replace(f'||{token}||', token)
                    to_remove.add(token)
        self.tokens = self.tokens.difference(to_remove)
        if to_remove:
            await message.channel.send(censor(self.text))
        if '||' in self.text:
            return True
        else:
            await message.channel.send('Congratulations!')
            return False
    
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> bool:
        return True # No-op on reactions

class NeedsMorePixelsGame():
    def __init__(self, client: discord.Client, message: discord.Message) -> None:
        self.client = client
        self.author = message.author
        self.channel = client.get_partial_messageable(1173827731079827586) # NMP channel
        self.image_file = io.BytesIO()
        self.filetype = os.path.splitext(message.attachments[0].filename)[-1]
        if self.filetype.lower() == ".jpg":
            self.filetype = ".jpeg"
        words = message.content.split()
        self.levels = [1000, 500, 250, 100, 50, 30, 20, 10, 5, 1]
        self.level = 1 if len(words) < 2 else (len(self.levels) - int(words[-1]) - 1)
    
    async def set_image(self, attachment: discord.Attachment) -> None:
        await attachment.save(self.image_file)
        
    async def update_message(self, message: discord.Message) -> bool:
        words = message.content.replace(',','').lower().split()
        if message.channel.id != self.channel.id:
            return True
        
        if message.author.id == self.author.id or any(role.id == 1173817341876903956 for role in message.author.roles):
            if words[0] == '!reveal':
                self.image_file.seek(0)
                await message.channel.send(file=discord.File(self.image_file, filename="nmp"+self.filetype))
                return False
            if words[0] == '!end':
                await message.channel.send('Game Canceled')
                return False
            if words[0] == '!next':
                self.level += 1
                self.image_file.seek(0)
                img = Image.open(self.image_file)
                if self.level > 1:
                    pixelfactor = self.levels[self.level]
                    imgSmall = img.resize((img.width//pixelfactor, img.height//pixelfactor), resample=Image.Resampling.BILINEAR)
                    imgBig = imgSmall.resize(img.size, Image.Resampling.NEAREST)
                    newImg = io.BytesIO()
                    imgBig.save(newImg, self.filetype[1:])
                    newImg.seek(0)
                    await message.channel.send(f'Round {self.level+1}/{len(self.levels)}', file=discord.File(newImg, filename="nmp"+self.filetype))
                    return True
                self.image_file.seek(0)
                await message.channel.send(file=discord.File(self.image_file, filename="nmp"+self.filetype))
                return False
            
        return True
            
            
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> bool:
        return True # No-op on reactions