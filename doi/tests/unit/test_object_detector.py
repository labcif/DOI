import unittest
from core.object_detector import ObjectDetector
from unittest.mock import Mock

"""
Unit tests about the ObjectDetector component
"""

DUMMY_DETECTION_GPU = [('dog', 0.9, (220, 380, 195, 320))]
DUMMY_DETECTION_CPU = [('dog', 0.8, (221, 381, 196, 321))]

class TestObjectDetection(unittest.TestCase):
    object_detector = None

    def setUp(self):
        self.object_detector = ObjectDetector(dict(), 0.5, gpu_mode=True)
        # override methods to mock their behavior
        self.object_detector._get_detections_gpu_mode = Mock(return_value=DUMMY_DETECTION_GPU)
        self.object_detector._get_detections_cpu_mode = Mock(return_value=DUMMY_DETECTION_CPU)
    
    def test_object_detection(self):
        """
        Test that it can perform object detection without error
        """
        # arrange
        self.object_detector._gpu_mode = True # force GPU mode to test, because in instanciation it could have switched to CPU (if GPU not supported)
        # act
        result = self.object_detector.apply_object_detection('some_image_path.jpg')
        # assert
        self.assertIs(result, DUMMY_DETECTION_GPU)

    def test_object_detection_in_different_modes(self):
        """
        Test that it can perform object detection, in the right mode (CPU/GPU)
        """
        # arrange and act
        self.object_detector._gpu_mode = True
        result1 = self.object_detector.apply_object_detection('some_image_path.jpg')
        self.object_detector._gpu_mode = False
        result2 = self.object_detector.apply_object_detection('some_image_path.jpg')
        # assert
        self.assertIs(result1, DUMMY_DETECTION_GPU)
        self.assertIs(result2, DUMMY_DETECTION_CPU)

    def test_switch_to_cpu_on_gpu_error(self):
        """
        Test that it automatically switchs to CPU mode when error occurs on GPU mode
        """
        # arrange
            # override method, to raise error
        self.object_detector._get_detections_gpu_mode = Mock(side_effect=ValueError)
        self.object_detector._gpu_mode = True
        #act
        result = self.object_detector.apply_object_detection('some_image_path.jpg')
        # assert
        self.assertFalse(self.object_detector._gpu_mode)
        self.assertIs(result, DUMMY_DETECTION_CPU)



