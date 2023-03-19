import cv2
import numpy as np
from flask import Flask, request, make_response

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

if __name__ == '__main__':
    app.run(debug=True)
