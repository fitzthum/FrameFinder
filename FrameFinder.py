'''
  Given some input image and a video, find the most similar image in the video (and the timestamp)


  TODO: 
    - Test with a different input image. Something with a bold color and a well defined shape. (A person's shoulders?)
    - Try with black and white. 
    - Look into other metrics
    - Figure out the best way to match resolutions.
    
'''

import os
import sys
import cv2
import numpy as np
from pathlib import Path
from pymediainfo import MediaInfo

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

def info(path):
  media_info = MediaInfo.parse(path)
  h = int(media_info.video_tracks[0].height / DOWNSAMPLE)
  w = int(media_info.video_tracks[0].width / DOWNSAMPLE)
  name = media_info.general_tracks[0].file_name

  return (h, w, 3), name

def downsample(image):
  h, w, l = image.shape
  return cv2.resize(image,(int(w/DOWNSAMPLE),int(h/DOWNSAMPLE)))

def euclidean_distance(a,b):
  return cv2.norm(a - b, cv2.NORM_L2)

def save_nearest(name, haystack, scores, n, to_file=False):
  best_frames = sorted(scores, key=lambda x: x[0])[-n:] 
  for frame_info in best_frames:
    frame_score, frame_number = frame_info
    print("frame {} score = {}".format(frame_number,frame_score))
    
    haystack.set(1,frame_number);
    ret, frame = haystack.read()
    
    if not to_file:
      cv2.imshow(name,frame)
      cv2.waitKey(0)
    
    else:
      out_path = "results/o_{}_{}_{}.png".format(name,frame_number,frame_score)
      cv2.imwrite(out_path,frame)


def search_file(needle, video, debug=False):
  # load the image
  video = os.path.abspath(video)
  print(video)
  haystack = cv2.VideoCapture(video)

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

      if debug:
        cv2.imshow("distance", frame)
        cv2.waitKey(0)
    
    frame_number += 1
  
  return haystack, frame_scores
 

def main(args):
  assert(args.video or args.directory)
  
  # load the search frame here so we know the resolution
  needle = downsample(cv2.imread(args.search_frame))
  print(needle.shape)

  if args.directory:
    for path in Path(args.directory).rglob("*.mp4"):
      try:
        resolution, name = info(path)
      except:
        continue
      
      if resolution == needle.shape:
        print("Searching for {} in {}".format(args.search_frame, path))
        haystack, frame_scores = search_file(needle, path)

        print("Saving results for {} in {}".format(args.search_frame, path))
        save_nearest(name, haystack, frame_scores, args.num_found, to_file=True)

  else:
    print("Searching for {} in {}".format(args.search_frame, args.video))
    haystack, frame_scores = search_file(needle, args.video, args.debug)
    
    print("Showing results for {} in {}".format(needle, args.video))
    save_nearest("", haystack, frame_scores, args.num_found)

if __name__ == "__main__":
  parser = ArgumentParser(prog="FrameFinder.py",description="Find similar frames in a video.")
  
  parser.add_argument("-s","--search_frame",required=True)
  parser.add_argument("-v","--video")
  parser.add_argument("-D","--directory")
  parser.add_argument("-d","--debug")
  parser.add_argument("-n","--num_found",default=20)

  args = parser.parse_args()
  main(args)
