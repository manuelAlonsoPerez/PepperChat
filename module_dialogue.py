# -*- coding: utf-8 -*-

###########################################################
# This module implements the main dialogue functionality for Pepper, based on ChatGPT.
#
# Syntax:
#    python scriptname --pip <ip> --pport <port>
#
#    --pip <ip>: specify the ip of your robot (without specification it will use the ROBOT_IP defined below
#
# Author: Erik Billing, University of Skovde based on code from Johannes Bramauer, Vienna University of Technology
# Created: May 30, 2018 and updated spring progressively during in the period 2022-05 to 2024-04.
# License: MIT
###########################################################

import os
import sys
from oaichat.oaiclient import OaiClient
from naoqi import ALProxy
import codecs
import time
import naoqi
import re
from optparse import OptionParser
import langid

ROBOT_PORT = 9559  # Robot
ROBOT_IP = "pepper.local"  # Pepper default

# NAOqi API “Sensitivity” Parameter, between 0 and 1 to adjust the detection threshold. At 0, the robot does not detect any sound.
# At 1, it reacts to the slightest sound.

MICROPHONE_SENSITIVITY = 0.05

START_PROMPT = codecs.open(str(os.getenv('DIALOGUE_START_PROMPTFILE'), encoding='utf-8')
                           ).read() if os.path.isfile(str(os.getenv('DIALOGUE_START_PROMPTFILE'))) else None
# participantId = raw_input('Participant ID: ')
# ALIVE = int(participantId) % 2 == 1

# ALAnimatedSpeech say method does not have the option to set up the language,
# In case we want to Show the ALAnimatedSpeech remove the functionality of handling 
# several languagues dinamically

participantId = 1
ALIVE = False

chatbot = OaiClient(user=participantId)
chatbot.reset()


class DialogueModule(naoqi.ALModule):
    """
    Main dialogue module. Depends on both the ChatGPT service and the Speech Recognion module.
    """

    def __init__(self, strModuleName, strNaoIp):
        self.misunderstandings = 0

        # self.log = codecs.open('dialogue.log', 'a', encoding='utf-8')

        try:
            naoqi.ALModule.__init__(self, strModuleName)
            self.BIND_PYTHON(self.getName(), "callback")
            self.strNaoIp = strNaoIp
            # self.session = qi.Session()
        except BaseException, err:
            print("ERR: ReceiverModule: loading error: %s" % str(err))

    def __del__(self):
        print("INF: ReceiverModule.__del__: cleaning everything")
        self.stop()

    def start(self):
        self.configureSpeechRecognition()

        self.memory = naoqi.ALProxy("ALMemory", self.strNaoIp, ROBOT_PORT)
        self.memory.subscribeToEvent(
            "SpeechRecognition", self.getName(), "processRemote")
        print("INF: ReceiverModule: started!")

        self.tablet = ALProxy('ALTabletService',  self.strNaoIp, ROBOT_PORT)

        # Reducing Microphone sensitivity to reduce capturing background noise
        self.soundDetection = ALProxy(
            "ALSoundDetection",  self.strNaoIp, ROBOT_PORT)
        self.soundDetection.setParameter("Sensitivity", MICROPHONE_SENSITIVITY)
        print("INF: Microphone sensitivity set to %f" % MICROPHONE_SENSITIVITY)

        # Robot preferences Proxy for changing the language
        self.robotPereferences = ALProxy(
            'ALPreferenceManager',  self.strNaoIp, ROBOT_PORT)

        try:
            self.posture = ALProxy("ALRobotPosture", self.strNaoIp, ROBOT_PORT)

            # Participant Id is an Odd number
            if ALIVE:
                self.aup = ALProxy("ALAnimatedSpeech",
                                   self.strNaoIp, ROBOT_PORT)

            # Participant Id is an even number
            else:
                self.aup = ALProxy("ALTextToSpeech",
                                   self.strNaoIp, ROBOT_PORT)

                languaguesAvailable = self.aup.getAvailableLanguages()
                print("INF: Available languages: %s" %
                      languaguesAvailable)

                # self.aup.setLanguage('English')

                languagueInstalled = self.aup.getLanguage()

                print("INF: Installed language: %s" %
                      languagueInstalled)

                voices = self.aup.getAvailableVoices()
                print("INF: Available voices: %s" % voices)

                # self.aup.setVoice("naoenu")
                # self.aup.setVoice("naomnc")
                self.aup.setVoice("nora")

                voice = self.aup.getVoice()
                print("INF: Voice installed: %s" % voice)

        except RuntimeError:
            print("ERR: Can't connect to Naoqi at ip \"" + self.strNaoIp + "\" on port " + str(ROBOT_PORT) + ".\n"
                  "Please check your script arguments. Run with -h option for help.")

        if START_PROMPT:
            # answer = self.encode(chatbot.respond(START_PROMPT))
            answer = chatbot.respond(START_PROMPT)
            self.aup.say(answer, languagueInstalled)

        self.listen(True)
        print('INF: Listening...')

    def stop(self):
        print("INF: ReceiverModule: stopping...")
        self.memory.unsubscribe(self.getName())
        print("INF: ReceiverModule: stopped!")

    def version(self):
        return "2.0"

    def configureSpeechRecognition(self):
        self.speechRecognition = ALProxy("SpeechRecognition")

        AUTODEC = True
        if (AUTODEC == False):
            print("INF: AUTODEC is False, auto-detection not available")
            # one-shot recording for at least 5 seconds
            self.speechRecognition = ALProxy("SpeechRecognition")
            self.speechRecognition.start()

            self.speechRecognition.setHoldTime(5)
            self.speechRecognition.setIdleReleaseTime(1.7)
            self.speechRecognition.setMaxRecordingDuration(10)
            # self.speechRecognition.setLanguage("en-US")
            # self.speechRecognition.startRecording()
        else:
            print("INF: AUTODEC is True, auto-detection selected")
            # auto-detection
            self.speechRecognition = ALProxy("SpeechRecognition")
            # self.speechRecognition.start()

            self.speechRecognition.setHoldTime(3)
            self.speechRecognition.setIdleReleaseTime(2.0)
            self.speechRecognition.setMaxRecordingDuration(15)
            self.speechRecognition.setLookaheadDuration(0.5)
            # self.speechRecognition.setLanguage("en-US")
            # self.speechRecognition.calibrate()
            self.speechRecognition.setAutoDetectionThreshold(6)
            # self.speechRecognition.startRecording()
        # Ensure that speech recog is off from previous instance.
        self.listen(False)

    def listen(self, enable):

        if enable:
            self.speechRecognition.start()
            self.speechRecognition.enableAutoDetection()
        else:
            # always disable to not detect its own speech
            self.speechRecognition.disableAutoDetection()
            # and stop if it was already recording another time
            self.speechRecognition.pause()

    def encode(self, s):
        encodedString = codecs.encode(s, 'utf-8')

        return encodedString

    def processRemote(self, signalName, message):
        # message = self.encode(message)
        # self.log.write('INP: ' + message + '\n')

        if message == 'error':
            print('ERR: Input not recognized, continue listen')
            return
        self.listen(False)

        # received speech recognition result
        print("\nUSER QUESTION: " + message + '.\n')

        languageToAnswer = self.indentifyLanguage(message)

        answer = ""

        # computing answer
        if message == 'error':
            self.misunderstandings += 1

            if self.misunderstandings == 1:
                answer = "I didn't understand, can you repeat?"
            elif self.misunderstandings == 2:
                answer = "Sorry I didn't get it, can you say it one more time?"
            elif self.misunderstandings == 3:
                answer = "Today I'm having troubles uderstanding what you are saying, I'm sorry"
            else:
                answer = "Please repeat that."

            print('ERR: DEFAULT ANSWER:\n'+answer)

        else:
            chatGPTresponse = chatbot.respond(message)
            # answer = chatGPTresponse

            answer = self.encode(chatGPTresponse)

            self.misunderstandings = 0

            print('\nROBOT ANSWER:' + answer + '\n')

        # text to speech the answer
        # self.log.write('ANS: ' + answer + '\n')

        # self.tablet.showInputTextDialog(
          #  "Answer: ", "Ok", "Cancel", answer, 300)

        if ALIVE:
            configuration = {"language": languageToAnswer}
            self.aup.say(answer, configuration)
        else:
            self.aup.say(answer, languageToAnswer)

        self.react(answer)
        # time.sleep(2)
        self.listen(True)

    def react(self, s):
        if re.match(".*I.*sit down.*", s):  # Sitting down
            self.posture.goToPosture("Sit", 1.0)
        elif re.match(".*I.*stand up.*", s):  # Standing up
            self.posture.goToPosture("Stand", 1.0)
        elif re.match(".*I.*(lie|lyi).*down.*", s):  # Lying down
            self.posture.goToPosture("LyingBack", 1.0)

    def indentifyLanguage(self, text):
        clasiffyResult = langid.classify(text)
        textLanguage = clasiffyResult[0]

        robotLanguage = 'Norwegian'

        if textLanguage == "en":
            robotLanguage = 'English'
        
        print('INF: The language of the question was "%s",  robot language to answer is %s' % (textLanguage, robotLanguage))

        return robotLanguage

    def getRobotPreferences(self, language):

        # Uncomment to debug prefferences sat on the Robot
        # Getting Robot preferences

        preferenceDomains = self.robotPereferences.getDomainList()
        print('\n\INF: Robot preference Domains:')
        
        #printing the list using loop
        for x in range(len(preferenceDomains)):
            print(preferenceDomains[x] + ' ,')

        webPreferences = self.robotPereferences.getValueList(
            'com.aldebaran.robotwebpage')

        if (len(webPreferences) <= 0):
            return
        else:
            print('\n\INF: Robot web page preferences')
            for x in range(len(webPreferences)):
                for y in range(len(webPreferences[x])):
                    print(webPreferences[y])

        wizardPreferences = self.robotPereferences.getValueList(
            'com.aldebaran.wizard')

        if (len(wizardPreferences) <= 0):
            return
        else:
            print('\n\INF: Robot wizard preferences')
            for x in range(len(wizardPreferences)):
                for y in range(len(wizardPreferences[x]) - 1):
                    print(wizardPreferences[y])


def main():
    """ Main entry point
    """

    parser = OptionParser()
    parser.add_option("--pip",
                      help="Parent broker port. The IP address or your robot",
                      dest="pip")
    parser.add_option("--pport",
                      help="Parent broker port. The port NAOqi is listening to",
                      dest="pport",
                      type="int")
    parser.set_defaults(
        pip=ROBOT_IP,
        pport=ROBOT_PORT)

    (opts, args_) = parser.parse_args()
    pip = opts.pip
    pport = opts.pport

    # We need this broker to be able to construct
    # NAOqi modules and subscribe to other modules
    # The broker must stay alive until the program exists
    myBroker = naoqi.ALBroker("myBroker",
                              "0.0.0.0",   # listen to anyone
                              0,           # find a free port and use it
                              pip,         # parent broker IP
                              pport)       # parent broker port

    try:
        print('Module Dialoge debugging. # kill previous instance')
        p = ALProxy("dialogueModule")
        p.exit()  # kill previous instance

    except Exception as error:
        print(
            'Module Dialoge debugging. # Failed killing previous instance. %s' % error)
        pass

    audio = ALProxy("ALAudioDevice")
    audio.setOutputVolume(70)

    """ AutonomousLife = ALProxy('ALAutonomousLife')
    RobotPosture = ALProxy('ALRobotPosture')
    if ANIMATED_SPEECH:
        AutonomousLife.setState('solitary')
        AutonomousLife.stopAll()
        AutonomousLife.switchFocus('julia-8b4016/behavior_1')
        print('Odd participant number, autonomous life enabled.')
    else:
        if AutonomousLife.getState() != 'disabled':
            AutonomousLife.setState('disabled')
        RobotPosture.goToPosture('Stand',0.5)
        print('Even participant number, autonomous life disabled.') """

    # TabletService = ALProxy('ALTabletService')
    # TabletService.goToSleep()

    # Reinstantiate module

    # Warning: ReceiverModule must be a global variable
    # The name given to the constructor must be the name of the
    # variable
    global dialogueModule
    dialogueModule = DialogueModule("dialogueModule", pip)
    dialogueModule.start()

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print
        print("Interrupted by user, shutting down")
        myBroker.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()
