def insert_prefix_js():
    return """
    var dataSet = [
    """

def insert_object_js(img_link, img_original_link, img_name, original_path ,img_class, img_size, confidence):
    
    return """
        [
            "{imglink}",
            "{imgoriginallink}",
            "{imgfilename}",
            "{imgsize}",
            "{imgclass}",
            "{img_confidence}",
            "{img_original_path}"
        ],
    """.format(imglink = img_link, imgoriginallink = img_original_link, img_original_path = original_path, imgclass = img_class, img_confidence = confidence, imgfilename = img_name, imgsize = img_size)

def insert_suffix_js():
    return """
    ]
    """