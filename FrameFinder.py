'''
  Given some input image and a video, find the most similar image in the video (and the timestamp)


  TODO: 
    - Test with a different input image. Something with a bold color and a well defined shape. (A person's shoulders?)
    - Try with black and white. 
    - Look into other metrics
    - Figure out the best way to match resolutions.
    
'''

import sys
import cv2
import numpy as np

from skimage.metrics import structural_similarity as ssim
from argparse import ArgumentParser

DISTANCE_THRESHOLD = 0.1
SAMPLE_RATE = 40
DOWNSAMPLE = 10

# dynamic sample rate
FRAME_SKIP_FLOOR = 1
FRAME_SKIP_CEIL = 200
FRAME_SKIP_STEP = 1000
FRAME_SKIP_START = 40

def downsample(image):
  h, w, l = image.shape
  return cv2.resize(image,(int(w/DOWNSAMPLE),int(h/DOWNSAMPLE)))

def euclidean_distance(a,b):
  return cv2.norm(a - b, cv2.NORM_L2)

def show_nearest(haystack, scores, n):
  best_frames = sorted(scores, key=lambda x: x[0])[-n:] 
  for frame_info in best_frames:
    frame_score, frame_number = frame_info
    print("frame {} score = {}".format(frame_number,frame_score))
    
    haystack.set(1,frame_number);
    ret, frame = haystack.read()
    
    cv2.imshow("candidate",frame)
    cv2.waitKey(0)

def main(args):
  # load the image
  needle = downsample(cv2.imread(args.search_frame))
  haystack = cv2.VideoCapture(args.video)

  total_frames = int(haystack.get(cv2.CAP_PROP_FRAME_COUNT))

  frame_number = 0
  frames_skipped = 0
  frames_to_skip = FRAME_SKIP_START
  
  previous_frame_score = 0

  frame_scores = [] 

  while frame_number < total_frames:
    ret, frame = haystack.read()

    if not frames_skipped == frames_to_skip:
      frames_skipped += 1

    else: 
      frames_skipped = 0

      try:
        frame = downsample(frame)
      except:
        print("end of file")
        break

      assert(frame.shape == needle.shape)
      
      frame_score = ssim(needle, frame, multichannel=True)
      frame_scores.append((frame_score, frame_number))
      print("frame {} / {} distance = {}".format(frame_number,total_frames,frame_score))
      
      score_delta = previous_frame_score - frame_score
      skip_delta = int(score_delta * FRAME_SKIP_STEP)
      frames_to_skip = min(max((frames_to_skip + skip_delta),FRAME_SKIP_FLOOR),FRAME_SKIP_CEIL)
      
      previous_frame_score = frame_score

      if args.debug:
        cv2.imshow("distance", frame)
        cv2.waitKey(0)
    
    frame_number += 1
 
  show_nearest(haystack, frame_scores, 20)


if __name__ == "__main__":
  parser = ArgumentParser(prog="FrameFinder.py",description="Find similar frames in a video.")
  
  parser.add_argument("-s","--search_frame",required=True)
  parser.add_argument("-v","--video",required=True)
  parser.add_argument("-d","--debug")

  args = parser.parse_args()
  main(args)
