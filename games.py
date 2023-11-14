class RedactedGame():
    def __init__(self, message) -> None:
        self.author = message.author
        self.text = message.content
        
    async def update(self, message) -> str:
        words = message.content.split()
        print(words)
        print(self.text)
        changes = False
        for word in words:
            to_replace = f'[{word}]'
            if to_replace in self.text:
                self.text = self.text.replace(to_replace, word)
                changes = True
        if changes:
            await message.channel.send(self.text)