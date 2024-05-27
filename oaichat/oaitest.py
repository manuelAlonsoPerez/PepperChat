
from openaichat import OaiChat

chat = OaiChat(('Your name is Pepper.',
               'We are currently at the TechEdge studio at Sopra Steria. In Oslo, Norway.', 'You are a robot.'))

while True:
    s = input('> ')
    if s:
        print(chat.history)
        print(chat.respond(s).getText())
    else:
        break
