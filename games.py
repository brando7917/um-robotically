import discord
import io
import re
import os
from nltk.stem.snowball import SnowballStemmer
from PIL import Image

snow_stemmer = SnowballStemmer(language='english')

def censor(text: str) -> str:
    pattern = '\|\|.*?\|\|'
    censored = re.sub(pattern, '||XXX||', text)
    if len(censored) >= 2000:
        censored = re.sub(pattern, '||XX||', text)
    if len(censored) >= 2000:
        censored = re.sub(pattern, '||X||', text)
    return censored

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
        if message.content.startswith('!redactall'):
            messageContent = re.sub(r"([\w']+)", r'||\1||', messageContent)
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
        
        # Parse the !game command only in a DM or the game
        if (words[0] == '!game' and
            (
                (isinstance(message.channel, discord.DMChannel) and message.author.id == self.author.id)
                or message.channel.id == self.channel.id
            )):
            await message.channel.send(censor(self.text))
            return True
        
        # Don't process messages outside the game channel
        if message.channel.id != self.channel.id:
            return True
        
        # Let the game creator or mod end the game
        if message.author.id == self.author.id or any(role.id == 1173817341876903956 for role in message.author.roles):
            if words[0] == '!reveal':
                await message.channel.send(self.plain_text)
                return False
            if words[0] == '!end':
                await message.channel.send('Game Canceled')
                return False
        
        # Don't process words by the game creator
        if message.author.id == self.author.id:
            return True
        
        to_remove = set()
        for word in words:
            for token in self.tokens:
                if snow_stemmer.stem(re.sub('\W', '', word)) == snow_stemmer.stem(re.sub('\W', '', token)):
                    self.text = self.text.replace(f'||{token}||', token)
                    to_remove.add(token)
                if re.sub('\W', '', token).lower().endswith('in'):
                    if snow_stemmer.stem(re.sub('\W', '', word)) == snow_stemmer.stem(re.sub('\W', '', token+'g')):
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
        self.resize_values = None
        words = message.content.split()
        if len(words) == 2:
            self.round_count = int(words[1])
        else:
            self.round_count = 10
    
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
                self.image_file.seek(0)
                img = Image.open(self.image_file)
                # Calculate the resize values on the first round
                if not self.resize_values:
                    if img.width < img.height:
                        total_mult_factor = img.width / 5 # Start with 5 boxes
                        individual_mult_factor = pow(total_mult_factor, 1 / (self.round_count - 1))
                        self.resize_values = [(int(5 * pow(individual_mult_factor, i)), int((5 * pow(individual_mult_factor, i) * img.height) // img.width)) for i in range(self.round_count)]
                    else:
                        total_mult_factor = img.height / 5 # Start with 5 boxes
                        individual_mult_factor = pow(total_mult_factor, 1 / (self.round_count - 1))
                        self.resize_values = [(int((5 * pow(individual_mult_factor, i) * img.width) // img.height), int(5 * pow(individual_mult_factor, i))) for i in range(self.round_count)]
                    self.current_round = 1    
                if self.current_round <= self.round_count:
                    pixelfactor = self.resize_values[self.current_round - 1]
                    imgSmall = img.resize(pixelfactor, resample=Image.Resampling.BILINEAR)
                    imgBig = imgSmall.resize(img.size, Image.Resampling.NEAREST)
                    newImg = io.BytesIO()
                    imgBig.save(newImg, self.filetype[1:])
                    newImg.seek(0)
                    await message.channel.send(f'Round {self.current_round}/{self.round_count}', file=discord.File(newImg, filename="nmp"+self.filetype))
                    self.current_round += 1
                    return True
                self.image_file.seek(0)
                await message.channel.send(file=discord.File(self.image_file, filename="nmp"+self.filetype))
                return False
            
        return True
            
            
    async def update_reaction(self, reaction_event: discord.RawReactionActionEvent) -> bool:
        return True # No-op on reactions