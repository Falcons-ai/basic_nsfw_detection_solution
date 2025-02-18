# Copyright @ 2025 FALCONS.AI

from flask import Flask, request, render_template, redirect, url_for, send_from_directory
import os
import time
import csv
from werkzeug.utils import secure_filename
from detect_nsfw import detect_nsfw
from datetime import datetime

# Initialize the Flask web application
app = Flask(__name__)

# Configuration constants
UPLOAD_FOLDER = "media"  # Directory for storing uploaded images
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}  # Allowed file extensions
NSFW_PREFIX = "nsfw_"  # Prefix for NSFW images
CAPTIONS_FILE = "captions.csv"  # CSV file to store image captions

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configure application
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # Limit uploads to 16MB

def init_captions_file():
    """
    Initialize the captions CSV file if it doesn't exist.
    Creates the file with headers if it's not present.
    """
    if not os.path.exists(CAPTIONS_FILE):
        with open(CAPTIONS_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'caption', 'timestamp'])

def load_captions():
    """
    Load all captions from the CSV file into a dictionary.
    
    Returns:
        dict: Dictionary mapping filenames to (caption, timestamp) tuples
    """
    captions = {}
    if os.path.exists(CAPTIONS_FILE):
        with open(CAPTIONS_FILE, 'r', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                captions[row['filename']] = (row['caption'], row['timestamp'])
    return captions

def save_image_caption(filename, caption):
    """
    Save or update image caption in the CSV file.
    
    Args:
        filename (str): Image filename
        caption (str): Image caption
    """
    captions = load_captions()
    captions[filename] = (caption, datetime.now().isoformat())
    
    with open(CAPTIONS_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['filename', 'caption', 'timestamp'])  # Write headers
        for fname, (cap, timestamp) in captions.items():
            writer.writerow([fname, cap, timestamp])

def get_image_caption(filename):
    """
    Retrieve image caption from the CSV file.
    
    Args:
        filename (str): Image filename
    
    Returns:
        tuple: (caption, timestamp) or ("", "") if not found
    """
    captions = load_captions()
    return captions.get(filename, ("", ""))

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_filename(filename, is_nsfw):
    """
    Process filename based on NSFW status.
    """
    if filename.startswith(NSFW_PREFIX):
        filename = filename[len(NSFW_PREFIX):]
    return f"{NSFW_PREFIX}{filename}" if is_nsfw else filename

def rename_file(old_path, new_path):
    """
    Safely rename a file.
    """
    try:
        os.rename(old_path, new_path)
        return True
    except Exception as e:
        print(f"Error renaming file: {e}")
        return False

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Main route handler for the application.
    """
    # Initialize captions file if it doesn't exist
    init_captions_file()

    if request.method == "POST":
        if "file" not in request.files:
            return redirect(request.url)

        file = request.files["file"]
        caption = request.form.get("caption", "").strip()

        if file.filename == "":
            return "No file selected", 400
        if not allowed_file(file.filename):
            return "Invalid file type", 400

        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config["UPLOAD_FOLDER"], f"temp_{filename}")

        try:
            # Save the uploaded file with temporary name
            file.save(temp_path)

            # Wait for file to be saved
            attempts = 10
            for _ in range(attempts):
                if os.path.exists(temp_path):
                    break
                time.sleep(0.1)

            # Perform NSFW detection
            nsfw_status = detect_nsfw(temp_path)
            is_nsfw = nsfw_status == "NSFW"

            # Process filename based on NSFW status
            final_filename = process_filename(filename, is_nsfw)
            final_path = os.path.join(app.config["UPLOAD_FOLDER"], final_filename)

            # Rename temporary file to final filename
            if rename_file(temp_path, final_path):
                # Save caption to CSV
                save_image_caption(final_filename, caption)
                return redirect(url_for("index"))
            else:
                return "Error processing upload", 500

        except Exception as e:
            print(f"Error processing upload: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return "Upload failed", 500

    # Handle GET request
    try:
        # Get list of images
        image_dir = app.config["UPLOAD_FOLDER"]
        images = [img for img in os.listdir(image_dir) 
                 if os.path.exists(os.path.join(image_dir, img))]

        # Sort images by creation time
        images.sort(
            key=lambda img: os.path.getctime(os.path.join(image_dir, img)),
            reverse=True
        )

        # Prepare feed data
        feed_data = []
        for img in images:
            if os.path.exists(os.path.join(image_dir, img)):
                caption, timestamp = get_image_caption(img)
                feed_data.append({
                    "url": f"/media/{img}",
                    "caption": caption,
                    "is_nsfw": img.startswith(NSFW_PREFIX),
                    "timestamp": timestamp or datetime.fromtimestamp(
                        os.path.getctime(os.path.join(image_dir, img))
                    ).isoformat()
                })

        return render_template("index.html", feed=feed_data)

    except Exception as e:
        print(f"Error preparing feed: {e}")
        return "Error loading feed", 500

@app.route("/media/<filename>")
def uploaded_file(filename):
    """
    Serve uploaded media files.
    """
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.errorhandler(413)
def too_large(e):
    """
    Handle file too large error.
    """
    return "File is too large", 413

if __name__ == "__main__":
    init_captions_file()  # Initialize captions CSV when starting the application
    app.run(debug=True, host='0.0.0.0', port=5000)
