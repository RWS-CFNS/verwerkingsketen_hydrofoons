#include <cstdlib>

int main() {
    system(R"(
mkdir -p ~/Downloads/recordings

# Find all Scarlett capture devices
arecord -l | grep -i scarlett | grep '^card' | while read -r line; do
    card=$(echo "$line" | sed -n 's/^card \([0-9]\+\):.*/\1/p')

    # Check and enable phantom power
    if ! amixer -c "$card" get 'Line In 1 Phantom Power' | grep -q '\\[on\\]'; then
        amixer -c "$card" set 'Line In 1 Phantom Power' toggle
    fi

    # Get high-precision timestamp
    timestamp=$(date +\"%Y-%m-%d_%H-%M-%S_$(date +%%N | cut -c1-3)\")
    filepath=~/Downloads/recordings/rec_${card}_$timestamp.wav

    # Start recording in background
    arecord -D hw:${card},0 -f S32_LE -r 44100 -c 2 -d 10 \"$filepath\" &
done
    )");
    return 0;
}
