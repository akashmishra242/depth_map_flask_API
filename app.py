import cv2
import numpy as np
from flask import Flask, request, make_response, jsonify
import requests
from io import BytesIO
import os
from azure_blob_functions import upload_file_and_get_link, download_from_blob_storage

app = Flask(__name__)

@app.route('/')
def welcome():
    return 'Welcome to the Depth Map API!'

@app.route('/depth-map', methods=['POST'])
def create_depth_map():
    # Retrieve the two image files from the request
    image1 = request.files['image1']
    image2 = request.files['image2']

    # Prompt the user to input values for numDisparities and blockSize
    numDisparities = int(request.form.get('numDisparities', 16))
    blockSize = int(request.form.get('blockSize', 15))

    # Convert the images to grayscale
    img1 = cv2.imdecode(np.fromstring(image1.read(), np.uint8), cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imdecode(np.fromstring(image2.read(), np.uint8), cv2.IMREAD_GRAYSCALE)

    # Compute the depth map using OpenCV's StereoBM
    stereo = cv2.StereoBM_create(numDisparities=numDisparities, blockSize=blockSize)
    depth = stereo.compute(img1, img2)

    # Convert the depth map to a PNG image
    depth_png = cv2.imencode('.png', depth)[1]

    # Return the depth map as a response
    response = make_response(depth_png.tobytes())
    response.headers.set('Content-Type', 'image/png')
    response.headers.set('Content-Disposition', 'attachment', filename='depth_map.png')
    return response

@app.route('/azure-blob-depth-map', methods=['POST'])
def create_azure_blob_depth_map():
    # Retrieve the image URLs from the request
    left_image_url = request.form.get('left_image_url')
    right_image_url = request.form.get('right_image_url')

    # Prompt the user to input values for numDisparities and blockSize
    numDisparities = int(request.form.get('numDisparities', 16))
    blockSize = int(request.form.get('blockSize', 15))

    # Download the images from the URLs
    left_image_response = requests.get(left_image_url)
    right_image_response = requests.get(right_image_url)

    if left_image_response.status_code != 200 or right_image_response.status_code != 200:
        return "Failed to fetch images from the provided URLs", 400

    # Read the images and convert them to grayscale
    img1 = cv2.imdecode(np.frombuffer(left_image_response.content, np.uint8), cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imdecode(np.frombuffer(right_image_response.content, np.uint8), cv2.IMREAD_GRAYSCALE)

    # Compute the depth map using OpenCV's StereoBM
    stereo = cv2.StereoBM_create(numDisparities=numDisparities, blockSize=blockSize)
    depth = stereo.compute(img1, img2)

    # Convert the depth map to a PNG image
    depth_png = cv2.imencode('.png', depth)[1]

    # Return the depth map as a response
    response = make_response(depth_png.tobytes())
    response.headers.set('Content-Type', 'image/png')
    response.headers.set('Content-Disposition', 'attachment', filename='depth_map.png')
    return response


# Flask route to compute and upload a depth map
@app.route('/compute-and-upload-fetch-depth-map', methods=['POST'])
def compute_and_upload_depth_map_route():
    # Retrieve the image URLs from the request
    left_image_url = request.form.get('left_image_url')
    right_image_url = request.form.get('right_image_url')

    # Prompt the user to input values for numDisparities and blockSize
    numDisparities = int(request.form.get('numDisparities', 16))
    blockSize = int(request.form.get('blockSize', 15))
    
    #get container name and the file name which be want to keep
    container_name = request.form.get('container_name')
    file_name = request.form.get('file_name')
    firstname_name, extension = os.path.splitext(file_name)
    if not extension:
     file_name += ".png"

    # Download the images from the URLs
    left_image_response = requests.get(left_image_url)
    right_image_response = requests.get(right_image_url)

    if left_image_response.status_code != 200 or right_image_response.status_code != 200:
        return "Failed to fetch images from the provided URLs", 400

    # Read the images and convert them to grayscale
    img1 = cv2.imdecode(np.frombuffer(left_image_response.content, np.uint8), cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imdecode(np.frombuffer(right_image_response.content, np.uint8), cv2.IMREAD_GRAYSCALE)

    # Compute the depth map using OpenCV's StereoBM
    stereo = cv2.StereoBM_create(numDisparities=numDisparities, blockSize=blockSize)
    depth = stereo.compute(img1, img2)

    # Convert the depth map to a PNG image
    depth_png = cv2.imencode('.png', depth)[1]
    
    #upload depth_map_and get link
    try:
     blob_url= upload_file_and_get_link(depth_png.tobytes(), file_name=file_name, container_name=container_name)
    
    #response
     return jsonify({"message": "Depth-Map Created Uploaded and Link Created Successfully", "blob_url": blob_url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

if __name__ == '__main__':
    app.run(debug=True)