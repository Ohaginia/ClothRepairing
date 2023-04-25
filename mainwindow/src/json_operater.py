## -*- coding: utf-8 -*-

import json
import time

def update_json_data(file_path, new_data):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    for key, value in new_data.items():
        if key == "data":
            data[key].extend(value)
        else:
            data[key] = value
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

def load_json_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def clear_data_elements(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
    # Clear the data element
    data["data"] = []
    
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)