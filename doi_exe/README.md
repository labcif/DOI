# DOI - Detection of Objects in Images

[DOI](https://github.com/labcif/DOI/) is an application that searches for images in a provided folder and detects objects in the images.

This is the executable version of DOI, built using the [Python version](../doi).

## Installation

* Copy the files in this folder
* Put weights files in folder `config/weights`. Download at least one from:
  * http://pjreddie.com/media/files/yolov3.weights (recomended, for `default` configuration)
  * http://pjreddie.com/media/files/yolov3-tiny.weights (for `tiny` configuration)
  * http://pjreddie.com/media/files/yolov3-openimages.weights (for `openimages` configuration)

## Usage

Check the documentation in the [Python version](../doi). The commands and options are the same, but instead of:

`python doi.py [...]`

Should be:

`doi [...]`