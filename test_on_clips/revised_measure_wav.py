# Environment specific paths
API_PATH = "../../OpenVokaturi-3-0a/api"
BIN_PATH = "../../OpenVokaturi-3-0a/lib/open/linux/OpenVokaturi-3-0-linux64.so"
import argparse
import os
import scipy.io.wavfile
import numpy as np
import ctypes
import sys
sys.path.append(API_PATH)  # Alternatively set this in bashrc/profile
import Vokaturi
Vokaturi.load(BIN_PATH)  # Instantiates C lib related signatures (arg types)

def main(filepath):
  # Read wavefile and its metadata
  rate, data = scipy.io.wavfile.read(filepath)
  num_channels = 1 if data.ndim == 1 else data.shape[1]
  num_samples = len(data)
  print("{} => {} Hz ({} channels), total {} samples".format(os.path.split(filepath)[1], rate, num_channels, num_samples))

  # Vokaturi lib needs the 16-bit PCM data => in c_double format
  # tldr: divide by int16, and when multi-channel get average (sum and divide)
  if num_channels == 1:
    float_data = data / 32768.0
  else:
    float_data = np.sum(data, axis=1) / num_channels / 32768.0
  c_data = float_data.ctypes.data_as(ctypes.POINTER(ctypes.c_double))

  # Init and use Vokaturi lib just once
  voice = Vokaturi.Voice(rate, num_samples)
  voice.fill(num_samples, c_data)
  quality = Vokaturi.Quality()
  emotion_probs = Vokaturi.EmotionProbabilities()
  voice.extract(quality, emotion_probs)  # This runs the analysis on <whatever content> the Vokaturi.Voice has been filled with
  if quality.valid:
    print("({} analyzed frames)".format(quality.num_frames_analyzed))
    print("Neutral: {:4.0%}".format(emotion_probs.neutrality))
    print("Happy:   {:4.0%}".format(emotion_probs.happiness))
    print("Sad:     {:4.0%}".format(emotion_probs.sadness))
    print("Angry:   {:4.0%}".format(emotion_probs.anger))
    print("Fear:    {:4.0%}".format(emotion_probs.fear))
  else:
    print("Too low quality audio to discern emotions.")  

  voice.destroy()

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("filepath", help="Path to the wav file (either mono or stereo)")
  args = parser.parse_args()
  main(args.filepath)
