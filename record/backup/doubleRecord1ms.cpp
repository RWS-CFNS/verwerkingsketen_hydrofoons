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

using namespace std;
using namespace std::chrono;

namespace fs = std::filesystem;

struct RecorderConfig {
    string device_name;
    int duration_sec = 5;
    string base_filename;
};

atomic<bool> start_recording_flag(false);

string generate_uuid() {
    random_device rd;
    mt19937 gen(rd());
    uniform_int_distribution<int> dist(0, 15);
    stringstream ss;
    for (int i = 0; i < 32; ++i) ss << hex << dist(gen);
    return ss.str();
}

long long t1 = 0;

void record_audio(const RecorderConfig& config) {
    snd_pcm_t* pcm_handle;
    snd_pcm_hw_params_t* params;
    snd_pcm_uframes_t frames = 1024;
    int rc;
    unsigned int rate = 44100;
    int channels = 2;

    rc = snd_pcm_open(&pcm_handle, config.device_name.c_str(), SND_PCM_STREAM_CAPTURE, 0);
    if (rc < 0) {
        cerr << "Unable to open device " << config.device_name << ": " << snd_strerror(rc) << endl;
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
        cerr << "Unable to set hw parameters: " << snd_strerror(rc) << endl;
        return;
    }

    int frame_bytes = channels * sizeof(int32_t);
    int buffer_size = frames * frame_bytes;
    char* buffer = new char[buffer_size];

    string uuid = generate_uuid();
    stringstream tmp_filename;
    tmp_filename << config.base_filename << "_" << uuid << ".wav";

    while (!start_recording_flag.load()) {
        this_thread::sleep_for(milliseconds(1));
    }

    ofstream wav(tmp_filename.str(), ios::binary);

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

    auto start_ts = high_resolution_clock::now();

    int total_bytes = 0;
    for (int i = 0; i < (rate * config.duration_sec) / frames; ++i) {
        rc = snd_pcm_readi(pcm_handle, buffer, frames);
        if (rc == -EPIPE) {
            snd_pcm_prepare(pcm_handle);
            continue;
        } else if (rc < 0) {
            cerr << "Read error: " << snd_strerror(rc) << endl;
        } else {
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

    // Get pulse timestamp from file
    ifstream file("./pulse_timestamp.txt");
    int64_t pulse_timestamp;
    file >> pulse_timestamp;
    file.close();

    // Rename file to use precise timestamp
    auto timestamp = start_ts.time_since_epoch().count() - pulse_timestamp;
    stringstream new_filename;
    new_filename << config.base_filename << "_" << timestamp << ".wav";
    fs::rename(tmp_filename.str(), new_filename.str());

    auto end_ts = high_resolution_clock::now();
    cout << "[Time at start of script] " << (t1 - pulse_timestamp)/ 1000000 << " ms\n";
    auto duration = duration_cast<microseconds>(end_ts - start_ts).count();
    cout << "[Time taken to start of record] " << timestamp / 1000000 << " ms\n";
    cout << "[" << config.device_name << "] Took " << duration / 1000.0 << " ms | Started at " << timestamp << "ns" << endl;

    

    // cout << "[ Time at start of recordingz: " << start_ts.time_since_epoch().count() / 1000000 << " ms\n";
}

int main() {
    auto time1 = std::chrono::high_resolution_clock::now();
    t1 = time1.time_since_epoch().count();

    // Get id from file
    ifstream file("./id.txt");
    string id;
    file >> id;
    file.close();

    vector<RecorderConfig> configs = {
        {"hw:3,0", 15, "/home/hydro/Downloads/recordingModule/recordings/rec_" + id},
        // {"hw:4,0", 15, "/home/hydro/Downloads/recordings/rec_card4"}
    };

    vector<thread> threads;
    for (auto& cfg : configs) {
        threads.emplace_back(record_audio, cfg);
    }

    // cout << "All recorders ready. Starting...\n";
    // this_thread::sleep_for(seconds(1));
    // cout << "2...\n";
    // this_thread::sleep_for(seconds(1));
    // cout << "1...\n";
    // this_thread::sleep_for(seconds(1));
    start_recording_flag.store(true);

    for (auto& t : threads) t.join();
    // cout << "All recordings finished." << endl;
    return 0;
}
