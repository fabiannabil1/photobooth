// Capture workflow: Countdown, Audio cues, Flash, Multi-shot sequencing, and Live Photos recording
import { playCountdownBeep, playShutterSound } from './audio.js';

export function getSupportedVideoMimeType() {
  if (typeof MediaRecorder === 'undefined') return '';
  const types = [
    'video/mp4;codecs=avc1',
    'video/mp4',
    'video/webm;codecs=vp9',
    'video/webm;codecs=vp8',
    'video/webm',
  ];
  for (const t of types) {
    if (MediaRecorder.isTypeSupported(t)) {
      return t;
    }
  }
  return '';
}

export class CaptureManager {
  constructor(segmenter, flashOverlay) {
    this.segmenter = segmenter;
    this.flashOverlay = flashOverlay;
    this.isCapturing = false;
    this.cancelRequested = false;
    this.activeRecorder = null;
  }

  async runSession({
    mode = '4-cut',
    timerSeconds = 3,
    isLivePhoto = true,
    onCountdownTick = null,
    onShotTaken = null,
    onSessionComplete = null,
  }) {
    if (this.isCapturing) return;
    this.isCapturing = true;
    this.cancelRequested = false;

    const totalShots = mode === 'single' ? 1 : 4;
    const snapshots = [];
    const mimeType = isLivePhoto ? getSupportedVideoMimeType() : '';

    for (let shotIndex = 0; shotIndex < totalShots; shotIndex++) {
      if (this.cancelRequested) break;

      let mediaRecorder = null;
      let chunks = [];
      let isRecordingLive = false;

      // Helper to start live video recording
      const startLiveRecording = () => {
        if (!isLivePhoto || !mimeType || isRecordingLive || !this.segmenter?.outputCanvas) return;
        try {
          const stream = this.segmenter.outputCanvas.captureStream(30);
          mediaRecorder = new MediaRecorder(stream, {
            mimeType,
            videoBitsPerSecond: 2500000,
          });
          this.activeRecorder = mediaRecorder;
          mediaRecorder.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) chunks.push(e.data);
          };
          mediaRecorder.start();
          isRecordingLive = true;
        } catch (err) {
          console.warn('Could not start Live Photo recorder:', err);
        }
      };

      // Countdown loop for current shot
      for (let count = timerSeconds; count > 0; count--) {
        if (this.cancelRequested) break;

        // Start Live recording 1.8s - 2s before shutter
        if (count <= 2) {
          startLiveRecording();
        }

        if (onCountdownTick) {
          onCountdownTick({
            count,
            shotIndex: shotIndex + 1,
            totalShots,
            isLiveActive: isLivePhoto && isRecordingLive,
          });
        }

        playCountdownBeep(count === 1 ? 1100 : 750, 0.09);
        await this.sleep(1000);
      }

      if (this.cancelRequested) {
        if (mediaRecorder && mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
        }
        break;
      }

      // If recording hasn't started yet (e.g. 1s timer), start now
      if (!isRecordingLive && isLivePhoto) {
        startLiveRecording();
      }

      // Capture moment!
      playCountdownBeep(1400, 0.12);
      playShutterSound();
      this.triggerFlash();

      const snapshot = this.segmenter.captureSnapshot();

      // Let Live recording capture the post-shutter reaction / smile for 350ms
      let liveResult = null;
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        await this.sleep(350);
        liveResult = await new Promise((resolve) => {
          mediaRecorder.onstop = async () => {
            try {
              const blob = new Blob(chunks, { type: mimeType });
              const url = URL.createObjectURL(blob);
              const video = document.createElement('video');
              video.src = url;
              video.loop = true;
              video.muted = true;
              video.playsInline = true;
              video.autoplay = false;
              // Wait for metadata / first frame ready
              await new Promise((res) => {
                video.onloadeddata = () => res();
                video.onerror = () => res();
                setTimeout(res, 800);
              });
              resolve({ blob, url, video });
            } catch (err) {
              console.warn('Error processing Live Photo video:', err);
              resolve(null);
            }
          };
          mediaRecorder.stop();
        });
      }

      // Attach Live Photo data directly to snapshot canvas
      if (liveResult) {
        snapshot.liveBlob = liveResult.blob;
        snapshot.liveUrl = liveResult.url;
        snapshot.liveVideo = liveResult.video;
        snapshot.isLive = true;
      } else {
        snapshot.isLive = false;
      }

      snapshots.push(snapshot);

      if (onShotTaken) {
        onShotTaken({
          shotIndex: shotIndex + 1,
          totalShots,
          snapshot,
        });
      }

      // If there are more shots, brief pause so user can see their photo and change pose
      if (shotIndex < totalShots - 1 && !this.cancelRequested) {
        if (onCountdownTick) {
          onCountdownTick({
            count: 'Next Pose...',
            shotIndex: shotIndex + 1,
            totalShots,
            isPrep: true,
          });
        }
        await this.sleep(1800);
      }
    }

    this.isCapturing = false;
    this.activeRecorder = null;

    if (!this.cancelRequested && onSessionComplete) {
      onSessionComplete(snapshots);
    }
  }

  triggerFlash() {
    if (!this.flashOverlay) return;
    this.flashOverlay.classList.remove('active');
    // Force reflow
    void this.flashOverlay.offsetWidth;
    this.flashOverlay.classList.add('active');
    setTimeout(() => {
      this.flashOverlay.classList.remove('active');
    }, 450);
  }

  cancel() {
    this.cancelRequested = true;
    this.isCapturing = false;
    if (this.activeRecorder && this.activeRecorder.state === 'recording') {
      try {
        this.activeRecorder.stop();
      } catch (_) {}
    }
    this.activeRecorder = null;
  }

  sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

