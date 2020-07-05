# DOI - Detection of Objects in Images

**DOI** is an application that searches for images in a provided folder and detects objects in the images.

It uses the [YOLOV3](https://pjreddie.com/darknet/yolo/) system. It works on GPU with CUDA support, using [Darknet For Windows](https://github.com/AlexeyAB/darknet). On CPU, the application uses the DNN module of [OpenCV](https://pypi.org/project/opencv-python/).

This application was built in Python 3.7.

It only supports Windows (for now).

## Usage

### As stand alone application

This application can be used as a stand alone application. There are two versions:

* Python version: check it out [here](./doi)
* Executable version: check it out [here]./doi_exe)

The executable version does not need instalation.

### In Autopsy

In order to integrate **DOI** with [Autopsy](https://www.autopsy.com/), there are two modules:

 * [DOI Data source ingest module](./doi_autopsy_modules/doi_ingest): uses the DOI stand alone application in order to detect objects in images
 * [DOI Report module](./doi_autopsy_modules/doi_ingest): exports a HTML report with the results of the ingest module

## Supported image file formats

BMP, DIB, GIF, JPEG, JPEG2000, PBM, PCX, PNG, PPM, SGI, SUN, TGA, TIFF, WEBP and XBM.

## Authors

* Mihail Stratan (Instituto Politécnico de Leiria - Portugal)
* Paulo Martinho (Instituto Politécnico de Leiria - Portugal)

## Mentors

* Patrício Domingues (Instituto Politécnico de Leiria - Portugal)
* Miguel Frade (Instituto Politécnico de Leiria - Portugal)