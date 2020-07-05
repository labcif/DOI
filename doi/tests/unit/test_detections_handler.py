import unittest
import os
from core.detections_handler import DetectionsHandler
import utils.file as file_utils

"""
Unit tests about the HandleDetections component
"""

TEMP_TEST_DIR = 'tests/unit/temp'
TEST_IMAGE_FILENAME = 'test_image.jpg'
TEST_IMAGE_PATH = 'tests/unit/test_files/' + TEST_IMAGE_FILENAME

class TestHandleDetections(unittest.TestCase):
    detections_handler = None
    classes_to_search_for = ['dog', 'car']

    def setUp(self):
        self.detections_handler = DetectionsHandler(self.classes_to_search_for, [], 'some_dir_for_results')
    
    def test_handle_detections_with_selected_class(self):
        """
        Test that it can register an image with class of interest in its dictionary
        """
        # arrange
        detection_class = self.classes_to_search_for[0]
        image_path = 'some_image_path.jpg'
        detections = [(detection_class, 0.9, (1, 1, 1, 1))]
        # act
        self.detections_handler.handle_detections(image_path, detections, False)
        # assert
            # dictionary has class from detections
        self.assertIn(detection_class, self.detections_handler.objects_images_dict.keys())
            # image with detections is in the list
        self.assertIn(image_path, self.detections_handler.objects_images_dict[detection_class][0]['image'])

    def test_handle_detections_with_class_not_selected(self):
        """
        Test that it not register an image with class not selected in its dictionary
        """
        # arrange
        detection_class = 'some_class_not_selected'
        image_path = 'some_image_path.jpg'
        detections = [(detection_class, 0.9, (1, 1, 1, 1))]
        # act
        self.detections_handler.handle_detections(image_path, detections, False)
        # assert
            # dictionary doesn't have class from detections
        self.assertNotIn(detection_class, self.detections_handler.objects_images_dict.keys())
            # empty lists of images for all selected classes
        for class_name in self.classes_to_search_for:
            self.assertEqual(len(self.detections_handler.objects_images_dict[class_name]), 0)

    def test_handle_detections_from_image_with_two_objects_of_selected_class(self):
        """
        Test that it not register in its dictionary same image twice, when image has more than one object of the same class
        """
        # arrange
        detection_class = self.classes_to_search_for[0]
        image_path = 'some_image_path.jpg'
        detections1 = [(detection_class, 0.9, (1, 1, 1, 1))]
        detections2 = [(detection_class, 0.9, (2, 2, 2, 2))]
        # act
        self.detections_handler.handle_detections(image_path, detections1, False)
        self.detections_handler.handle_detections(image_path, detections2, False)
        # assert
            # dictionary has class from detections
        self.assertIn(detection_class, self.detections_handler.objects_images_dict.keys())
            # image with detections is in the list, only once
        self.assertEqual(len(self.detections_handler.objects_images_dict[detection_class]), 1)
        self.assertIn(image_path, self.detections_handler.objects_images_dict[detection_class][0]['image'])

    
        
class TestDrawDetections(unittest.TestCase):
    detections_handler = None
    classes_to_search_for = ['dog', 'car']
    supported_classes = ['dog', 'car', 'horse']

    def setUp(self):
        file_utils.create_directory_if_not_exists(TEMP_TEST_DIR)
        self.detections_handler = DetectionsHandler(self.classes_to_search_for, self.supported_classes, TEMP_TEST_DIR)

    def tearDown(self):
        file_utils.remove_dir_if_exists(TEMP_TEST_DIR)
    
    def test_draw_detections_from_an_image_with_selected_class(self):
        """
        Test that it creates an image from an image that contains the selected class
        """
        # arrange
        detection_class = self.classes_to_search_for[0]
        image_path = TEST_IMAGE_PATH
        detections = [(detection_class, 0.9, (220, 380, 195, 320))]
        # act
        self.detections_handler.handle_detections(image_path, detections, create_image_with_detections=True)
        # assert
        self.assertTrue(os.path.isfile(os.path.join(TEMP_TEST_DIR, TEST_IMAGE_FILENAME + '_results_0.jpg')))

    def test_not_draw_detections_when_disabled(self):
        """
        Test that it doesn't create an image with detections, when this output is disabled
        """
        # arrange
        detection_class = self.classes_to_search_for[0]
        image_path = TEST_IMAGE_PATH
        detections = [(detection_class, 0.9, (220, 380, 195, 320))]
        # act
            # False will disable drawing detections in new image
        self.detections_handler.handle_detections(image_path, detections, create_image_with_detections=False)
        # assert
            # dir exists
        self.assertTrue(os.path.isdir(TEMP_TEST_DIR))
            # dir is empty
        self.assertEqual(len(os.listdir(TEMP_TEST_DIR)), 0)