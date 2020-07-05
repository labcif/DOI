import unittest
import unittest.mock
import doi
import utils.file as file_utils
import os
import io

"""
Integration tests about the feature: get supported classes for configuration
"""

class TestGetSupportedClasses(unittest.TestCase):
    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_get_supported_classes(self, mock_stdout):
        """
        Test that it prints the supported classes with no error, for all configurations
        """
        for config_choice in doi.CONFIG_CHOICES:
            # arrange
            class args: config = doi.set_config(config_choice)
            # act
            doi.get_supported_classes(args)
            # assert
            supported_classes = file_utils.read_file(args.config['classes_path'])
            print_output = mock_stdout.getvalue()
            for class_name in supported_classes:
                self.assertIn(class_name, print_output)

    def test_saves_json_with_supported_classes(self):
        """
        Test that it saves a json file with the supported classes
        """
        # delete json files with supported classes before perform the test
        file_utils.delete_all_files_in_dir_by_name(doi.RESULTS_DIR, '*' + doi.SUPPORTED_CLASSES_FILENAME)
        for config_choice in doi.CONFIG_CHOICES:
            # arrange
            class args: config = doi.set_config(config_choice)
            # act
            doi.get_supported_classes(args)
            # assert
            file_name = config_choice + '-' + doi.SUPPORTED_CLASSES_FILENAME
            self.assertTrue(os.path.isfile(os.path.join(doi.RESULTS_DIR, file_name)))