from flask import Flask, request, jsonify, send_from_directory, render_template
import cv2
import numpy as np
import requests
from pyzbar.pyzbar import decode

app = Flask(__name__)

# Serve index.html from the root directory
@app.route('/')
def index():
    return render_template('index.html')  # Render the HTML file

# Function to get traffic light color for nutritional values
def get_traffic_light_color(value, high_threshold, medium_threshold):
    if value > high_threshold:
        return 'red'
    elif value > medium_threshold:
        return 'yellow'
    else:
        return 'green'

# Function to fetch product details from Open Food Facts
def fetch_product_details(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            product_data = response.json()
            if product_data['status'] == 1:
                return product_data['product']
            return None
        return None
    except requests.exceptions.RequestException:
        return None

# Route to handle image upload and processing
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file uploaded.'})

    file = request.files['file']
    if not file:
        return jsonify({'status': 'error', 'message': 'No file uploaded.'})

    # Read the image using OpenCV
    in_memory_file = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(in_memory_file, cv2.IMREAD_COLOR)

    # Decode the barcode
    barcodes = decode(image)
    if not barcodes:
        return jsonify({'status': 'error', 'message': 'No barcode found.'})

    barcode_data = barcodes[0].data.decode('utf-8')
    product_details = fetch_product_details(barcode_data)

    if not product_details:
        return jsonify({'status': 'error', 'message': 'Product not found in the database.'})

    # Extract relevant product information
    nutritional_info = product_details.get('nutriments', {})
    response_data = {
        'status': 'success',
        'barcode': barcode_data,
        'product_name': product_details.get('product_name', 'Unknown'),
        'energy': nutritional_info.get('energy-kcal', 0),
        'fat': nutritional_info.get('fat', 0),
        'carbohydrates': nutritional_info.get('carbohydrates', 0),
        'sugars': nutritional_info.get('sugars', 0),
        'proteins': nutritional_info.get('proteins', 0),
        'traffic_light': {
            'energy': get_traffic_light_color(nutritional_info.get('energy-kcal', 0), 400, 200),
            'fat': get_traffic_light_color(nutritional_info.get('fat', 0), 20, 10),
            'sugars': get_traffic_light_color(nutritional_info.get('sugars', 0), 10, 5),
        }
    }

    return jsonify(response_data)

# Static file serving for CSS
@app.route('/styles.css')
def styles():
    return send_from_directory('', 'styles.css')

if __name__ == '__main__':
    app.run(debug=True, port=8000)  # Change the port to 8000 (or your desired port)
