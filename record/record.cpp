#include <alsa/asoundlib.h>
#include <chrono>
#include <fstream>
#include <iostream>
#include <thread>
#include <vector>
#include <atomic>
#include <cstring>
#include <sstream>
#include <filesystem>
#include <random>
#include <cstdio>
#include <memory>
#include <array>
#include <wiringPi.h>

#define TRANSISTOR_GPIO 26
#define TRIGGER_GPIO 12

using namespace std;
using namespace std::chrono;
namespace fs = filesystem;

// Accessed by different threads
std::atomic<int> id(0);
std::atomic<bool> start_recording_flag(false);
std::atomic<long long> pulse_time(0);
std::atomic<long long> trigger_count(0);

// Configuration for each recording thread
struct RecorderConfig {
    int card;
    std::string file_location;
    std::string recording_id;
    std::string random_uuid;
    int sample_rate;
    double duration;
    std::string mode;
    bool isMaster;
};

// Execute bash and get print output as return value
std::string exec(const char* cmd) {
    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd, "r"), pclose);
    if (!pipe) return "ERROR";
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr)
        result += buffer.data();
    return result;
}

// Generate random 32-character hexadecimal string
std::string generate_uuid() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<int> dist(0, 15);
    std::stringstream ss;
    for (int i = 0; i < 32; ++i) ss << std::hex << dist(gen);
    return ss.str();
}

// Read audio device, write to wav file, set filename with timestamp
void record_audio(const RecorderConfig& config) {
    // Prepare config structures
    snd_pcm_t* pcm_handle;
    snd_pcm_hw_params_t* params;
    snd_pcm_uframes_t frames = 1024;
    int rc;
    unsigned int rate = config.sample_rate;
    int channels = 2;

    // Set device to read from
    std::string cardname = "hw:" + std::to_string(config.card) + ",0";
    rc = snd_pcm_open(&pcm_handle, cardname.c_str(), SND_PCM_STREAM_CAPTURE, 0);
    if (rc < 0) {
        std::cerr << "Unable to open device " << cardname << ": " << snd_strerror(rc) << std::endl;
        return;
    }

    // Create configurations 
    snd_pcm_hw_params_alloca(&params);
    snd_pcm_hw_params_any(pcm_handle, params);
    snd_pcm_hw_params_set_access(pcm_handle, params, SND_PCM_ACCESS_RW_INTERLEAVED);
    snd_pcm_hw_params_set_format(pcm_handle, params, SND_PCM_FORMAT_S32_LE);
    snd_pcm_hw_params_set_channels(pcm_handle, params, channels);
    snd_pcm_hw_params_set_rate_near(pcm_handle, params, &rate, 0);
    snd_pcm_hw_params_set_period_size_near(pcm_handle, params, &frames, 0);

    // Add configurations
    rc = snd_pcm_hw_params(pcm_handle, params);
    if (rc < 0) {
        std::cerr << "Unable to set hw parameters: " << snd_strerror(rc) << std::endl;
        return;
    }

    // Define recording characteristics
    int frame_bytes = channels * sizeof(int32_t);
    int buffer_size = frames * frame_bytes;
    char* buffer = new char[buffer_size];

    // Set temporary filename
    std::string uuid_filename = config.file_location + "/" + config.random_uuid + ".wav";

    // Create and open file
    std::ofstream wav(uuid_filename, std::ios::binary);

    // Write dummy header (overwrite later)
    wav.write("RIFF\0\0\0\0WAVEfmt ", 16);
    int fmt_chunk_size = 16;
    short audio_format = 1;
    wav.write((char*)&fmt_chunk_size, 4);
    wav.write((char*)&audio_format, 2);
    wav.write((char*)&channels, 2);
    wav.write((char*)&rate, 4);
    int byte_rate = rate * frame_bytes;
    wav.write((char*)&byte_rate, 4);
    short block_align = frame_bytes;
    wav.write((char*)&block_align, 2);
    short bits_per_sample = 32;
    wav.write((char*)&bits_per_sample, 2);
    wav.write("data\0\0\0\0", 8);

    // Wait so recordings will start at the same time
    if (config.mode == "demo" && !config.isMaster) {
        std::cout << "Waiting..." << std::endl;
        while (digitalRead(TRIGGER_GPIO) == LOW) {
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        std::cout << "Received." << std::endl;
    } else {
        while (!start_recording_flag.load()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
    }

    // Set timestamp, just before recording really starts
    long long start_time = std::chrono::high_resolution_clock::now().time_since_epoch().count();

    // Start recording
    int total_bytes = 0;
    for (int i = 0; i < (rate * config.duration) / frames; ++i) {
        rc = snd_pcm_readi(pcm_handle, buffer, frames);
        if (rc == -EPIPE) {
            snd_pcm_prepare(pcm_handle);
            continue;
        } else if (rc < 0) {
            std::cerr << "Read error: " << snd_strerror(rc) << std::endl;
        } else {
            wav.write(buffer, rc * frame_bytes);
            total_bytes += rc * frame_bytes;
        }
    }

    // Fix header
    wav.seekp(4); int chunk_size = 36 + total_bytes; wav.write((char*)&chunk_size, 4);
    wav.seekp(40); wav.write((char*)&total_bytes, 4);
    wav.close();

    // Clean up
    delete[] buffer;
    snd_pcm_drain(pcm_handle);
    snd_pcm_close(pcm_handle);

    // Overwrite timestamp with timestamp of pulse
    if (config.mode == "field") {
        start_time = pulse_time.load();
    }

    // Rename file to use precise timestamp
    std::string final_filename = config.file_location + "/" + config.recording_id + "_" + std::to_string(start_time) + ".wav";
    std::filesystem::rename(uuid_filename, final_filename);

    // Info
    std::cout << "[" << config.card << "] AKA " << config.recording_id << " started at " << start_time << "ns" << std::endl;
}

void transistor(double duration) {
    // Wait for recording to start and half the duration
    while (!start_recording_flag.load()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
    std::this_thread::sleep_for(std::chrono::milliseconds(int(duration * 1000)));

    // Pulse
    digitalWrite(TRANSISTOR_GPIO, HIGH);
    std::this_thread::sleep_for(std::chrono::milliseconds(5));
    digitalWrite(TRANSISTOR_GPIO, LOW);

    // Save pulse
    long long now = std::chrono::high_resolution_clock::now().time_since_epoch().count();
    pulse_time.store(now);
}

// Let slave Pi's know to start recording
void trigger() {
    for (int i = 0; i < 25; ++i) {
        digitalWrite(TRIGGER_GPIO, HIGH);
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
        digitalWrite(TRIGGER_GPIO, LOW);
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}


int main(int argc, char* argv[]) {
    // Check arguments
    if (argc < 4) {
        std::cerr << "Usage: ./r <1|2|3> <test|demo|field> <1|0> (<Pi ID> <Mode> <Master|Slave>)\n";
        return 1;
    }
    int pi_id = std::stoi(argv[1]);
    if (pi_id != 1 && pi_id != 2 && pi_id != 3) {
        std::cerr << "Invalid Pi ID. Use '1', '2', or '3'." << std::endl;
        return 1;
    }
    std::string mode = argv[2];
    if (mode != "test" && mode != "demo" && mode != "field") {
        std::cerr << "Invalid mode. Use 'test', 'demo', or 'field'." << std::endl;
        return 1;
    } else if (mode != "demo") {
        std::cout << "Master|Slave ignored." << std::endl;
    }
    bool isMaster = std::stoi(argv[3]) != 0;

    // Set Pi id
    id.store(pi_id);

    // Setup GPIO
    if (mode != "test") {
        wiringPiSetupGpio();
        pinMode(TRANSISTOR_GPIO, OUTPUT);
        digitalWrite(TRANSISTOR_GPIO, LOW);
    }
    if (mode == "demo" && isMaster) {
        pinMode(TRIGGER_GPIO, OUTPUT);
        digitalWrite(TRIGGER_GPIO, LOW);
        std::this_thread::sleep_for(std::chrono::milliseconds(3000));
    } else if (mode == "demo") {
        pinMode(TRIGGER_GPIO, INPUT);
        pullUpDnControl(TRIGGER_GPIO, PUD_UP);
        std::this_thread::sleep_for(std::chrono::milliseconds(2000));
    }
    
    // Get list of cards to record from. Also turn on phantom power
    std::string list = exec("arecord -l | grep -i scarlett | grep '^card'");
    std::vector<int> cards;
    size_t pos = 0;
    while ((pos = list.find("card ")) != std::string::npos) {
        list = list.substr(pos + 5);
        int card = std::stoi(list);
        cards.push_back(card);
        std::string checkCmd = "amixer -c " + std::to_string(card) + " get 'Line In 1 Phantom Power'";
        std::string status = exec(checkCmd.c_str());
        if (status.find("[off]") != std::string::npos) {
            std::string toggleCmd = "amixer -c " + std::to_string(card) + " set 'Line In 1 Phantom Power' toggle";
            exec(toggleCmd.c_str());
        }
    }

    // Folder where recordings will be saved
    std::string file_location = "/home/hydro/Downloads/recordingModule/recordings";

    // Sampling rate in Hz
    int sample_rate = 44100;

    // Recording duration in seconds
    double duration = 1; // 0.3 is tested to be too little; misses pulse injection

    // Recording frequency in Hz
    double recording_frequency = 0.5; // 0 means record once, 0.1 means every 10 seconds

    // Info
    std::cout << "Pi ID:          " << id.load() << std::endl;
    std::cout << "Mode:           " << mode << std::endl;
    std::cout << "Master:         " << (isMaster ? "True" : "False") << std::endl;
    std::cout << "File location:  " << file_location << std::endl;
    std::cout << "Sample rate:    " << sample_rate << " Hz" << std::endl;
    std::cout << "Duration:       " << duration << " seconds" << std::endl;
    std::cout << "Recording freq: " << recording_frequency << " Hz" << std::endl;
    std::cout << "Cards found:    " << cards.size() << std::endl;
    
    while (true) {
        // Start recording threads
        std::vector<std::thread> threads;
        for (int card : cards) {
            std::string recording_id = "rec_" + std::to_string(id.load()) + ((mode == "test") ? std::to_string(card) : "");
            std::string random_uuid = generate_uuid();
            RecorderConfig config = {card, file_location, recording_id, random_uuid, sample_rate, duration, mode, isMaster};
            threads.emplace_back(record_audio, config);
        }
        // Start pulse thread
        if ((mode == "demo" && isMaster) || mode == "field") {
            threads.emplace_back(transistor, duration * 0.5);
        }
        
        // Prepare and start recording and pulse injection
        std::cout << "Recordings starting..." << std::endl;
        start_recording_flag.store(true);
        if (mode == "demo" && isMaster) trigger();
        for (auto& t : threads) t.join();
        start_recording_flag.store(false);
        std::cout << "All recordings finished." << std::endl;

        // Wait before starting a new recording
        if (recording_frequency == 0) {
            break;
        } else if (!(mode == "demo" && !isMaster)) {
            std::this_thread::sleep_for(std::chrono::milliseconds(int(1.0 / recording_frequency - duration) * 1000));
        }
    
    }

    return 0;
}
