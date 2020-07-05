import unittest
import doi
import argparse
import os
import utils.file as file_utils
import utils.json as json_utils

"""
Integration tests about the feature: Detect objects of selected classes in images from a provided directory
"""

TEMP_TEST_DIR = 'tests/integration/temp'
RESULTS_TEST_DIR = 'tests/integration/results'
TEST_FILES_DIR = 'tests/integration/test_files'
RESULTS_JSON_FILE_PATH = os.path.join(RESULTS_TEST_DIR, 'results.json')

# class to get a valid args object
class Args():
    def __init__(self, config, no_output_images, classes, classesfile):
        self.config = config
        self.nogpu = True
        self.no_output_images = no_output_images
        self.classes = classes
        self.classesfile = classesfile
        self.threshold = 0.5
        self.dir = os.path.join(TEST_FILES_DIR, 'test_dir')
        self.no_results_clean = False

# tests superclass
class TestDetect(unittest.TestCase):
    args = None
    
    def setUp(self):
        file_utils.remove_dir_if_exists(TEMP_TEST_DIR)
        file_utils.remove_dir_if_exists(RESULTS_TEST_DIR)
        doi.TEMP_DIR = TEMP_TEST_DIR
        doi.RESULTS_DIR = RESULTS_TEST_DIR
        doi.arg_parser = argparse.ArgumentParser()
        config = doi.set_config('tiny')
        self.args = Args(config, no_output_images=False, classes=['dog'], classesfile=None)


class TestDetectInvalidInputs(TestDetect):
    def test_detect_with_class_not_supported(self):
        """
        Test that it not process images when class provided is not supported and exits
        """
        # arrange
        self.args.classes=['not_supported_class']
        # act and assert
        with self.assertRaises(SystemExit):
            doi.detect(self.args)
        # didn't save the json file and image results
        self.assertEqual(len(os.listdir(RESULTS_TEST_DIR)), 0)

    def test_detect_with_no_classes_selected(self):
        """
        Test that it not process images when no classes are provided and exits
        """
        # arrange
        self.args.classes=[]
        # act and assert
        with self.assertRaises(SystemExit):
            doi.detect(self.args)
        # didn't save the json file and image results
        self.assertEqual(len(os.listdir(RESULTS_TEST_DIR)), 0)

    def test_detect_with_invalid_directory(self):
        """
        Test that it not process images when provided directory is invalid and exits
        """
        # arrange
        self.args.dir = 'dir_that_doesnt_exist'
        # act and assert
        with self.assertRaises(SystemExit):
            doi.detect(self.args)
        # didn't save the json file and image results
        self.assertEqual(len(os.listdir(RESULTS_TEST_DIR)), 0)

    def test_detect_on_directory_with_no_images(self):
        """
        Test that it not process images when provided directory doesn't have image files, with no error
        """
        # arrange
        self.args.dir = os.path.join(TEST_FILES_DIR, 'test_dir_no_images')
        # act and assert
        with self.assertRaises(SystemExit):
            doi.detect(self.args)
        # didn't save the json file and image results
        self.assertEqual(len(os.listdir(RESULTS_TEST_DIR)), 0)


class TestDetectRun(TestDetect):
    def test_detect_with_selected_class_by_arg(self):
        """
        Test that it can process an image, providing classes to search for by argument
        """
        # arrange
        # act
        doi.detect(self.args)
        # assert
            # saved the json file
        self.assertTrue(os.path.isfile(RESULTS_JSON_FILE_PATH))
        results = json_utils.read_file(RESULTS_JSON_FILE_PATH)
        self.assertIn('dog', results.keys())
        self.assertTrue(len(results['dog']) > 0)
            # saved results in image
        self.assertEqual(len(os.listdir(RESULTS_TEST_DIR)), 2)

    def test_detect_with_selected_class_by_file(self):
        """
        Test that it can process an image, providing classes to search for by a json file
        """
        # arrange
        with open(os.path.join(TEST_FILES_DIR, 'test_set_classes_file.json')) as classesfile:
            self.args.classes = None
            self.args.classesfile = classesfile
            # act
            doi.detect(self.args)
        # assert
            # saved the json file with the results
        self.assertTrue(os.path.isfile(RESULTS_JSON_FILE_PATH))
        results = json_utils.read_file(RESULTS_JSON_FILE_PATH)
        self.assertIn('dog', results.keys())
        self.assertTrue(len(results['dog']) > 0)
            # saved results in image
        self.assertEqual(len(os.listdir(RESULTS_TEST_DIR)), 2)

    def test_detect_with_no_output_images(self):
        """
        Test that it can process an image, and doesn't save the results in an image file, if disabled
        """
        # arrange
        self.args.no_output_images=True
        # act
        doi.detect(self.args)
        # assert
            # saved the json file with the results
        self.assertTrue(os.path.isfile(RESULTS_JSON_FILE_PATH))
        results = json_utils.read_file(RESULTS_JSON_FILE_PATH)
        self.assertIn('dog', results.keys())
        self.assertTrue(len(results['dog']) > 0)
            # didn't saved results in images
        self.assertEqual(len(os.listdir(RESULTS_TEST_DIR)), 1)

    def test_detect_with_class_not_present_in_image(self):
        """
        Test that it can process an image with no objects of selected class
        """
        # arrange
        self.args.classes = ['horse']
        # act
        doi.detect(self.args)
        # assert
            # saved the json file with the results
        results = json_utils.read_file(RESULTS_JSON_FILE_PATH)
        self.assertIn('horse', results.keys())
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results['horse']), 0)
            # didn't save results in images
        self.assertEqual(len(os.listdir(RESULTS_TEST_DIR)), 1)


class TestDetectFilesAndDir(TestDetect):
    def test_detect_subdirectories(self):
        """
        Test that it can process images in subdirectories of the provided directory
        """
        # arrange
        self.args.dir = os.path.join(TEST_FILES_DIR, 'test_dir_sub')
        # act
        doi.detect(self.args)
        # assert
            # saved the json file with the results
        results = json_utils.read_file(RESULTS_JSON_FILE_PATH)
        self.assertIn('dog', results.keys())
        self.assertEqual(len(results['dog']), 3)

    def test_detect_hidden_files(self):
        """
        Test that it can process hidden image files, in hidden directory
        """
        # arrange
        self.args.dir = os.path.join(TEST_FILES_DIR, 'test_dir_hidden')
        # act
        doi.detect(self.args)
        # assert
            # saved the json file with the results
        results = json_utils.read_file(RESULTS_JSON_FILE_PATH)
        self.assertIn('dog', results.keys())
        self.assertEqual(len(results['dog']), 1)

    def test_detect_files_with_not_image_extension(self):
        """
        Test that it can process image files, even if their extension is wrong (eg. jpg image hidden in a .txt file)
        """
        # arrange
        self.args.dir = os.path.join(TEST_FILES_DIR, 'test_dir_txt_image')
        # act
        doi.detect(self.args)
        # assert
            # saved the json file with the results
        results = json_utils.read_file(RESULTS_JSON_FILE_PATH)
        self.assertIn('dog', results.keys())
        self.assertEqual(len(results['dog']), 1)


class TestDetectFileConvertion(TestDetect):
    def test_convert_not_supported_format_before_detect(self):
        """
        Test that it can convert images in format not supported by detectors, before detect (eg. webp format)
        """
        # arrange
        self.args.dir = os.path.join(TEST_FILES_DIR, 'test_dir_convert')
        # act
        doi.detect(self.args)
        # assert
            # saved the json file with the results
        results = json_utils.read_file(RESULTS_JSON_FILE_PATH)
        self.assertIn('dog', results.keys())
        self.assertEqual(len(results['dog']), 1)
         # saved results in image
        self.assertEqual(len(os.listdir(RESULTS_TEST_DIR)), 2)
            # converted image is in temp dir
        self.assertEqual(len(os.listdir(TEMP_TEST_DIR)), 1)
        self.assertIn('.jpg', os.listdir(TEMP_TEST_DIR)[0])
