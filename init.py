
import sys
import os
env = '.env'
print('Initiating PepperChat environment in %s' % env)


DEFAULTS = {
    'LOGDIR': 'logs',
    'AVAILABLE_LANGUAGES': 'norwegian',
    'OPENAI_PROMPTFILE': 'openai.prompt',
    'CHATBOT_SERVER_ADDRESS': 'tcp://localhost:5556'
}

if sys.version_info[0] > 2:
    raw_input = input

if os.path.isfile(env):
    print('%s already exists, exiting.' % env)
else:
    DEFAULTS['OPENAI_KEY'] = raw_input('Specify your OpenAI account key >')

    AVAILABLE_LANGUAGES_NUMBER = raw_input(
        '\n\nPlease select the Robot available languages:\n\n   1: Norwegian \n   2: Norwegian and English \n\n (1 or 2): ')

    if (AVAILABLE_LANGUAGES_NUMBER == 2):
        DEFAULTS['AVAILABLE_LANGUAGES'] = 'norwegian&english'

    with open(env, 'w') as f:
        for key, value in DEFAULTS.items():
            f.write('%s=%s\n' % (key, value))
    print('Done. Default environment stored in %s.' % env)
