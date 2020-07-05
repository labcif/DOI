import unittest
import doi
import argparse

"""
Unit tests about the main component
"""

TEST_FILES_DIR = 'tests/unit/test_files/'
TEST_CONFIG_DIR = 'tests/unit/test_files/config/'

class TestThresholdInput(unittest.TestCase):
    def test_valid_numbers(self):
        """
        Test that it can parse a valid number for threshold ([0.1-0.99])
        """
        # arrange
        data = ['0.1', '0.5', '0.89999999', '0.99']
        for input in data:
            # act
            result = doi.range_limited_float_type(input)      
            # assert
            self.assertEqual(result, float(input))

    def test_invalid_inputs(self):
        """
        Test that it raises ArgumentTypeError on inputs that are not numbers for threshold ([0.1-0.99])
        """
        # arrange
        data = ['0,1', 'xyz']
        # act and assert
        for input in data:
            with self.assertRaises(argparse.ArgumentTypeError) as cm:
                result = doi.range_limited_float_type(input)
            self.assertIn('Must be a floating point number', str(cm.exception))

    def test_invalid_numbers(self):
        """
        Test that it raises ArgumentTypeError on invalid numbers for threshold ([0.1-0.99])
        """
        # arrange
        data = ['-0.1', '0.09', '0.991']
        # act and assert
        for input in data:
            with self.assertRaises(argparse.ArgumentTypeError) as cm:
                result = doi.range_limited_float_type(input)
            self.assertIn('must be between 0.1 and 0.99', str(cm.exception))


class TestConfigurationInput(unittest.TestCase):
    original_choices = []

    def setUp(self):
        doi.CONFIG_DIR = TEST_CONFIG_DIR
        # copy this list because it will be changed
        self.original_choices = list(doi.CONFIG_CHOICES)

    def tearDown(self):
        # restore the list
        doi.CONFIG_CHOICES = self.original_choices
    
    def test_valid_configurations(self):
        """
        Test that it can get the configuration files
        """
        # arrange
        data = doi.CONFIG_CHOICES
        for input in data:
            # act
            result = doi.set_config(input)
            # assert
            self.assertIsInstance(result, dict)
            print(result)
            self.assertIs(result['config_name'], input)

    def test_invalid_configuration_name(self):
        """
        Test that it raises ArgumentTypeError on invalid configuration
        """
        # arrange
        data = 'invalid_configuration'
        # act and assert
        with self.assertRaises(argparse.ArgumentTypeError) as cm:
            result = doi.set_config(data)
        self.assertIn('invalid choice', str(cm.exception))

    def test_valid_configuration_but_file_not_present(self):
        """
        Test that it raises ArgumentTypeError on valid configuration but file not present
        """
        # arrange
        data = 'valid_config_but_with_no_file'
        doi.CONFIG_CHOICES.append(data)
        # act and assert
        with self.assertRaises(argparse.ArgumentTypeError) as cm:
            result = doi.set_config(data)
        self.assertIn('Config file not found', str(cm.exception))


class TestParsingTheClassesToSearchFor(unittest.TestCase):
    def test_set_classes_by_args(self):
        """
        Test that it sets the selected classes, provided in arguments
        """
        # arrange
        class args: classes = ['dog', 'car']
        # act
        result = doi.get_classes_to_search_for(args)
        # assert
        self.assertIs(result, args.classes)

    def test_set_classes_by_file(self):
        """
        Test that it sets the selected classes, provided by a json file
        """
        # arrange
        with open(TEST_FILES_DIR + 'test_set_classes_file.json') as valid_classes_file:
            class args: classes = None; classesfile = valid_classes_file
            # act
            result = doi.get_classes_to_search_for(args)
            # assert
            self.assertIn('dog', result)
            self.assertNotIn('car', result)
            self.assertIn('horse', result)

    def test_set_classes_with_invalid_file(self):
        """
        Test that it exits when no classes and provided file is invalid
        """
        # arrange
        for file_number in range(3):
            with open(TEST_FILES_DIR + 'test_set_classes_invalid_file' + str(file_number) + '.json') as invalid_classes_file:
                class args: classes = None; classesfile = invalid_classes_file
                # act and assert
                with self.assertRaises(SystemExit):
                    result = doi.get_classes_to_search_for(args)

    def test_set_classes_with_valid_file_but_wrong_syntax(self):
        """
        Test that when it reads a valid json file, but with incorrect syntax, it has no classes selected
        """
        # arrange
        with open(TEST_FILES_DIR + 'test_set_classes_valid_file_wrong_syntax.json') as invalid_classes_file:
            class args: classes = None; classesfile = invalid_classes_file
            # act
            result = doi.get_classes_to_search_for(args)
            # assert
            self.assertEqual(len(result), 0)

    def test_set_classes_with_no_file_and_no_classes_in_args(self):
        """
        Test that it raises AttributeError when no classes and no file provided in arguments
        """
        # arrange
        class args: classes = None; classesfile = None
        # act and assert
        with self.assertRaises(AttributeError):
            result = doi.get_classes_to_search_for(args)




