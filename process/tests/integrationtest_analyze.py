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

def test_analyze_script(folder):
    load_test_data(folder)
    # Emtpy results.txt
    output_file = os.path.join(folder, "results.txt")
    with open(output_file, 'w') as f:
        pass
    
    # Analyze
    grouped_files = analyze.load_grouped_wav_files(folder)
    with open(output_file, "a") as f:
        analyze.calculate_signal_pairs(grouped_files, f, "demo")
    
    # Check if results.txt contains expected output
    expected_output = [
        '[Group 1] Signal pair (1, 2): Estimated distance from center: 0.00 cm. SNR: 30.88\n', 
        '[Group 1] Signal pair (1, 3): Estimated distance from center: 8.17 cm. SNR: 41.94\n',
        '[Group 1] Signal pair (2, 3): Estimated distance from center: 7.78 cm. SNR: 24.36\n'
    ]
    results = []
    with open(output_file, 'r') as f:
        results = f.readlines()
    
    assert len(results) == len(expected_output), "Number of results does not match expected."
    for result, expected in zip(results, expected_output):
        assert result == expected, f"Expected '{expected.strip()}', got '{result.strip()}'"

    print("integration test analyze.py passed.")
    
    # Remove test files
    for file in os.listdir(folder):
        if file.endswith(".wav"):
            os.remove(os.path.join(folder, file))

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(script_dir, "../../recordings"))
    test_analyze_script(folder)
    # load_test_data(folder)