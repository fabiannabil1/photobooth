// Camera Stream Manager

export class CameraManager {
  constructor(videoElement) {
    this.videoElement = videoElement;
    this.currentStream = null;
    this.currentDeviceId = null;
    this.isMirrored = true;
    this.isReady = false;
    this.onError = null;
    this.onReady = null;
  }

  async getDevices() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
      return [];
    }
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      return devices.filter((d) => d.kind === 'videoinput');
    } catch (err) {
      console.warn('Could not enumerate media devices:', err);
      return [];
    }
  }

  async start(deviceId = null) {
    this.stop();

    const constraints = {
      audio: false,
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: deviceId ? undefined : 'user',
        deviceId: deviceId ? { exact: deviceId } : undefined,
      },
    };

    try {
      this.currentStream = await navigator.mediaDevices.getUserMedia(constraints);
      this.videoElement.srcObject = this.currentStream;
      this.currentDeviceId = deviceId;

      await new Promise((resolve) => {
        this.videoElement.onloadedmetadata = () => {
          this.videoElement.play();
          this.isReady = true;
          if (this.onReady) this.onReady(this.videoElement);
          resolve();
        };
      });

      return true;
    } catch (err) {
      console.error('Failed to access camera:', err);
      this.isReady = false;
      if (this.onError) this.onError(err);
      return false;
    }
  }

  stop() {
    if (this.currentStream) {
      this.currentStream.getTracks().forEach((track) => track.stop());
      this.currentStream = null;
    }
    this.isReady = false;
  }

  toggleMirror() {
    this.isMirrored = !this.isMirrored;
    return this.isMirrored;
  }
}
