from flask import Flask, render_template, Response, request, redirect, url_for, jsonify
import cv2
import threading
import os
from datetime import datetime
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# Azure Blob Storage configuration
#connection_string = "DefaultEnxxxxxxxxxxxx"  # Replace with your Azure storage connection string
container_name = "video-uploads"  # Replace with your Azure Blob Storage container name
blob_service_client = BlobServiceClient.from_connection_string(connection_string)

# Global variables
video_stream = cv2.VideoCapture(0)
output_frame = None
lock = threading.Lock()
recording = False
paused = False
video_writer = None
video_filename = ""

def generate_frames():
    global output_frame, lock, video_writer, recording, paused

    while True:
        success, frame = video_stream.read()
        if not success:
            break

        with lock:
            output_frame = frame.copy()

            if recording and not paused:
                if video_writer is not None:
                    video_writer.write(frame)

        # Sleep for a short period to reduce CPU usage
        cv2.waitKey(1)

def encode_frame():
    global output_frame, lock

    while True:
        with lock:
            if output_frame is None:
                continue
            ret, buffer = cv2.imencode('.jpg', output_frame)
            frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(encode_frame(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/control', methods=['POST'])
def control():
    global recording, paused, video_writer, video_filename

    action = request.form.get('action')

    if action == 'record':
        if not recording:
            video_filename = f"recorded_stream_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            fps = 20.0
            frame_size = (int(video_stream.get(cv2.CAP_PROP_FRAME_WIDTH)),
                          int(video_stream.get(cv2.CAP_PROP_FRAME_HEIGHT)))
            video_writer = cv2.VideoWriter(video_filename, fourcc, fps, frame_size)
            recording = True
            paused = False
            return jsonify(status='Recording started')
        else:
            return jsonify(status='Already recording')

    elif action == 'pause_resume':
        if recording:
            paused = not paused
            status = 'Paused' if paused else 'Resumed'
            return jsonify(status=f'Recording {status}')
        else:
            return jsonify(status='Not recording')

    elif action == 'stop':
        if recording:
            recording = False
            paused = False
            if video_writer is not None:
                video_writer.release()
                video_writer = None
            # Start upload in a separate thread
            threading.Thread(target=upload_to_azure, args=(video_filename,)).start()
            return jsonify(status='Recording stopped and upload started')
        else:
            return jsonify(status='Not recording')

    else:
        return jsonify(status='Invalid action')

def upload_to_azure(file_name):
    blob_name = f"videos/{file_name}"
    container_client = blob_service_client.get_container_client(container_name)

    try:
        # Create the container if it does not exist
        container_client.create_container()
        print(f"Container '{container_name}' created.")
    except Exception as e:
        if "ContainerAlreadyExists" in str(e):
            print(f"Container '{container_name}' already exists.")
        else:
            print(f"Failed to create or access container '{container_name}': {e}")
            return

    blob_client = container_client.get_blob_client(blob=blob_name)

    try:
        with open(file_name, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        print(f"Successfully uploaded {file_name} to Azure Blob Storage as {blob_name}")
    except Exception as e:
        print(f"Failed to upload {file_name} to Azure: {e}")
    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"Local video file {file_name} deleted after upload.")

def start_background_tasks():
    # Start the frame generation thread
    t = threading.Thread(target=generate_frames)
    t.daemon = True
    t.start()

if __name__ == '__main__':
    start_background_tasks()
    app.run(host='0.0.0.0', port=5001, threaded=True)
