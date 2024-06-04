

#!/bin/bash

# List all processes listening on TCP ports and get their PIDs
pids=$(sudo lsof -iTCP -sTCP:LISTEN -n -P | awk 'NR>1 {print $2}')

# Check if there are any PIDs to kill
if [ -z "$pids" ]; then
  echo "No TCP listening processes found."
  exit 0
fi

# Iterate over each PID and kill the process
for pid in $pids; do
  echo "Killing process with PID: $pid"
  sudo kill -9 $pid
done

echo "All TCP listening processes have been killed."


# Make the script executable by running the following command in your terminal:
# chmod +x kill_tcp_listen_processes.sh

#./kill_tcp_listen_processes.sh