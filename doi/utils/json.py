import json

# read json file and return its data
def read_file(file_path):
    with open(file_path) as json_file:
        data = get_data(json_file)
        return data

# get data from a opened json file
def get_data(json_file):
    data = json.load(json_file)
    return data

# write data to a json file
def write_file(file_path, data):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

# print data as json format
def print_as_json(data, indent=4):
    print(json.dumps(data, indent=indent))