# Detector Dockerfile
FROM ubuntu:latest
ENV DEBIAN_FRONTEND noninteractive
#RUN ping -c 2 8.8.8.8
#RUN apt-get update && apt-get install -y \
#	libopencv-dev

#RUN apt-get install python3
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-dev \
    			python3-opencv libopencv-dev
RUN pip3 install roboflow pillow boto3
COPY lp_detector.py .
COPY dashcam.mp4 .
CMD python3 lp_detector.py 'dashcam.mp4' 'w251lpdetector'
