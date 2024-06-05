# -*- coding: utf-8 -*-

###########################################################
# Retrieve robot audio buffer and do google speech recognition
#
# Syntax:
#    python scriptname --pip <ip> --pport <port>
#
#    --pip <ip>: specify the ip of your robot (without specification it will use the ROBOT_IP defined below)
#
# Author: Johannes Bramauer, Vienna University of Technology and Erik Billing, University of Skovde
# Created: May 30, 2018 and updated spring 2022.
# License: MIT
###########################################################
###########################################################

import time
import sys
from pepperspeechrecognition import SpeechRecognitionModule
from optparse import OptionParser
import naoqi
from naoqi import ALProxy
ROBOT_IP = "pepper.local"  # default, for running on Pepper
ROBOT_PORT = 9559


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
        # kill previous instance, useful for developing ;)
        print('Speech recognition debugging. # kill previous instance')

        speechRecognitionProxy = ALProxy("SpeechRecognition")
        speechRecognitionProxy.exit()

        alMemoryProxy = ALProxy("ALMemory")
        alMemoryProxy.exit()

    except Exception as error:
        print(
            'Speech recognition debugging. # Failed killing previous instance. %s' % error)
        pass

    # Reinstantiate module

    # Warning: SpeechRecognition must be a global variable
    # The name given to the constructor must be the name of the
    # variable
    global SpeechRecognition
    SpeechRecognition = SpeechRecognitionModule(
        "SpeechRecognition", pip, pport)

    # uncomment for debug purposes
    # usually a subscribing client will call start() from ALProxy
    print('# Speech recognition debugging.pip:%s  port:%s' %
          (str(pip), str(pport)))

    # SpeechRecognition.start()
    # SpeechRecognition.startRecording()
    # SpeechRecognition.calibrate()
    # SpeechRecognition.enableAutoDetection()
    # SpeechRecognition.startRecording()

    print('Speech recognition running.')

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print
        print("\n\n -----------  Interrupted by user, shutting down  ---------- \n\n")
        myBroker.shutdown()
        sys.exit(0)


if __name__ == "__main__":
    main()
