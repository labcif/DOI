import os
import utils.file as file_utils
import cv2
import numpy as np

class DetectionsHandler:
    
    objects_images_dict = dict()
    _classes_colors_dict = dict()
    _results_dir = 'results'
    _file_counter = 0

    def __init__(self, classes_to_search, supported_classes, results_dir, clean_results_dir=True):
        # initialize dictionary of results: <class name, new list>
        self.objects_images_dict = dict()
        for class_name in classes_to_search:
            self.objects_images_dict[class_name] = list()
        self._results_dir = results_dir
        self._set_colors_for_classes(supported_classes)
        # delete all the image files created previously in results directory
        if clean_results_dir:
            file_utils.delete_all_files_in_dir_by_name(self._results_dir, '*_results*.jpg')

    # get dict<class name, list of images with that object class> from detections
    def handle_detections(self, image, detections, create_image_with_detections=True):
        image_abs_path = os.path.abspath(image).replace('\\', '/')
        image_with_results = None

        for class_name, confidence, localization in detections:
            # check if class detected is in classes to search for
            if class_name in self.objects_images_dict:
                # check if image is already in the class list of images (same image can have several objects of same class)
                image_already_inserted_in_class = False
                for result_dict in self.objects_images_dict[class_name]:
                    # if image already inserted: only update the confidence
                    if image_abs_path == result_dict['image']:
                        image_already_inserted_in_class = True
                        # set the best confidence found for the class in image 
                        if result_dict['bestConfidence'] < confidence:
                            result_dict['bestConfidence'] = confidence
                        break
                # if the image is new for this class, insert it in the class list of images
                if not image_already_inserted_in_class:
                    # draw the image with results if not already drawn (only draw once for this image, all the detections)
                    if create_image_with_detections and image_with_results is None:
                        image_with_results = self._draw_detection(image_abs_path, detections)
                    self.objects_images_dict[class_name].append({'image': image_abs_path, 'imageWithResults': image_with_results, 'bestConfidence': round(confidence, 4)})

    # function to draw bounding box on the detected object with class name
    def _draw_detection(self, image_path, detections):
        # read from original image
        image = cv2.imread(image_path)
        if image is None or image.size == 0: # error reading the file
            return None
        
        for class_name, confidence, localization in detections:
            center_x, center_y, width, height = localization
            start_x = int(round(center_x - width/2))
            end_x = int(round(center_x - width/2 + width))
            start_y = int(round(center_y - height/2))
            end_y = int(round(center_y - height/2 + height))
            color = self._classes_colors_dict[class_name]

            # draw the retangle in image
            cv2.rectangle(image, (start_x, start_y), (end_x, end_y), color, 2)
            # draw the label+confidence on top of retangle
            cv2.putText(image, class_name + ' (' + str(round(confidence, 4)) + ')', (start_x - 10, start_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # save output image to disk
        result_file_name = self._get_result_filename(image_path)
        result_file_path = os.path.join(self._results_dir, result_file_name)
        cv2.imwrite(result_file_path, image)
        return result_file_path.replace('\\', '/')

    # generate different colors for different classes (used when drawing detections in image)
    def _set_colors_for_classes(self, supported_classes):
        colors = np.random.uniform(0, 255, size=(len(supported_classes), 3))
        self._classes_colors_dict = { class_name : colors[i] for i, class_name in enumerate(supported_classes) }
    
    # get a unique filename for a detections result, from original file name
    def _get_result_filename(self, original_file_path):
        result_filename = os.path.basename(original_file_path) + '_results_' + str(self._file_counter) + '.jpg'
        self._file_counter += 1
        return result_filename
