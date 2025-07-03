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

using namespace std;
using namespace std::chrono;
namespace fs = filesystem;

std::atomic<bool> start_recording_flag(false);

struct RecorderConfig {
    std::string device;
    std::string file_location;
    std::string recording_id;
    std::string random_uuid;
    int sample_rate;
    int duration_sec;
    long long correction_offset;
};

std::string exec(const char* cmd) {
    std::array<char, 128> buffer;
    std::string result;
    std::unique_ptr<FILE, decltype(&pclose)> pipe(popen(cmd, "r"), pclose);
    if (!pipe) return "ERROR";
    while (fgets(buffer.data(), buffer.size(), pipe.get()) != nullptr)
        result += buffer.data();
    return result;
}

std::string generate_uuid() {
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<int> dist(0, 15);
    std::stringstream ss;
    for (int i = 0; i < 32; ++i) ss << std::hex << dist(gen);
    return ss.str();
}

void record_audio(const RecorderConfig& config) {
    snd_pcm_t* pcm_handle;
    snd_pcm_hw_params_t* params;
    snd_pcm_uframes_t frames = 1024;
    int rc;
    unsigned int rate = config.sample_rate;
    int channels = 2;

    rc = snd_pcm_open(&pcm_handle, config.device.c_str(), SND_PCM_STREAM_CAPTURE, 0);
    if (rc < 0) {
        std::cerr << "Unable to open device " << config.device << ": " << snd_strerror(rc) << std::endl;
        return;
    }

    snd_pcm_hw_params_alloca(&params);
    snd_pcm_hw_params_any(pcm_handle, params);
    snd_pcm_hw_params_set_access(pcm_handle, params, SND_PCM_ACCESS_RW_INTERLEAVED);
    snd_pcm_hw_params_set_format(pcm_handle, params, SND_PCM_FORMAT_S32_LE);
    snd_pcm_hw_params_set_channels(pcm_handle, params, channels);
    snd_pcm_hw_params_set_rate_near(pcm_handle, params, &rate, 0);
    snd_pcm_hw_params_set_period_size_near(pcm_handle, params, &frames, 0);

    rc = snd_pcm_hw_params(pcm_handle, params);
    if (rc < 0) {
        std::cerr << "Unable to set hw parameters: " << snd_strerror(rc) << std::endl;
        return;
    }

    int frame_bytes = channels * sizeof(int32_t);
    int buffer_size = frames * frame_bytes;
    char* buffer = new char[buffer_size];

    std::string uuid_filename = config.file_location + "/" + config.random_uuid + ".wav";

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

    while (!start_recording_flag.load()) {
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }

    long long start_time = 0;
    bool first_read_flag = true;

    int total_bytes = 0;
    for (int i = 0; i < (rate * config.duration_sec) / frames; ++i) {
        rc = snd_pcm_readi(pcm_handle, buffer, frames);
        if (rc == -EPIPE) {
            snd_pcm_prepare(pcm_handle);
            continue;
        } else if (rc < 0) {
            std::cerr << "Read error: " << snd_strerror(rc) << std::endl;
        } else {
            if (first_read_flag) {
                start_time = std::chrono::high_resolution_clock::now().time_since_epoch().count();
                first_read_flag = false;
            }
            wav.write(buffer, rc * frame_bytes);
            total_bytes += rc * frame_bytes;
        }
    }

    // Fix header
    wav.seekp(4); int chunk_size = 36 + total_bytes; wav.write((char*)&chunk_size, 4);
    wav.seekp(40); wav.write((char*)&total_bytes, 4);
    wav.close();

    delete[] buffer;
    snd_pcm_drain(pcm_handle);
    snd_pcm_close(pcm_handle);

    // Add user identified correction offset
    start_time -= config.correction_offset;

    // Rename file to use precise timestamp
    std::string final_filename = config.file_location + "/" + config.recording_id + "_" + std::to_string(start_time) + ".wav";
    std::filesystem::rename(uuid_filename, final_filename);

    std::cout << "[" << config.device << "] AKA " << config.recording_id << " started at " << start_time << "ns" << std::endl;
}


int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: ./rec <correction offset in ns> (common is 0 or 18'385'556)\n";
        return 1;
    }

    long long corr_offset = std::stoi(argv[1]);
    
    // List of device cards to record from (Also turn on phantom power)
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

    // ID of this Raspberry Pi
    std::ifstream file("./id.txt");
    std::string pi_id;
    file >> pi_id;
    file.close();

    // Folder where recordings will be saved
    std::string file_location = "/home/hydro/Downloads/recordingModule/recordings";

    // Recording duration in seconds
    int duration_sec = 15;

    // Recording frequency in Hz
    double recording_frequency = 0; // 0 means record once

    // Sampling rate in Hz
    int sample_rate = 44100;

    // Check number of cards
    int single_pi = (cards.size() > 1) ? 1 : 0;

    // Info
    std::cout << "Pi ID:          " << pi_id << std::endl;
    std::cout << "N devices:      " << cards.size() << std::endl;
    std::cout << "Single Pi mode: " << (single_pi ? "True" : "False") << std::endl;
    std::cout << "Duration:       " << duration_sec << " seconds" << std::endl;
    
    while (true) {

        // Start recording threads
        std::vector<std::thread> threads;
        for (int card : cards) {
            std::string device = "hw:" + std::to_string(card) + ",0";
            std::string recording_id = "rec_" + pi_id + (single_pi ? std::to_string(card) : "");
            std::string random_uuid = generate_uuid();
            RecorderConfig config = {device, file_location, recording_id, random_uuid, sample_rate, duration_sec, corr_offset};
            threads.emplace_back(record_audio, config);
        }

        std::cout << "Recordings starting..." << std::endl;
        start_recording_flag.store(true);

        for (auto& t : threads) t.join();

        start_recording_flag.store(false);

        std::cout << "All recordings finished." << std::endl;

        if (recording_frequency == 0) {
            break;
        } else {
            std::this_thread::sleep_for(std::chrono::milliseconds(int(1.0 / recording_frequency - duration_sec)));
        }
    
    }

    return 0;
}
