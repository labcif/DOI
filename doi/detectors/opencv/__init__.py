# import required packages
import cv2
import argparse
import numpy as np


# cache for classes names
classes = None

# function to get the output layer names
# in the architecture
def _get_output_layers(net):

    layer_names = net.getLayerNames()

    output_layers = [layer_names[i[0] - 1]
                     for i in net.getUnconnectedOutLayers()]

    return output_layers


# Detect objects in provided image, with the provided parameters
def performDetect(imagePath, thresh, configPath, weightPath, metaPath):

    # read input image
    image = cv2.imread(imagePath)
    if image is None:
        return None
    Width = image.shape[1]
    Height = image.shape[0]
    scale = 0.00392

    global classes
    if classes is None:
        # read class names from text file
        with open(metaPath, 'r') as f:
            classes = [line.strip() for line in f.readlines()]

    # read pre-trained model and config file
    net = cv2.dnn.readNet(weightPath, configPath)

    # create input blob
    blob = cv2.dnn.blobFromImage(
        image, scale, (416, 416), (0, 0, 0), True, crop=False)

    # set input blob for the network
    net.setInput(blob)

    # run inference through the network
    # and gather predictions from output layers
    outs = net.forward(_get_output_layers(net))

    # initialization
    class_ids = []
    confidences = []
    boxes = []
    conf_threshold = thresh
    nms_threshold = 0.45

    # for each detetion from each output layer
    # get the confidence, class id, bounding box params
    # and ignore weak detections (confidence < e.g. 0.5)
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > conf_threshold:
                center_x = detection[0] * Width
                center_y = detection[1] * Height
                w = detection[2] * Width
                h = detection[3] * Height
                class_ids.append(class_id)
                confidences.append(float(confidence))
                boxes.append([center_x, center_y, w, h])

    # apply non-max suppression
    indices = cv2.dnn.NMSBoxes(boxes, confidences, conf_threshold, nms_threshold)

    # go through the detections remaining after nms
    results = []

    for i in indices:
        i = i[0]
        box = boxes[i]
        x = box[0]
        y = box[1]
        w = box[2]
        h = box[3]

        label = classes[class_ids[i]]
        results.append((label, confidences[i], (x, y, w, h)))

    return results
