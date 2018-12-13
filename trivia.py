import discord
import asyncio
import urllib.request
import html
import random
import time
import json
import re

responses = {
    '!answer': {
        'usage': '**{}**, please enter the corresponding letter for your answer to the question.'
    }
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
        
        if tokens[0] not in responses:
            raise InvalidCommandException(None, location)

        # Baseline acceptance criteria
        if len(types) > len(tokens)-1:
            # Command must have at least len(criteria) tokens.
            raise InvalidCommandException(
                responses[tokens[0]]['usage'].format(self.sender.name),
                location)
        
        # Parse into arguments.
        self.args = []
        for index in range(0, len(types)):
            try:
                self.args.append(types[index](tokens[index+1]))
            except:
                raise InvalidCommandException(
                    responses[tokens[0]]['usage'].format(self.sender.name),
                    location)

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
letters = ['a', 'b', 'c', 'd', 'e']
currentQuestion = False
choices = None
botsChannel = None
gambleChannel = None

@asyncio.coroutine
async def sendQuestion():
    global choices
    if choices == None:
        question = json.loads(urllib.request.urlopen('https://opentdb.com/api.php?amount=1&category=18').read().decode('utf-8'))
        choices = [(choice, 0) for choice in question['results'][0]['incorrect_answers']]
        choices.append((question['results'][0]['correct_answer'], 1))
        random.shuffle(choices)
        body = '\n'.join(['({}) {}'.format(letters[i], html.unescape(choices[i][0])) for i in range(len(choices))])
        await send(gambleChannel, '*Trivia time!*')
        await sendRich(gambleChannel, html.unescape(question['results'][0]['question']), body, 0x666666)
    timeDelay = random.randrange(60*60, 60*60*2)
    print('Waiting {} seconds for next trivia question.'.format(timeDelay))
    await asyncio.sleep(timeDelay)
    await sendQuestion()

@client.event
async def on_message(message):
    global choices
    # Ignore messages sent by a bot.
    if message.author.bot:
        return

    if message.content.startswith('!answer'):
        try:
            if choices == None:
                await send(message.channel,
                    'Sorry {}, there\'s no currently unanswered question.'
                    .format(message.author.name))
            else:
                command = Command(message, [str])
                sender = command.sender
                letter = command.args[0]
                if letter not in [letters[i] for i in range(len(choices))]:
                    raise InvalidCommandException(responses['!answer']['usage'].format(sender.name), message.channel)
                index = letters.index(letter)
                if choices[index][1]:
                    # Correct!
                    await send(gambleChannel, random.choice([string.format(message.author.name) for string in [
                        '**{}**, you got it!',
                        '**{}** got it!',
                        'Correct, **{}**!',
                        '**{}** got it!',
                        'Correct, **{}**!',
                        'Right! Well done, **{}**.',
                        'Ding! Good job, **{}**.'
                    ]]))
                    await send(botsChannel, '!reward 200 {}'.format(sender.id))
                    await send(gambleChannel, 'You\'ve been rewarded 200 beans.')
                    choices = None
                else: # Incorrect!
                    await send(gambleChannel, random.choice([
                        'So close!',
                        'Incorrect!',
                        'Wrong!',
                        'Nope!',
                        'Wrong!',
                        'Nope!',
                        'Try again!'
                    ]) + ' -100 beans!')
                    await send(botsChannel, '!request 100 {}'.format(sender.id))
        except InvalidCommandException as e:
            await send(message.channel, e.value)


@client.event
async def on_ready():
    global botsChannel
    global gambleChannel
    print('Logged in!')
    botsChannel = list(client.servers)[0].get_channel('514095418481704972')
    # TODO: Eventually change this to the right channel ID
    gambleChannel = list(client.servers)[0].get_channel('514118083854467092')
    await sendQuestion()
        
client.run(TOKEN)
