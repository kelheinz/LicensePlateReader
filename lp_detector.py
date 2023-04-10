from PIL import Image, ImageDraw
from roboflow import Roboflow
import cv2
import sys
import boto3

# Initialize plate detection model API connection
rf_plate_detect = Roboflow(api_key="csCH8PchJ8ZqRqC99txw")
project_plate_detect = rf_plate_detect.workspace().project("license-plate-detector-uni5r")
model_plate_detect = project_plate_detect.version(6).model

# Initialize OCR model API connection
rf_ocr = Roboflow(api_key="T7TqkGjW4FsMg06nyCOQ")
project_ocr = rf_ocr.workspace().project("ocr-oy9a7")
model_ocr = project_ocr.version(1).model

# Connect to S3 Bucket
s3 = boto3.resource('s3')
# Will use bucket 'w251lpdetector'
BUCKET = sys.argv[2]

# Load video
# Will test on file 'dashcam.mp4'
filename = sys.argv[1]
vidcap = cv2.VideoCapture(filename)
success, image = vidcap.read()
count = 0
while success:
    vidcap.set(cv2.CAP_PROP_POS_MSEC, (count*1000))
    success, image = vidcap.read()
    print("Read a new frame: ", success)
    if success:
        count += 1
        cv2.imwrite('temp.jpg', image)

        # filename = 'multi_car_example.jpg'
        image = Image.open('temp.jpg')
        draw = ImageDraw.Draw(image)

        # # Detect plates in image
        prediction = model_plate_detect.predict('temp.jpg', confidence=40,
                                                overlap=30).json()

        if prediction['predictions']:
            for pred in prediction['predictions']:
                # Crop to Coordinates
                x = pred['x']
                y = pred['y']
                w = pred['width']/2
                h = pred['height']/2
                area = (x-w, y-h, x+w, y+h)
                plate = image.crop(area)

                # Save to temp file to send to OCR model
                _plate = plate.save('temp.jpg')

                # Send to OCR
                ocr_prediction = model_ocr.predict('temp.jpg', confidence=40, overlap=30).json()
                sorted_predictions = sorted(ocr_prediction['predictions'], key=lambda d: d['x'])
                plate_str = None
                for symbol in sorted_predictions:
                    if symbol['confidence']>0.6:
                        try:
                            plate_str += symbol['class']
                        except TypeError:
                            plate_str = symbol['class']

                # Save as original filename + LP string if LP# was detected
                if plate_str:
                    og_filename = filename.split(".")[0]
                    draw.rectangle((area), outline='blue', width=2)
                    draw.text((x+w,y+h), plate_str, fill='white')
                    img_name = og_filename+"_"+plate_str+'.jpg'
                    _image = image.save(img_name)
                    s3.Bucket(BUCKET).upload_file(img_name,
                                                  img_name)
                    print(f"LP detected in {img_name}")
                else:
                    print("License Plate unreadable")
        else:
            print('No License Plate Detected')


