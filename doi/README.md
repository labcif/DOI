# DOI - Detection of Objects in Images

[DOI](https://github.com/labcif/DOI/) is an application that searches for images in a provided folder and detects objects in the images.

This is the stand alone application, in Python 3.

The main inputs are a directory, to search for images, and the object classes that you want to detect (see [Usage](#usage)).
The result is a json file with each class of objects selected and copies of the images with the objects detected surrounded by boxes.

This application was built in Python 3.7.

It only supports Windows (for now).

There are an ingest module and a report module to use this application in Autopsy. Check it out in this repository.

## Installation

* Install [Python version 3](https://www.python.org/downloads/) (tested in Python 3.7)
* Install [CUDA](https://developer.nvidia.com/cuda-downloads/) (optional, only with you have a compatible GPU)
* Run the command: `pip install numpy opencv-python pillow`
* Put weights files in folder `config/weights`. Download at least one from:
  * http://pjreddie.com/media/files/yolov3.weights (recomended, for `default` configuration)
  * http://pjreddie.com/media/files/yolov3-tiny.weights (for `tiny` configuration)
  * http://pjreddie.com/media/files/yolov3-openimages.weights (for `openimages` configuration)

## Usage

### Detector

Get the list of images with dogs and horses (-cls or --classes), from all the images in directory and sub-directories:

`python doi.py detect <directory_with_images> --classes dog horse`


Get the list of images with dogs and baseball bats, from all the images in directory and sub-directories ("baseball bat" has a space between, so you must use quotes):

`python doi.py detect <directory_with_images> --classes dog "baseball bat"`


Using other configuration (-c or --config):

`python doi.py --config tiny detect <directory_with_images> --classes dog horse`


Other options as CPU mode (-ng or --nogpu) and threshold of 0.25 (-t or --threshold):

`python doi.py --config tiny detect <directory_with_images> --classes dog horse --nogpu --threshold 0.25`


Using a json file as input for classes to search for (-clsf or --classesfile):

`python doi.py detect <directory_with_images> --classesfile <file_with_the_classes_to_search_for.json>`


Do not clean images in results directory, created in a previous detection (-nrc or --no-results-clean) (by default, it cleans the results directory before saving new files):

`python doi.py detect <directory_with_images> --classes dog horse --no-results-clean`


Disable saving images with the detections in results directory (-nout or --no-output-images):

`python doi.py detect <directory_with_images> --classes dog horse --no-output-images`


### Get supported classes

Get supported object classes (it will write a json file in results folder with the supported classes, that can be used as template for a json file with the classes to search for):

`python doi.py classes`


Get supported object classes for configuration (-c or --config):

`python doi.py --config tiny classes`


Example of a json file for indicating the classes to search for (detector will search for persons and dogs):
```json
{
    "person": true,
    "dog": true,
    "car": false
}
```

## About the detectors modules

### darknet

* `yolo_cpp_dll.dll` and `yolo_cpp_dll_nogpu.dll` compiled from https://github.com/AlexeyAB/darknet
* `pthreadGC2.dll` and `pthreadVC2.dll` from https://github.com/AlexeyAB/darknet/tree/master/build/darknet/x64
* `__init__.py` is the same as `darknet.py` from https://github.com/AlexeyAB/darknet/blob/master/darknet.py

### opencv

* Using opencv-python (dnn module), based on the example from https://github.com/arunponnusamy/object-detection-opencv

## To Build EXE

You can build the executable file of this application (or you can use the one that is with the Autopsy ingest module). With the EXE, there is no need to install Python or other dependencies, but the folder 'config' must be in same directory of the EXE file.

* Install pyinstaller: `pip install pyinstaller`
* In the main project directory, run the command: `pyinstaller doi.spec --distpath .`
* To execute the application in exe mode, the commands and options are the same, eg.: `doi detect <directory_with_images> --classes dog horse`

## Issues

* This application does not support directories with non-ASCII characters, due to its dependencies, namely OpenCV and Darknet.