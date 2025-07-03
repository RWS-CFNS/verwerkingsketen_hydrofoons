
import os
import sys
import shutil
import numpy as np

current_script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(current_script_dir, os.pardir)
sys.path.insert(0, parent_dir)

import analyze

def load_test_data(folder):
    file1_from = os.path.join(folder, "backup/three_synced/rec_1_1749395332089410077_synced_1.wav")
    file2_from = os.path.join(folder, "backup/three_synced/rec_2_1749395332089300963_synced_1.wav")
    file3_from = os.path.join(folder, "backup/three_synced/rec_3_1749395332088366066_synced_1.wav")
    file1_to = os.path.join(folder, os.path.basename(file1_from))
    file2_to = os.path.join(folder, os.path.basename(file2_from))
    file3_to = os.path.join(folder, os.path.basename(file3_from))
    shutil.copyfile(file1_from, file1_to)
    shutil.copyfile(file2_from, file2_to)
    shutil.copyfile(file3_from, file3_to)
    return [file1_to, file2_to, file3_to]

def test_load_grouped_wav_files(folder):
    testfiles = load_test_data(folder)
    expected_output = {
        1: [(1, testfiles[0]),
            (2, testfiles[1]),
            (3, testfiles[2])]
    }
    files = analyze.load_grouped_wav_files(folder)

    assert isinstance(files, dict), "Output should be a dictionary."
    assert all(isinstance(k, int) for k in files.keys()), "Keys should be integers (sync IDs)."
    assert all(isinstance(v, list) for v in files.values()), "Values should be lists of tuples."
    assert all(isinstance(t, int) and isinstance(f, str) for pair in files.values() for t, f in pair), "Each tuple should contain an integer and a string."
    assert len(files) == len(expected_output), "Number of sync IDs does not match expected."
    
    assert 1 in files, "Sync ID 1 should be present in the output."
    assert len(files[1]) == len(expected_output[1]), "Number of files for sync ID 1 does not match expected."
    for (id_, file_path), (expected_id, expected_file_path) in zip(files[1], expected_output[1]):
        assert id_ == expected_id, f"Expected ID {expected_id}, got {id_} for sync ID 1."
        assert file_path == expected_file_path, f"Expected file path {expected_file_path}, got {file_path} for sync ID 1."
    print("load_grouped_wav_files function passed.")
    
    # Remove test files
    for file in testfiles:
        if os.path.exists(file):
            os.remove(file)

def test_get_signals(folder):
    testfiles = load_test_data(folder)
    grouped_files = analyze.load_grouped_wav_files(folder)
    expected_output = [
        [
            (1, np.array([])),
            (2, np.array([])),
            (3, np.array([]))
        ],
        44100  # Sample rate
    ]
    signals, fs = analyze.get_signals(grouped_files[1])

    assert isinstance(signals, list), "Signals should be a list."
    assert len(signals) == 3, "Expected 3 signals for sync ID 1."
    assert all(isinstance(sig, tuple) and len(sig) == 2 for sig in signals), "Each signal should be a tuple of (id, numpy array)."
    assert all(isinstance(sig[1], np.ndarray) for sig in signals), "Each signal's second element should be a numpy array."
    assert all(len(sig[1]) == len(signals[0][1]) for sig in signals), "All signals should have the same length."
    assert fs == 44100, "Expected sample rate of 44100 Hz."
    print("get_signals function passed.")
    
    # Remove test files
    for file in testfiles:
        if os.path.exists(file):
            os.remove(file)

def test_compute_gcc_phat(folder):
    testfiles = load_test_data(folder)
    grouped_files = analyze.load_grouped_wav_files(folder)
    signals, fs = analyze.get_signals(grouped_files[1])
    gcc_phat, lags, center = analyze.compute_gcc_phat(signals[0][1], signals[1][1])

    assert isinstance(gcc_phat, np.ndarray), "GCC-PHAT should be a numpy array."
    assert len(gcc_phat) == len(lags), "GCC-PHAT and lags should have the same length."
    assert center == len(lags) // 2, "Center index should be at half the length of lags."
    print("compute_gcc_phat function passed.")
    
    # Remove test files
    for file in testfiles:
        if os.path.exists(file):
            os.remove(file)

def test_find_best_peak():
    succeed_three_tries_array = np.array([
        1.0, 0.1, 0.0, -0.2, 0.3,   # Peak 1 (index 0): 1.0 (highest overall, but at edge)
        0.9, -0.1, -0.3, 0.4, -0.5,  # Peak 2 (index 5): 0.9 (second highest, but negative neighbors)
        0.8, 0.7, 0.6, -0.4, -0.5,  # Peak 3 (index 10): 0.8 (third highest, good neighbors 0.7, 0.6)
        0.5, 0.4, -0.6, -0.7, -0.8
    ])
    peak_idx = analyze.find_best_peak(succeed_three_tries_array)
    assert peak_idx == 10, "Expected peak index at 10, found at " + str(peak_idx)
    fallback_array_negative = np.array([
        1.0, 0.1, -0.5, -0.6, 0.2, # Peak 1 at 0 (edge)
        0.9, -0.1, -0.2, 0.3, -0.7, # Peak 2 at 5 (no positive neighbors)
        0.8, -0.3, -0.4, 0.4, -0.8, # Peak 3 at 10 (no positive neighbors)
        0.7, -0.5, -0.6, 0.5, -0.9 # Peak 4 at 15 (no positive neighbors)
    ])
    peak_idx = analyze.find_best_peak(fallback_array_negative)
    assert peak_idx == 10, "Expected fallback peak index at 8, found at " + str(peak_idx)


def run_all_tests(folder):
    print("-- Running unittests. --")
    test_load_grouped_wav_files(folder)
    test_get_signals(folder)
    test_compute_gcc_phat(folder)
    test_find_best_peak()
    print("-- All unittests passed. --")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(script_dir, "../../recordings"))
    run_all_tests(folder)
    # load_test_data(folder)