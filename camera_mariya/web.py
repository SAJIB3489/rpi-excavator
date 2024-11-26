from flask import Flask, Response
import cv2
import os
import signal
from azure.storage.blob import BlobServiceClient
from datetime import datetime

app = Flask(__name__)

# Azure Blob Storage configuration
connection_string = "DefaultEndpointsProtocol=https;AccountName=iotprojectcamera;AccountKey=ehHx9Ci++fd5dk23WvK74SUeYFsCO9BNEe62wHJVsPCR0z2V3PHJVIIx0LlCVWlh1KgBZ9GdPldx+AStz4vuFg==;EndpointSuffix=core.windows.net"  # Replace with your Azure storage connection string
container_name = "video-uploads"  # Replace with your Azure Blob Storage container name
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Variable to track streaming status and filename
is_streaming = False
exit_signal_received = False
video_filename = ""  # Global variable to keep track of the current video filename

# Function to generate a unique video file name based on the current timestamp
def get_video_filename():
    return f"recorded_stream_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

def record_and_stream():
    global is_streaming, video_filename
    video_filename = get_video_filename()  # Get a unique file name for each recording
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open the camera.")
        raise RuntimeError("Error: Could not open the camera.")
    
    print("Camera opened successfully. Starting recording and streaming...")
    print(f"Recording video to {video_filename}")

    # Define video codec and create VideoWriter object to save the stream locally
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_filename, fourcc, 20.0, (640, 480))

    is_streaming = True

    try:
        while is_streaming:
            success, frame = cap.read()
            if not success:
                print("Error: Failed to capture frame.")
                break

            # Write the frame to the video file
            out.write(frame)

            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()

            # Yield the output frame in byte format for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        cap.release()
        out.release()
        print("Recording stopped. Attempting to upload video to Azure Blob Storage...")
        upload_to_azure(video_filename)

def upload_to_azure(file_name):
    blob_name = f"videos/{file_name}"  # Use the same unique name for the blob
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
    
    try:
        with open(file_name, "rb") as data:
            blob_client.upload_blob(data)
        print(f"Successfully uploaded {file_name} to Azure Blob Storage as {blob_name}")
    except Exception as e:
        print(f"Failed to upload {file_name} to Azure: {e}")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"Local video file {file_name} deleted after upload.")

@app.route('/')
def index():
    return "Welcome to the Webcam Live Stream. Go to /video_feed to view the stream."

@app.route('/video_feed')
def video_feed():
    print("Video feed endpoint accessed. Starting live stream...")
    return Response(record_and_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

def handle_exit(*args):
    global is_streaming, exit_signal_received, video_filename
    if not exit_signal_received:  # Prevent multiple calls
        print("Exit signal received. Stopping stream and uploading...")
        exit_signal_received = True
        is_streaming = False  # Stop streaming
        # Call the upload function with the current video filename only once
        if video_filename:
            upload_to_azure(video_filename)
        print("Upload completed. Exiting program.")
        os._exit(0)  # Directly exit the process after upload completes

# Register signal handler for graceful shutdown
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5000)
