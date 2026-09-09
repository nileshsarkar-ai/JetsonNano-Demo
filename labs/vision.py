#!/usr/bin/env python3
"""Nano TensorRT camera labs. See docs/VISION.md for installation."""
import argparse
import json
import subprocess
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['detect', 'classify', 'pose', 'segment'])
    p.add_argument('input', nargs='?', default='v4l2:///dev/video0')
    p.add_argument('output', nargs='?', default='display://0')
    p.add_argument('--network', default=None)
    p.add_argument('--threshold', type=float, default=0.5)
    p.add_argument('--frames', type=int, default=0, help='0 means until stream ends')
    p.add_argument('--speak', action='store_true', help='Speak detected class names every 5 seconds')
    a, extra = p.parse_known_args()
    from jetson_inference import detectNet, imageNet, poseNet, segNet
    from jetson_utils import videoSource, videoOutput, cudaAllocMapped
    defaults = {'detect': 'ssd-mobilenet-v2', 'classify': 'googlenet',
                'pose': 'resnet18-body', 'segment': 'fcn-resnet18-voc'}
    name = a.network or defaults[a.mode]
    argv = ['vision.py'] + extra
    if a.mode == 'detect':
        net = detectNet(name, argv, a.threshold)
    elif a.mode == 'classify':
        net = imageNet(name, argv)
    elif a.mode == 'pose':
        net = poseNet(name, argv, a.threshold)
    else:
        net = segNet(name, argv)
        net.SetOverlayAlpha(150.0)
    source = videoSource(a.input, argv=argv)
    output = videoOutput(a.output, argv=argv)
    overlay = None
    frame, last_speech, speaker = 0, -5.0, None
    try:
        while source.IsStreaming() and output.IsStreaming():
            img = source.Capture()
            if img is None:
                continue
            frame += 1
            record = {'frame': frame, 'mode': a.mode}
            labels = []
            if a.mode == 'detect':
                detections = net.Detect(img, overlay='box,labels,conf')
                record['detections'] = [
                    {'label': net.GetClassDesc(d.ClassID), 'confidence': float(d.Confidence),
                     'box': [float(d.Left), float(d.Top), float(d.Right), float(d.Bottom)]}
                    for d in detections]
                labels = sorted(set(d['label'] for d in record['detections']))
                # This is occupancy in one frame, not a count of unique visitors.
                record['objects_in_frame'] = len(detections)
            elif a.mode == 'classify':
                class_id, confidence = net.Classify(img)
                record.update(label=net.GetClassDesc(class_id), confidence=float(confidence))
            elif a.mode == 'pose':
                poses = net.Process(img, overlay='links,keypoints')
                record['people'] = len(poses)
                record['raised_left_hands'] = 0
                for pose in poses:
                    wrist, shoulder = pose.FindKeypoint('left_wrist'), pose.FindKeypoint('left_shoulder')
                    if wrist >= 0 and shoulder >= 0:
                        record['raised_left_hands'] += int(pose.Keypoints[wrist].y < pose.Keypoints[shoulder].y)
            else:
                if overlay is None or overlay.width != img.width or overlay.height != img.height:
                    overlay = cudaAllocMapped(width=img.width, height=img.height, format=img.format)
                net.Process(img, ignore_class='void')
                net.Overlay(overlay, filter_mode='linear')
                img = overlay
            print(json.dumps(record), flush=True)
            if a.speak and labels and time.monotonic() - last_speech >= 5 and (speaker is None or speaker.poll() is not None):
                speaker = subprocess.Popen(['espeak-ng', '--stdin'], stdin=subprocess.PIPE)
                speaker.stdin.write(('I see ' + ', '.join(labels)).encode('utf-8'))
                speaker.stdin.close()
                last_speech = time.monotonic()
            output.Render(img)
            output.SetStatus('{} | {:.1f} network FPS'.format(name, net.GetNetworkFPS()))
            if a.frames and frame >= a.frames:
                break
    finally:
        source.Close()
        output.Close()
        if speaker is not None and speaker.poll() is None:
            speaker.terminate()
            speaker.wait()


if __name__ == '__main__':
    main()
