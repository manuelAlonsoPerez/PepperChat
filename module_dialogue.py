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
ROBOT_PORT = 9559  # Robot
ROBOT_IP = "pepper.local"  # Pepper default


START_PROMPT = codecs.open(str(os.getenv('DIALOGUE_START_PROMPTFILE'), encoding='utf-8')
                           ).read() if os.path.isfile(str(os.getenv('DIALOGUE_START_PROMPTFILE'))) else None
participantId = raw_input('Participant ID: ')
ANIMATED_SPEECH = int(participantId) % 2 == 1

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
        print("Module_dialogue.py start")
        self.configureSpeechRecognition()
        self.memory = naoqi.ALProxy("ALMemory", self.strNaoIp, ROBOT_PORT)
        self.memory.subscribeToEvent(
            "SpeechRecognition", self.getName(), "processRemote")
        print("INF: ReceiverModule: started!")

        self.tablet = ALProxy('ALTabletService',  self.strNaoIp, ROBOT_PORT)

        try:
            self.posture = ALProxy("ALRobotPosture", self.strNaoIp, ROBOT_PORT)
            if ANIMATED_SPEECH:
                self.aup = ALProxy("ALAnimatedSpeech",
                                   self.strNaoIp, ROBOT_PORT)
            else:
                self.aup = ALProxy("ALTextToSpeech",
                                   self.strNaoIp, ROBOT_PORT)

                languaguesAvailable = self.aup.getAvailableLanguages()
                print("**********************  Available languages: %s" %
                      languaguesAvailable)

                # self.aup.setLanguage('Norwegian')

                languagueInstalled = self.aup.getLanguage()
                print("**********************  Installed language: %s" %
                      languagueInstalled)

                # self.aup.setLanguage("English")

                voices = self.aup.getAvailableVoices()
                print("**********************  Available voices: %s" % voices)

                voice = self.aup.getVoice()
                print("**********************  Voice installed: %s" % voice)

                self.aup.setVoice("naoenu")
                # self.aup.setVoice("naomnc")
                # self.aup.setVoice("nora")

        except RuntimeError:
            print("Can't connect to Naoqi at ip \"" + self.strNaoIp + "\" on port " + str(ROBOT_PORT) + ".\n"
                  "Please check your script arguments. Run with -h option for help.")

        if START_PROMPT:
            # answer = self.encode(chatbot.respond(START_PROMPT))
            answer = chatbot.respond(START_PROMPT)
            self.aup.say(answer)
        self.listen(True)
        print('Listening...')

    def stop(self):
        print("INF: ReceiverModule: stopping...")
        self.memory.unsubscribe(self.getName())
        print("INF: ReceiverModule: stopped!")

    def version(self):
        return "2.0"

    def configureSpeechRecognition(self):
        print("Module_dialogue.py configureSpeechRecognition")
        self.speechRecognition = ALProxy("SpeechRecognition")
        # self.speechRecognition.setLanguage("en-US")

        # self.speechRecognition.calibrate()

        AUTODEC = True
        if (AUTODEC == False):
            print("False, auto-detection not available")
            # one-shot recording for at least 5 seconds
            self.speechRecognition = ALProxy("SpeechRecognition")
            self.speechRecognition.start()
            self.speechRecognition.setHoldTime(5)
            self.speechRecognition.setIdleReleaseTime(1.7)
            self.speechRecognition.setMaxRecordingDuration(10)
            # self.speechRecognition.setLanguage("en-US")
            # self.speechRecognition.setLanguage("no-NO")
            self.speechRecognition.setLanguage("nn-NO")
            # self.speechRecognition.startRecording()
        else:
            print("True, auto-detection selected")
            # auto-detection
            self.speechRecognition = ALProxy("SpeechRecognition")
            # self.speechRecognition.start()
            self.speechRecognition.setHoldTime(3)
            self.speechRecognition.setIdleReleaseTime(2.0)
            self.speechRecognition.setMaxRecordingDuration(15)
            self.speechRecognition.setLookaheadDuration(0.5)
            # self.speechRecognition.setLanguage("en-US")
            # self.speechRecognition.setLanguage("no-NO")
            self.speechRecognition.setLanguage("nn-NO")
            # self.speechRecognition.calibrate()
            self.speechRecognition.setAutoDetectionThreshold(6)
            # self.speechRecognition.startRecording()
        # Ensure that speech recog is off from previous instance.
        self.listen(False)

    def listen(self, enable):
        print("INF: Module_dialogue.py listen")

        if enable:
            self.speechRecognition.start()
            self.speechRecognition.enableAutoDetection()
        else:
            # always disable to not detect its own speech
            self.speechRecognition.disableAutoDetection()
            # and stop if it was already recording another time
            self.speechRecognition.pause()

    def encode(self, s):
        print('****************************** : point  A')

        # s = s.replace(u'å', 'a').replace(u'ä', 'a').replace(u'ö', 'o')
        # s = s.replace(u'ø', 'oe').replace(u'æ', 'a')
        encodedString = codecs.encode(s, 'utf-8')

        print('****************************** : point  B')
        print('****************************** : %s' % encodedString)

        return encodedString
        # return codecs.encode(s, 'ascii', 'ignore')

    def processRemote(self, signalName, message):
        print('****************************** : point  1')
        # message = self.encode(message)
        print('****************************** : point  2')
        # self.log.write('INP: ' + message + '\n')

        if message == 'error':
            print('****************************** : point  3')
            # print('Input not recognized, continue listen')
            return
        self.listen(False)
        print('****************************** : point  4')
        # received speech recognition result
        print("USER: \n" + message)
        print('****************************** : point  5')
        answer = ""

        # computing answer
        if message == 'error':
            print('****************************** : point  6')
            self.misunderstandings += 1
            if self.misunderstandings == 1:
                answer = "I didn't understand, can you repeat?"
            elif self.misunderstandings == 2:
                answer = "Sorry I didn't get it, can you say it one more time?"
            elif self.misunderstandings == 3:
                answer = "Today I'm having troubles uderstanding what you are saying, I'm sorry"
            else:
                answer = "Please repeat that."
            print('****************************** : point  7')
            print('ERROR, DEFAULT ANSWER:\n'+answer)

        else:
            print('****************************** : point  8')
            chatGPTresponse = chatbot.respond(message)
            print('****************************** : point  9')
            answer = chatGPTresponse
            # answer = self.encode(chatGPTresponse)
            print('****************************** : point  10')
            self.misunderstandings = 0
            print('ROBOT:\n'+answer)

        # text to speech the answer

        # self.log.write('ANS: ' + answer + '\n')

        self.tablet.showInputTextDialog(
            "Answer: ", "Ok", "Cancel", answer, 300)

        print('****************************** : point  11')
        self.aup.say(answer)
        print('****************************** : point  12')
        self.react(answer)
        print('****************************** : point  13')
        # time.sleep(2)
        self.listen(True)

    def react(self, s):
        if re.match(".*I.*sit down.*", s):  # Sitting down
            self.posture.goToPosture("Sit", 1.0)
        elif re.match(".*I.*stand up.*", s):  # Standing up
            self.posture.goToPosture("Stand", 1.0)
        elif re.match(".*I.*(lie|lyi).*down.*", s):  # Lying down
            self.posture.goToPosture("LyingBack", 1.0)


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
        p = ALProxy("dialogueModule")
        p.exit()  # kill previous instance
    except:
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