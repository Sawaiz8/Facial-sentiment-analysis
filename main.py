from ultralytics import YOLO
import cv2
from deepface.extendedmodels import Emotion
from random import randint
import numpy as np
import argparse
import os

class VideoAnalyzer:

    def __init__(self):
        self.senti_model = Emotion.loadModel()
        self.labels = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
        self.colors = self.gen_colors_based_on_id()
        self.yolo_model = YOLO('models/yolo_basic/yolov8n.pt')

    def gen_colors_based_on_id(self):
        """
        Generates random colors for each indivual
        """
        colors = dict()
        for i in range(1,50):
            colors["id " + str(i)] = (randint(0,255), randint(0,255), randint(0,255))
        return colors

    def sentiment_analysis(self, cropped_image):  
        """
        Predicts the emotion based on the given image
        """
        #Process the image for the sentiment analysis model
        cropped_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        cropped_image = cv2.resize(cropped_image, (48,48))

        result = self.senti_model.predict(np.expand_dims(cropped_image, axis=0), verbose=False)
        emotion = np.argmax(result)
        return emotion

    def draw(self,image, bounding_boxes, ids):
        """
        Given the bounding box coordinates and their cooresponding ids 
        the function draw the bounding boxes with the emotion of each face
        """
        i = 0 
        for x, y,w,h in bounding_boxes:

            # Convert coordinates into integers
            x = int(x) 
            y = int(y) 
            w = int(w) 
            h = int(h)

            #Convert YOLO coordinates 
            l = int((x - w / 2))
            r = int((x + w / 2))
            t = int((y - h / 2))
            b = int((y + h / 2))
            cropped_image = image[t:b, l:r]
            #Get sentiment
            emotion = self.sentiment_analysis(cropped_image)

            #Get the identity of the person
            id = str(int(ids[i]))

            #Plot bounding box with text
            image = cv2.rectangle(image, (l, t), (r, b), self.colors[f"id {id}"], 2)   
            image = cv2.putText(image, f"id {id}:{self.labels[emotion]}", (l, t-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors[f"id {id}"], 2)
            i+=1

        return image 

    def process_video(self, video_path, output_path, show=False):
        """
        Analyzes the video for identites and emotions of each face through time.
        Inputs:
            video_path: The path of the video to be processed
            output_path: The path of the output folder
        """
        # Open the video file
        cap = cv2.VideoCapture(video_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(os.path.join(output_path, "output.mp4"), fourcc, fps, (frame_width,frame_height))  

        # Loop through the video frames
        print("Started writing")
        while cap.isOpened():
            # Read a frame from the video
            success, frame = cap.read()

            if success:
                # Run YOLOv8 tracking on the frame, persisting tracks between frames
                results = self.yolo_model.track(frame, classes=[0], persist=True, verbose=False, conf=0.1)

                # Visualize the results on the frame
                annotated_frame = self.draw(results[0].orig_img, results[0].boxes.xywh, ids=results[0].boxes.id)

                # Display the annotated frame
                if show:
                    cv2.imshow("YOLOv8 Tracking", annotated_frame)
                else:
                    #Write the annotated frame
                    out.write(annotated_frame)

                # Break the loop if 'q' is pressed
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            else:
                break

        # Release the video capture object and close the display window
        cap.release()
        out.release()
        cv2.destroyAllWindows()
        print("Writing completed")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--video_path', type=str, help="video path")
    parser.add_argument('--output_path', type=str, help="output video path")
    parser.add_argument('--show_video_only', type=int, help="0 or 1", default=1)
    args = parser.parse_args()

    #Intiaize the class and process the video
    proc = VideoAnalyzer()
    proc.process_video(args.video_path, args.output_path, args.show_video_only)