#!/bin/bash

# Enter the folder, activate python3 virtual env, and run the python command
cd ..
source venv3/bin/activate
cd PepperChat
python3 startDialogueServer.py &

# Open a new terminal, enter the folder, activate python2 virtual env, and run the second python command
gnome-terminal -- bash -c "
cd ..
source venv/bin/activate 
cd PepperChat
python module_speechrecognition.py --pip 192.168.103.103
exec bash
"

# Open a new terminal, enter the folder and run the third python command

gnome-terminal -- bash -c "
cd ..
source venv/bin/activate
cd PepperChat
python module_dialogue.py --pip 192.168.103.103
exec bash
"


# make the script executable
# chmod +x run_pepper.sh

# execute the script by running
# ./run_pepper.sh