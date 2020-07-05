import os
from PIL import Image
from . import file as file_utils


# walk throw the directory tree to find images.
# If file found is image but format not supported, convert it to jpg and save it to <directory_path_to_converted_files>
# Returns dict with { image file path : converted file path or None (not converted) }
def get_images_files(directory_path, directory_path_to_converted_files, supported_formats):
    
    images_paths = dict()
    
    for dirpath, dirnames, files in os.walk(directory_path):
        for file_name in files:
            file_path = os.path.abspath(os.path.join(dirpath, file_name))
            # try to get file as image
            image = get_pil_image(file_path)
            # if file is image
            if image is not None:
                #if image format not supported
                if image.format not in supported_formats:
                    # try to convert it to jpg and save it to temp dir
                    try:
                        converted_file_path = convert_pil_image_to_jpg(image, directory_path_to_converted_files)
                        images_paths[file_path] = converted_file_path
                    except:
                        # file is not supported and convertion failed, so ignore it
                        pass
                else:
                    images_paths[file_path] = None
                image.close()

    return images_paths

# try to get file as image
def get_pil_image(file_path):
    try:
        # try to open file as image
        return Image.open(file_path)
    except IOError:
        # not an image
        return None

# convert image to jpg, by PIL Image object
def convert_pil_image_to_jpg(image, dir_path):
    file_utils.create_directory_if_not_exists(dir_path)
    converted_file_path = os.path.join(dir_path, os.path.basename(image.filename) + '.jpg')
    image_converted = image.convert()
    image_converted.save(converted_file_path, 'jpeg')
    return converted_file_path