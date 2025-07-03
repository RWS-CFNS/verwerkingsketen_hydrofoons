import os
import numpy as np
import shutil
import sys

current_script_dir = os.path.dirname(__file__)
parent_dir = os.path.join(current_script_dir, os.pardir)
sys.path.insert(0, parent_dir)

import synchronize

def load_test_data(folder):
    file1_from = os.path.join(folder, "backup/three/rec_1_1749395332089410077.wav")
    file2_from = os.path.join(folder, "backup/three/rec_2_1749395332089300963.wav")
    file3_from = os.path.join(folder, "backup/three/rec_3_1749395332088366066.wav")
    file1_to = os.path.join(folder, os.path.basename(file1_from))
    file2_to = os.path.join(folder, os.path.basename(file2_from))
    file3_to = os.path.join(folder, os.path.basename(file3_from))
    shutil.copyfile(file1_from, file1_to)
    shutil.copyfile(file2_from, file2_to)
    shutil.copyfile(file3_from, file3_to)
    return [file1_to, file2_to, file3_to]              

def test_load_wav_files(folder):
    testfiles = load_test_data(folder)
    expected_output = [
        (1749395332089410077, testfiles[0]),
        (1749395332089300963, testfiles[1]),
        (1749395332088366066, testfiles[2])
    ]
    files = synchronize.load_wav_files()

    assert all(isinstance(t, int) for t, _ in files), "Timestamps should be integers."
    assert all(isinstance(f, str) for _, f in files), "File paths should be strings."
    assert len(files) == len(expected_output), "Number of files loaded does not match expected."
    for (timestamp, file_path), (expected_timestamp, expected_file_path) in zip(files, expected_output):
        assert timestamp == expected_timestamp, f"Expected timestamp {expected_timestamp}, got {timestamp}."
        assert file_path == expected_file_path, f"Expected file path {expected_file_path}, got {file_path}."
    print("load_test_data function passed.")
    
    # Remove test files
    for file in testfiles:
        if os.path.exists(file):
            os.remove(file)

def test_get_signals(folder):
    testfiles = load_test_data(folder)
    files = synchronize.load_wav_files()
    signals, _, _ = synchronize.get_signals(files, "demo")

    assert all(isinstance(sig, np.ndarray) for sig in signals), "Each signal must be a numpy array."
    assert all(len(sig) == len(signals[0]) for sig in signals), "All signals should be the same length."
    print("get_signals function passed.")
    
    # Remove test files
    for file in testfiles:
        if os.path.exists(file):
            os.remove(file)

def run_all_tests(folder):
    print("-- Running unittests. --")
    test_load_wav_files(folder)
    test_get_signals(folder)
    print("-- All unittests passed. --")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(script_dir, "../../recordings"))
    run_all_tests(folder)
    # load_test_data(folder)