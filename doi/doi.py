# import required packages
import argparse
import sys
import os
import shutil
import utils.json as json_utils
import utils.file as file_utils
import utils.image as image_utils
import utils.list as list_utils
from core.object_detector import ObjectDetector
from core.detections_handler import DetectionsHandler

# constants
if getattr(sys, 'frozen', False):
    # we are running in a bundle (created by pyinstaller)
    WORKING_DIR = os.path.dirname(sys.executable)
else:
    # we are running in a normal Python environment
    WORKING_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(WORKING_DIR, 'config')
RESULTS_DIR = os.path.join(WORKING_DIR, 'results')
RESULTS_FILENAME = 'results.json'
SUPPORTED_CLASSES_FILENAME = 'supported-classes.json'
CONFIG_CHOICES = ['default', 'tiny', 'openimages', 'custom']
TEMP_DIR = os.path.join(WORKING_DIR, 'temp')
# image formats as named by PIL
SUPPORTED_FORMATS = ['JPEG', 'PNG', 'BMP', 'PPM']
# formats also supported (because we convert them to JPEG):
# DIB, GIF, JPEG2000, PCX, PPM, PBM, SUN, SGI, TGA, TIFF, WEBP, XBM

# type function for argparse: a float within 0.1-0.99
def range_limited_float_type(arg):
    try:
        f = float(arg)
    except ValueError:    
        raise argparse.ArgumentTypeError('Must be a floating point number')
    if f < 0.1 or f > 0.99:
        raise argparse.ArgumentTypeError('Argument must be between ' + str(0.1) + ' and ' + str(0.99))
    return f

# type function for argparse: read a config file
def set_config(arg):
    if arg not in CONFIG_CHOICES:
         raise argparse.ArgumentTypeError(f'invalid choice: {arg} (choose from {CONFIG_CHOICES})')
    try:
        filename = 'config-' + arg + '.json'
        config_filepath = os.path.join(CONFIG_DIR, filename)
        # get configuration from json config file
        config = json_utils.read_file(config_filepath)
        # parse the paths
        for config_name, config_value in config.items():
            if 'path' in config_name:
                config[config_name] = os.path.join(WORKING_DIR, config_value)
        # add name to config file
        config['config_name'] = arg
    except:
        raise argparse.ArgumentTypeError('Config file not found or is invalid: ' + config_filepath)
    return config


########## sub-command function to detect objects in images ##########
def detect(args):
    # remove temporary directory
    file_utils.remove_dir_if_exists(TEMP_DIR)
    # create results dir
    file_utils.create_directory_if_not_exists(RESULTS_DIR)
    
    # check if provided directory exists
    if not os.path.isdir(args.dir):
        arg_parser.error('invalid directory path: ' + os.path.abspath(args.dir))

    # check if provided classes are supported
    supported_classes = file_utils.read_file(args.config['classes_path'])
    classes_to_search_for = get_classes_to_search_for(args)
    classes_not_in_supported = list_utils.list_items_not_in_another_list(classes_to_search_for, supported_classes)
    if classes_not_in_supported:
        arg_parser.error('Object classes not supported: ' + ', '.join(classes_not_in_supported))
    if not classes_to_search_for:
        arg_parser.error('No classes selected')

    # get all the images (file paths) that exists in directory (and converted to jpg version, if format not supported)
    print('Collecting all the images files from', os.path.abspath(args.dir), '...')
    images = image_utils.get_images_files(args.dir, TEMP_DIR, SUPPORTED_FORMATS)
    if not any(images):
        print('No images found.')
        exit()
    print(f'Done (found {len(images)} images).')

    # configure core modules
    object_detector = ObjectDetector(args.config, args.threshold, not args.nogpu, WORKING_DIR)
    detections_handler = DetectionsHandler(classes_to_search_for, supported_classes, RESULTS_DIR, not args.no_results_clean)

    # apply object detection for each image (or converted version, in case format not supported)
    print('Applying object detection for each image found...')
    for image, converted_image in images.items():
        detections = object_detector.apply_object_detection(converted_image if converted_image is not None else image)
        if detections is None:
            continue
        print(os.path.abspath(image), f'(found {len(detections)} objects).')
        # process detections found
        detections_handler.handle_detections(image, detections, not args.no_output_images)
        # saving the results in order to not loose information in case of something wrong
        save_results(detections_handler.objects_images_dict)

    # output the results
    print('End of object detetion for all images.')
    output_results(detections_handler.objects_images_dict, args.no_output_images)

# get the classes the user choose to search for in images
def get_classes_to_search_for(args): 
    # get classes from args
    if args.classes is not None:
        # user input classes to search for
        return args.classes
    # get the classes from a file
    try:
        # get the classes to search for from the provided json file (as dict)
        classes_to_search_for_dict = json_utils.get_data(args.classesfile)
        if not isinstance(classes_to_search_for_dict, dict):
            raise ValueError
    except:
        arg_parser.error('Error reading classes to search for from file ' + os.path.abspath(args.classesfile.name))
    # convert dict to list (where the values == true)
    return [class_name for class_name, value in classes_to_search_for_dict.items() if value is True]

# print results
def output_results(results, no_output_images):
    print('Results:')
    json_utils.print_as_json(results)
    results_file_path = os.path.join(RESULTS_DIR, RESULTS_FILENAME)
    print('Results saved to', os.path.abspath(results_file_path) + '.')
    if not no_output_images:
        print('Images with detected objects saved to', os.path.abspath(RESULTS_DIR) + '.')

# save results to json file
def save_results(results):
    file_utils.create_directory_if_not_exists(RESULTS_DIR)
    json_utils.write_file(os.path.join(RESULTS_DIR, RESULTS_FILENAME), results)


########## Sub-command function to get supported classes ##########
def get_supported_classes(args):
    # create results dir
    file_utils.create_directory_if_not_exists(RESULTS_DIR)
    # get supported classes
    supported_classes = file_utils.read_file(args.config['classes_path'])
    # sort the list
    supported_classes.sort()
    # output
    print('Supported classes:')
    print('\n'.join(supported_classes))
    # Convert to dict and then save to json
    dict_supported_classes = { class_name : True for class_name in supported_classes }
    file_name = f"{args.config['config_name']}-{SUPPORTED_CLASSES_FILENAME}"
    json_utils.write_file(os.path.join(RESULTS_DIR, file_name), dict_supported_classes)


########## Start application ##########
if __name__ == '__main__':
    # handle command line arguments
    arg_parser = argparse.ArgumentParser(description='DOI: Detection of Objets in Images')
    # common argument
    arg_parser.add_argument('-c', '--config', required=False,
                    help='Configuration for DOI',
                    metavar='{' + ','.join(CONFIG_CHOICES) + '}',
                    default='default',
                    type=set_config)
    arg_parser.add_argument('-rd', '--resultsdir', required=False,
                    help='Path where DOI will write results',
                    default=RESULTS_DIR)
    # create sub-commands
    subparsers = arg_parser.add_subparsers(help='sub-command help')
    detect_parser = subparsers.add_parser('detect', 
                    help='Detect objects in images present in provided directory')
    classes_parser = subparsers.add_parser('classes', 
                    help='Show a list of suported object classes (depends on configuration)')
    # arguments for 'detect' sub-command
    detect_parser.add_argument('dir', help='directory where are images to process')
    classes_group = detect_parser.add_mutually_exclusive_group(required=True)
    classes_group.add_argument('-cls', '--classes',  nargs='+',
                    help='List of objects classes to search for (eg. "dog horse car")')
    classes_group.add_argument('-clsf', '--classesfile',
                    help='Json file with the classes to search for (similiar to the one that "classes" command writes)',
                    type=open)
    detect_parser.add_argument('-ng', '--nogpu', action='store_true',
                    help='Force cpu processing mode')
    detect_parser.add_argument('-t', '--threshold', required=False,
                    help='The detection confidence threshold (default: 0.5)',
                    metavar='[0.1-0.99]', default=0.5,
                    type=range_limited_float_type)
    detect_parser.add_argument('-nout', '--no-output-images', action='store_true',
                    help='Disable creating images with detections on results folder')
    detect_parser.add_argument('-nrc', '--no-results-clean', action='store_true',
                    help='Do not clean previous images with detections on results folder (with --no-output-images option, this has no effect)')
    detect_parser.set_defaults(func=detect)
    # arguments for classes sub-command
    classes_parser.set_defaults(func=get_supported_classes)

    # Parse arguments or print error
    args = None
    try:
        args = arg_parser.parse_args()
    except IOError as msg:
        arg_parser.error(str(msg))

    # Check if needed files exists (files refered in config files)
    for key in args.config:
        if 'path' in key:
            if not os.path.exists(args.config[key]):
                arg_parser.error('Invalid file path ' + os.path.abspath(args.config[key]) + ' (refered in config file)')

    # set the path to the results
    RESULTS_DIR = args.resultsdir

    # Execute the selected sub-command (functions in the top of the file)
    # If no command selected (it is parsed to args.func), launch help
    if not getattr(args, 'func', False):
        arg_parser.print_help()
        sys.exit()
    args.func(args)