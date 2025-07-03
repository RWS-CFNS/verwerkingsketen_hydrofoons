import os
import sys
import shutil
import subprocess
import time

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

def clear_results_file(folder):
    output_file = os.path.join(folder, "results.txt")
    with open(output_file, 'w') as f:
        pass

def start_script(script_to_run):
    # Get script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(script_dir, ".."))
    script_to_run = os.path.join(folder, script_to_run)
    # Start script
    process = subprocess.Popen(
        [sys.executable, script_to_run] + ["demo"],
        stdout=subprocess.DEVNULL, # Redirect standard output to /dev/null
        stderr=subprocess.DEVNULL  # Redirect standard error to /dev/null
    )
    # Wait for the specified duration
    time.sleep(2)
    # End script
    process.terminate()

def verify_results(folder):
    results = []
    with open(os.path.join(folder, "results.txt"), 'r') as f:
        results = f.readlines()
    
    expected_output = [
        '[Group 0] Signal pair (1, 2): Estimated distance from center: 0.00 cm. SNR: 30.88\n', 
        '[Group 0] Signal pair (1, 3): Estimated distance from center: 8.17 cm. SNR: 41.94\n',
        '[Group 0] Signal pair (2, 3): Estimated distance from center: 7.78 cm. SNR: 24.36\n'
    ]
    
    assert len(results) == len(expected_output), "Number of results does not match expected."
    for result, expected in zip(results, expected_output):
        assert result == expected, f"Expected '{expected.strip()}', got '{result.strip()}'"
    
    print("Acception test pipeline (synchronize.py with analyze.py) passed.")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.normpath(os.path.join(script_dir, "../../recordings"))
    testfiles = load_test_data(folder)
    clear_results_file(folder)
    start_script("synchronize.py")
    start_script("analyze.py")
    verify_results(folder)
    