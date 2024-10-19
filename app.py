from flask import Flask, request, jsonify, render_template
import cv2
from pyzbar.pyzbar import decode
import requests

app = Flask(__name__)

# Function to decode barcode
def scan_barcode(image_path):
    try:
        img = cv2.imread(image_path)
        if img is None:
            return "Error: Unable to read the image."
        
        barcodes = decode(img)
        if not barcodes:
            return "No barcodes found in the image."
        
        for barcode in barcodes:
            barcode_data = barcode.data.decode("utf-8")
            return barcode_data
    except Exception as e:
        return f"Error decoding barcode: {str(e)}"

# Function to fetch product details
def fetch_product_details(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    response = requests.get(url)
    if response.status_code == 200:
        product_data = response.json()
        if product_data['status'] == 1:
            return product_data['product']
        return "Product not found"
    return "Error fetching data"

# Route for the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle image upload and processing
@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file uploaded'}), 400
        
        file = request.files['file']
        file.save('uploaded_image.jpg')  # Save the image temporarily
        
        barcode = scan_barcode('uploaded_image.jpg')
        if barcode:
            product = fetch_product_details(barcode)
            if isinstance(product, dict):
                # Prepare data for chart and traffic light
                nutriments = product.get('nutriments', {})
                data = {
                    'status': 'success',
                    'barcode': barcode,
                    'product_name': product.get('product_name', 'N/A'),
                    'energy': nutriments.get('energy-kcal_100g', 0),
                    'fat': nutriments.get('fat_100g', 0),
                    'carbohydrates': nutriments.get('carbohydrates_100g', 0),
                    'sugars': nutriments.get('sugars_100g', 0),
                    'proteins': nutriments.get('proteins_100g', 0),
                    'traffic_light': {
                        'energy': get_traffic_light_color(nutriments.get('energy-kcal_100g', 0), 500, 250),
                        'fat': get_traffic_light_color(nutriments.get('fat_100g', 0), 17.5, 3),
                        'sugars': get_traffic_light_color(nutriments.get('sugars_100g', 0), 22.5, 5)
                    }
                }
                return jsonify(data)
            else:
                return jsonify({'status': 'error', 'message': product}), 400
        return jsonify({'status': 'error', 'message': 'No barcode found'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Traffic light function
def get_traffic_light_color(value, high, medium):
    if value >= high:
        return 'red'
    elif value >= medium:
        return 'yellow'
    else:
        return 'green'

if __name__ == '__main__':
    app.run(debug=True)
