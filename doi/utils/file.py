import os
import sys
import glob
import shutil
from contextlib import contextmanager


# read lines from file to a list of strings (without '\n')
def read_file(file_path):
    with open(file_path) as file:
        lines = file.read().splitlines()
        return lines

# create directory if not exists
def create_directory_if_not_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def delete_all_files_in_dir_by_name(directory, filename_pattern):
    for f in glob.glob(os.path.join(directory, filename_pattern)):
        try:
            os.remove(f)
        except:
            pass

def remove_dir_if_exists(directory):
    try:
        shutil.rmtree(directory)
    except:
        pass

# redirects stderr and stdout to file
@contextmanager
def stdout_redirected(to=os.devnull):
    '''
    import os

    with stdout_redirected(to=filename):
        print("from Python")
        os.system("echo non-Python applications are also supported")
    '''
    fd = sys.stdout.fileno()
    fderr = sys.stderr.fileno()

    ##### assert that Python and C stdio write using the same file descriptor
    ####assert libc.fileno(ctypes.c_void_p.in_dll(libc, "stdout")) == fd == 1

    def _redirect_stdout(to):
        sys.stdout.close() # + implicit flush()
        os.dup2(to.fileno(), fd) # fd writes to 'to' file
        sys.stdout = os.fdopen(fd, 'w') # Python writes to fd

    def _redirect_stderr(to):
        sys.stderr.close() # + implicit flush()
        os.dup2(to.fileno(), fderr) # fderr writes to 'to' file
        sys.stderr = os.fdopen(fderr, 'w') # Python writes to fderr

    with os.fdopen(os.dup(fd), 'w') as old_stdout, os.fdopen(os.dup(fderr), 'w') as old_stderr:
        with open(to, 'w') as file:
            _redirect_stdout(to=file)
            _redirect_stderr(to=file)
        try:
            yield # allow code to be run with the redirected stdout
        finally:
            _redirect_stdout(to=old_stdout) # restore stdout.
            _redirect_stderr(to=old_stderr) # restore stderr.
                                            # buffering and flags such as
                                            # CLOEXEC may be different

