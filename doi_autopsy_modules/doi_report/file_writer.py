from shutil import copy2
import os.path

def copy_to_results_folder(cwd, result_file):
    if not os.path.isdir(os.path.join(cwd, "results")):
        os.mkdir(os.path.join(cwd, "results"))
    copy2(result_file, os.path.join(cwd, "results"))
    return "results/" + result_file.split('/')[-1]

def copy_to_original_folder(cwd, original_file):
    if not os.path.isdir(os.path.join(cwd, "original")):
        os.mkdir(os.path.join(cwd, "original"))
    copy2(original_file, os.path.join(cwd, "original"))
    return "original/" + original_file.split('\\')[-1]

def get_file_with_extension(file_path):
    return file_path.rsplit('/', 1)[-1].split('_results')[0]

def get_file_original_with_extension(file_path):
    return file_path.rsplit('/')[-1]
