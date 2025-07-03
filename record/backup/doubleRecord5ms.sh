#!/bin/bash

mkdir -p ~/Downloads/recordings

record_with_timestamp() {
    local card=$1
    local filepath=~/Downloads/recordings/rec_card${card}_$(date +%Y-%m-%d_%H-%M-%S).wav

    echo "[Card $card] Starting recording..."
    arecord -D hw:${card},0 -f S32_LE -r 44100 -c 2 -d 5 "$filepath"
    end_time=$(date +%s.%N)
    echo "[Card $card] Finished recording at $end_time"
    mv "$filepath" ~/Downloads/recordings/rec_card${card}_$end_time.wav
}

pids=()

# Run while-loop in current shell using process substitution
while read -r line; do
    card=$(echo "$line" | sed -n 's/^card \([0-9]\+\):.*/\1/p')
    echo "Found Scarlett device on card $card"

    status=$(amixer -c "$card" get 'Line In 1 Phantom Power' | grep -o '\[on\]\|\[off\]')
    echo "Phantom power status: $status"

    if [[ "$status" == "[off]" ]]; then
        amixer -c "$card" set 'Line In 1 Phantom Power' toggle
    fi

    record_with_timestamp "$card" &
    pids+=($!)
done < <(arecord -l | grep -i scarlett | grep '^card')

# Wait for all background processes
echo "Waiting for recordings to finish..."
for pid in "${pids[@]}"; do
    wait $pid
done
echo "All recordings complete."

# Ideas for synchronization:
# Plan execution via cron or threads
# Disect arecord function
# Check when the recording is done
# Check card function, switch card order
# Split phantom power and recording processes
# Use arecord with --max-file-time and --use-strftime
# Test sound card recording time delays