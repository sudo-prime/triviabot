import discord
import threading
import urllib.request
import html
import random
import time
import json
import re

responses = {
    
}

class InvalidCommandException(Exception):
    def __init__(self, value, loc=''):
        self.value = value
        self.loc = loc
    def __str__(self):
        return repr(self.value)

class Command:
    def __init__(self, message, types, loc=''):
        self.sender = message.author
        location = message.channel if loc == '' else loc

        # Parse the message for tokens.
        tokens = message.content.split(' ')

        # Baseline acceptance criteria
        if len(types) > len(tokens)-1:
            # Command must have at least len(criteria) tokens.
            raise InvalidCommandException(responses[tokens[0]]['usage'].format(self.sender.name), location)
        
        # Parse into arguments.
        self.args = []
        for index in range(0, len(types)):
            try:
                self.args.append(types[index](tokens[index+1]))
            except:
                raise InvalidCommandException(responses[tokens[0]]['usage'].format(self.sender.name), location)

async def send(location, message):
    global client
    await client.send_message(location, message)

async def sendRich(location, title, message, color=0x22dd22):
    global client
    embed = discord.Embed(title=title, description=message, color=color)
    await client.send_message(location, embed=embed)

async def verifyValidUser(mention):
    global client
    try:
        await client.get_user_info(usrid(mention))
        return True
    except:
        return False

def usrid(mention):
    userID = re.sub('<|>|@|!', '', str(mention))
    return userID

with open('../TOKEN') as tokenFile:
    TOKEN = tokenFile.readline()

client = discord.Client()
currentQuestion = False
question = ''
botsChannel = ''
gambleChannel = ''

async def sendQuestion():
    global currentQuestion
    global botsChannel
    global gambleChannel
    if not currentQuestion:
        currentQuestion = True
        question = json.loads(urllib.request.urlopen('https://opentdb.com/api.php?amount=1').read().decode('utf-8'))
        choices = question['results'][0]['incorrect_answers']
        choices.append(question['results'][0]['correct_answer'])
        random.shuffle(choices)
        letters = ['a', 'b', 'c', 'd']
        body = '\n'.join(['({}) {}'.format(letters[i], html.unescape(choices[i])) for i in range(len(choices))])
        await send(gambleChannel, '*Trivia time!*')
        await sendRich(gambleChannel, html.unescape(question['results'][0]['question']), body, 0x666666)
    timeDelay = random.randrange(60*15, 60*60*2)
    print('Waiting {} seconds for next trivia question.'.format(timeDelay))
    threading.Timer(timeDelay, sendQuestion).start()

@client.event
async def on_message(message):
    # Ignore messages sent by a bot.
    if message.author.bot:
        return
    
    # DEBUG
    print(str(message.content))

    if message.content.startswith('!answer'):
        pass

@client.event
async def on_ready():
    global botsChannel
    global gambleChannel
    print('Logged in!')
    botsChannel = list(client.servers)[0].get_channel('514095418481704972')
    # TODO: Eventually change this to the right channel ID
    gambleChannel = list(client.servers)[0].get_channel('514095418481704972')
    await sendQuestion()
        
client.run(TOKEN)