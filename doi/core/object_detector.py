import os
import utils.file as file_utils
import detectors.opencv as opencv
# only import darknet on class instantiation to prevent errors with missing dependencies or not compatible GPU on app startup
darknet = None


class ObjectDetector:
    # Initialize
    _config = []
    _threshold = 0.5
    _gpu_mode = True
    _working_directory = '.'

    def __init__(self, config, threshold, gpu_mode=True, app_working_directory='.'):
        global darknet
        if gpu_mode:
            # try to import darknet, if error: switch to CPU
            try:
                import detectors.darknet as darknet
            except:
                print('darknet misses dependencies. Only CPU mode is available.')
                gpu_mode = False
        self._config = config
        self._threshold = threshold
        self._gpu_mode = gpu_mode
        self._working_directory = app_working_directory
        print('Mode:', 'GPU' if gpu_mode else 'CPU')

    # Apply object detection - GPU mode (using Darknet)
    def _get_detections_gpu_mode(self, image):
        # need to change working dir to the dir of the app, because darknet works with relative paths refered in the meta file
        cwd = os.getcwd()
        os.chdir(self._working_directory)
        # hide verbose output from darknet
        with file_utils.stdout_redirected():
            try:
                return darknet.performDetect(image, self._threshold, self._config['config_path'], self._config['weights_path'], self._config['meta_path'], showImage=False)
            finally:
                # reset the current working dir
                os.chdir(cwd)

    # Apply object detection - CPU mode (using OpenCV)
    def _get_detections_cpu_mode(self, image):
        return opencv.performDetect(image, self._threshold, self._config['config_path'], self._config['weights_path'], self._config['classes_path'])

    # Apply object detection
    def apply_object_detection(self, image):
        if self._gpu_mode:
            try:
                detections = self._get_detections_gpu_mode(image)
            except:
                print('Error on GPU mode. Trying to switch to CPU mode...')
                self._gpu_mode = False
                detections = self._get_detections_cpu_mode(image)
        else:
            detections = self._get_detections_cpu_mode(image)

        return detections
