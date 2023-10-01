# Import the necessary modules
from flask import Flask, request, jsonify, send_file, make_response
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
import mimetypes  # Import the mimetypes module

app = Flask(__name__)

load_dotenv()  # Load environment variables from .env
AZURE_STORAGE_ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
AZURE_STORAGE_ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

# Function to create a BlobServiceClient using your credentials
def create_blob_service_client():
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={AZURE_STORAGE_ACCOUNT_NAME};AccountKey={AZURE_STORAGE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
    return BlobServiceClient.from_connection_string(connection_string)

# Function to upload a file to Azure Blob Storage and get the link
def upload_file_and_get_link(file_data, file_name, container_name):
    try:
        blob_service_client = create_blob_service_client()
        container_client = blob_service_client.get_container_client(container_name)

        # Create the container if it doesn't exist
        if not container_client.exists():
            container_client.create_container()

        # Upload the file
        blob_client = container_client.get_blob_client(file_name)
        blob_client.upload_blob(file_data)

        # Get the public URL of the uploaded file
        blob_url = blob_client.url

        return blob_url
    except Exception as e:
        raise RuntimeError(f"Error uploading file: {str(e)}")

# Function to download a file from Azure Blob Storage
def download_from_blob_storage(container_name, file_name):
    try:
        blob_service_client = create_blob_service_client()
        container_client = blob_service_client.get_container_client(container_name)
        blob_client = container_client.get_blob_client(file_name)

        if blob_client.exists():
            blob_data = blob_client.download_blob()
            content_type, _ = mimetypes.guess_type(file_name)  # Determine content type based on file extension

            if content_type:
                response = make_response(blob_data.readall())
                response.headers["Content-Type"] = content_type
            else:
                # Default to application/octet-stream for unknown file types
                response = make_response(blob_data.readall())
                response.headers["Content-Type"] = "application/octet-stream"

            response.headers["Content-Disposition"] = f'attachment; filename="{file_name}"'
            return response
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Flask route to upload a file
@app.route('/upload', methods=['POST'])
def upload_file_and_get_link_route():
    try:
        # Get the file, container name, and file name from the request
        uploaded_file = request.files['file']
        if not uploaded_file:
            return jsonify({"error": "No file provided"}), 400

        container_name = request.form.get('container_name')
        file_name = request.form.get('file_name')

        if not container_name or not file_name:
            return jsonify({"error": "Container name and file name must be provided"}), 400

        # Upload the file to Azure Blob Storage and get the link
        blob_url = upload_file_and_get_link(uploaded_file.read(), file_name, container_name)

        return jsonify({"message": "File uploaded successfully", "blob_url": blob_url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Flask route to download a file
@app.route('/download', methods=['GET'])
def download_file_route():
    try:
        data = request.get_json()
        container_name = data.get('container_name')
        file_name = data.get('file_name')

        if not container_name or not file_name:
            return jsonify({"error": "Container name and file name must be provided"}), 400

        return download_from_blob_storage(container_name, file_name)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
