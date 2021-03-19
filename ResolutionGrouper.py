'''
  Find the resolution of every video in a directory and group together.
'''

from pathlib import Path
from argparse import ArgumentParser
from pymediainfo import MediaInfo
from collections import defaultdict
import shlex

EXTENSIONS = ["*.mp4"]


def main(args):
  resolutions = defaultdict(list) 
  for ext in EXTENSIONS:
    for path in Path(args.path).rglob(ext):
      media_info = MediaInfo.parse(path)
      try:
        h = media_info.video_tracks[0].height
        w = media_info.video_tracks[0].width
        name = media_info.general_tracks[0].file_name 
        resolutions[(w,h)].append(name)
      except:
        pass
  
  for resolution in resolutions.keys():
    print(resolution)
    for movie_path in resolutions[resolution]:
      print(movie_path)

if __name__ == "__main__":
  parser = ArgumentParser(prog="ResolutionGrouper.py",description="Group videos by resolution")
  parser.add_argument("-p","--path",required=True)
  
  args = parser.parse_args()
  main(args)



