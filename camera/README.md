### Docker

Build the image
```
sudo docker build --no-cache -t camera_app .
```

Create container

```
sudo docker run -it --restart=always -d --name camera \
  --device /dev/gpiomem \
  --device /dev/ttyUSB0 \
  --device /dev/ttyUSB1 \
  --device /dev/video0 \
  camera_app:latest
  ```
![image4](/attachment/camera.png)



## Webcam Streaming and Recording with Flask and Azure Blob Storage

This Python application uses Flask to create a web-based interface for streaming live video from a webcam, recording it, and saving the recorded footage to Azure Blob Storage. Users can view the live feed, start/pause/resume/stop recording, and automatically upload videos to the cloud when recording is complete.

### Prerequisites
Before running the script, ensure you have the following:

**Hardware:**
**Webcam:** Any standard USB or built-in camera.
**Device:** Raspberry Pi or any machine with Python 3.x support.
**Azure Setup:**
An Azure Blob Storage account and a container to store video files.
**Python Libraries:**
The script relies on these Python libraries:

**Flask:** To create the web interface.
**OpenCV:** For video capture and frame processing.
**Azure Storage Blob:** For uploading videos to Azure.

## How the Code Works
**Live Streaming:**
The generate_frames function continuously captures frames from the webcam and streams them to a web page using Flask’s /video_feed route.

**Recording:**
**Start Recording:** When the "Record" action is triggered, the script initializes a cv2.VideoWriter to save the video locally in MP4 format.
**Pause/Resume:** Temporarily pauses or resumes writing frames to the video file.
**Stop Recording:** Stops recording and starts a background thread to upload the video file to Azure Blob Storage.
**Azure Blob Upload:**
After recording stops, the video file is uploaded to Azure using the BlobServiceClient. The local file is deleted after successful upload to free up space.

## How it Works

**Set Up Azure Storage:**

Created a container named video-uploads in Azure Blob Storage.
Updated the connection string in the script with my Azure credentials.
**Tested Webcam:**

Verified that OpenCV was capturing video frames correctly using cv2.VideoCapture(0).
**Web Interface:**

Designed a simple HTML interface using Flask to stream the webcam feed and add recording controls.
**Azure Upload Configuration:**

Ensured the Azure Blob Storage library was correctly configured and tested uploads with sample files.
**Key Features**
1. Live Video Streaming
Visit http://ip_address:5001/ to view the live video feed.

**2. Recording Controls**
The web interface provides the following actions:

**Record:** Start recording the live video feed.
**Pause/Resume:** Pause or resume recording without stopping the feed.
**Stop:** Stop recording and upload the video to Azure.
**3. Automatic Azure Upload**
Once recording stops, the video file is automatically uploaded to Azure Blob Storage under the video-uploads container.

**How the Data is Handled**
**Live Frames:** Frames are streamed to the browser using Flask’s Response object in MJPEG format.
**Recording: **Frames are written to an MP4 file using OpenCV’s VideoWriter.
**Upload to Azure:** Files are uploaded to a predefined Azure Blob Storage container.

**Example Workflow**
**Start Streaming:** Open the live feed in your browser.
**Record Video:** Click the "Record" button to start saving the stream.
**Pause/Resume:** Pause the recording if needed, then resume.
**Stop Recording:** Stop recording to trigger an upload to Azure Blob Storage.
**Verify Upload:** Check the Azure Blob Storage container for the uploaded video.

![image5](/attachment/camera2.jpeg)
