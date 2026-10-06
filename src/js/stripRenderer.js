// Strip & Collage Renderer for Photobooth
// Handles 4-Cut Life4Cuts style, 2x2 Grid, and Single Photo with frames, filters, stickers, typography, and Live Photo animations
import { GIFEncoder, quantize, applyPalette } from 'gifenc';
import { getSupportedVideoMimeType } from './capture.js';

export const FRAME_THEMES = {
  white: {
    id: 'white',
    name: 'Classic White',
    bg: '#ffffff',
    textColor: '#1a1a1a',
    subTextColor: '#777777',
    border: '#e5e5e5',
  },
  black: {
    id: 'black',
    name: 'Charcoal Noir',
    bg: '#141416',
    textColor: '#ffffff',
    subTextColor: '#88888e',
    border: '#2a2a2e',
  },
  pink: {
    id: 'pink',
    name: 'Sweet Pink',
    bg: '#ffe0e6',
    textColor: '#4a1525',
    subTextColor: '#8a4055',
    border: '#f7cad0',
  },
  lavender: {
    id: 'lavender',
    name: 'Lilac Dream',
    bg: '#ece2fe',
    textColor: '#2c1a4d',
    subTextColor: '#6b5096',
    border: '#dcd0f7',
  },
  matcha: {
    id: 'matcha',
    name: 'Matcha Cream',
    bg: '#e2f0d9',
    textColor: '#1b3b1f',
    subTextColor: '#4f7253',
    border: '#c8e6b8',
  },
  yellow: {
    id: 'yellow',
    name: 'Butter Honey',
    bg: '#fef3c7',
    textColor: '#523405',
    subTextColor: '#8c651e',
    border: '#fde68a',
  },
  y2k: {
    id: 'y2k',
    name: 'Y2K Gradient',
    isGradient: true,
    colors: ['#ff9a9e', '#fecfef', '#a1c4fd'],
    textColor: '#22223b',
    subTextColor: '#4a4e69',
    border: 'rgba(255,255,255,0.4)',
  },
  sunset: {
    id: 'sunset',
    name: 'Sunset Glow',
    isGradient: true,
    colors: ['#f83600', '#f9d423'],
    textColor: '#ffffff',
    subTextColor: 'rgba(255,255,255,0.85)',
    border: 'rgba(255,255,255,0.3)',
  },
};

export const PHOTO_FILTERS = {
  normal: { id: 'normal', name: 'Original', filter: 'none' },
  vintage: {
    id: 'vintage',
    name: '90s Film',
    filter: 'sepia(0.3) contrast(1.1) brightness(0.96) saturate(1.2)',
  },
  bw: {
    id: 'bw',
    name: 'B&W Classic',
    filter: 'grayscale(1) contrast(1.2) brightness(1.05)',
  },
  warm: {
    id: 'warm',
    name: 'Golden Hour',
    filter: 'sepia(0.25) saturate(1.4) hue-rotate(-8deg) brightness(1.02)',
  },
  cool: {
    id: 'cool',
    name: 'Cool Breeze',
    filter: 'saturate(1.1) hue-rotate(15deg) contrast(1.05)',
  },
  cyber: {
    id: 'cyber',
    name: 'Cyberpunk',
    filter: 'contrast(1.25) saturate(1.6) hue-rotate(20deg)',
  },
};

export class StripRenderer {
  constructor() {
    this.canvas = document.createElement('canvas');
    this.ctx = this.canvas.getContext('2d');
  }

  /**
   * Render the complete photobooth strip or collage
   * @param {Object} options
   * @param {Array<HTMLCanvasElement|HTMLImageElement>} options.snapshots - Captured photos
   * @param {string} options.layout - '4-cut' | 'grid-2x2' | 'single'
   * @param {string} options.themeId - ID from FRAME_THEMES
   * @param {string} options.filterId - ID from PHOTO_FILTERS
   * @param {string} options.title - Custom text caption
   * @param {string} options.dateText - Formatted date string
   * @param {Array} options.stickers - Array of { emoji, x, y, size, rotation }
   * @param {boolean} options.useLive - Whether to render live moving video frames
   * @returns {HTMLCanvasElement}
   */
  render({
    snapshots = [],
    layout = '4-cut',
    themeId = 'white',
    filterId = 'normal',
    title = 'PHOTOBOOTH MEMORIES',
    dateText = new Date().toLocaleDateString('id-ID', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }),
    stickers = [],
    useLive = false,
  }) {
    const theme = FRAME_THEMES[themeId] || FRAME_THEMES.white;
    const filter = PHOTO_FILTERS[filterId] || PHOTO_FILTERS.normal;

    if (layout === '4-cut') {
      this.render4Cut(snapshots, theme, filter, title, dateText, useLive);
    } else if (layout === 'grid-2x2') {
      this.renderGrid2x2(snapshots, theme, filter, title, dateText, useLive);
    } else {
      this.renderSingle(snapshots, theme, filter, title, dateText, useLive);
    }

    // Render placed stickers
    if (stickers && stickers.length > 0) {
      this.renderStickers(stickers);
    }

    return this.canvas;
  }

  // Draw background frame (solid or gradient)
  drawBackground(theme, width, height) {
    if (theme.isGradient) {
      const grad = this.ctx.createLinearGradient(0, 0, width, height);
      theme.colors.forEach((col, idx) => {
        grad.addColorStop(idx / (theme.colors.length - 1), col);
      });
      this.ctx.fillStyle = grad;
    } else {
      this.ctx.fillStyle = theme.bg;
    }
    this.ctx.fillRect(0, 0, width, height);
  }

  // Helper to pick live video source or still canvas
  resolvePhotoSource(snap, useLive) {
    if (!snap) return null;
    if (useLive && snap.liveVideo && snap.liveVideo.readyState >= 2) {
      return snap.liveVideo;
    }
    return snap.canvas || snap;
  }

  // Draw photo with rounded corners and filter
  drawPhoto(img, x, y, width, height, filterStr, radius = 12) {
    if (!img) return;
    this.ctx.save();

    // Rounded rectangle clip
    this.ctx.beginPath();
    this.ctx.roundRect(x, y, width, height, radius);
    this.ctx.clip();

    // Apply color filter
    this.ctx.filter = filterStr;

    // Center-crop draw
    const imgW = img.width || img.videoWidth || img.naturalWidth;
    const imgH = img.height || img.videoHeight || img.naturalHeight;
    if (!imgW || !imgH) {
      this.ctx.restore();
      return;
    }

    const imgRatio = imgW / imgH;
    const targetRatio = width / height;

    let sx = 0,
      sy = 0,
      sWidth = imgW,
      sHeight = imgH;

    if (imgRatio > targetRatio) {
      sWidth = imgH * targetRatio;
      sx = (imgW - sWidth) / 2;
    } else {
      sHeight = imgW / targetRatio;
      sy = (imgH - sHeight) / 2;
    }

    this.ctx.drawImage(img, sx, sy, sWidth, sHeight, x, y, width, height);
    this.ctx.restore();

    // Subtle inner border for photo
    this.ctx.save();
    this.ctx.strokeStyle = 'rgba(0, 0, 0, 0.08)';
    this.ctx.lineWidth = 2;
    this.ctx.beginPath();
    this.ctx.roundRect(x, y, width, height, radius);
    this.ctx.stroke();
    this.ctx.restore();
  }

  // 1. Classic 4-Cut Life Strip (1x4)
  render4Cut(snapshots, theme, filter, title, dateText, useLive = false) {
    const W = 640;
    const H = 1920;
    this.canvas.width = W;
    this.canvas.height = H;

    this.drawBackground(theme, W, H);

    const padX = 40;
    const padTop = 45;
    const photoSpacing = 22;
    const photoW = W - padX * 2; // 560px
    const photoH = 370; // 4:3 approx

    // Draw up to 4 photos
    for (let i = 0; i < 4; i++) {
      const snap = snapshots[i] || snapshots[0];
      const y = padTop + i * (photoH + photoSpacing);
      const source = this.resolvePhotoSource(snap, useLive);
      if (source) {
        this.drawPhoto(source, padX, y, photoW, photoH, filter.filter, 10);
      }
    }

    // Footer section (below 4th photo)
    const footerY = padTop + 4 * (photoH + photoSpacing) + 20;

    this.ctx.save();
    this.ctx.textAlign = 'center';

    // Title
    this.ctx.fillStyle = theme.textColor;
    this.ctx.font = '700 24px "Outfit", "Plus Jakarta Sans", sans-serif';
    this.ctx.letterSpacing = '4px';
    this.ctx.fillText(title.toUpperCase(), W / 2, footerY + 30);

    // Decorative divider or dots
    this.ctx.fillStyle = theme.subTextColor;
    this.ctx.font = '400 15px "Outfit", "Plus Jakarta Sans", sans-serif';
    this.ctx.letterSpacing = '2px';
    this.ctx.fillText(`✦  ${dateText}  ✦`, W / 2, footerY + 65);

    // Aesthetic mini barcode / serial code
    this.ctx.font = '600 11px monospace';
    this.ctx.letterSpacing = '3px';
    this.ctx.fillText('LUMI-AI-BOOTH // 2026', W / 2, footerY + 95);

    this.ctx.restore();
  }

  // 2. 2x2 Grid Collage
  renderGrid2x2(snapshots, theme, filter, title, dateText, useLive = false) {
    const W = 1200;
    const H = 1450;
    this.canvas.width = W;
    this.canvas.height = H;

    this.drawBackground(theme, W, H);

    const padX = 60;
    const padTop = 60;
    const gap = 30;
    const photoW = (W - padX * 2 - gap) / 2; // 525px
    const photoH = 525; // square 1:1

    for (let i = 0; i < 4; i++) {
      const snap = snapshots[i] || snapshots[0];
      const col = i % 2;
      const row = Math.floor(i / 2);
      const x = padX + col * (photoW + gap);
      const y = padTop + row * (photoH + gap);

      const source = this.resolvePhotoSource(snap, useLive);
      if (source) {
        this.drawPhoto(source, x, y, photoW, photoH, filter.filter, 14);
      }
    }

    // Footer
    const footerY = padTop + 2 * photoH + gap + 40;
    this.ctx.save();
    this.ctx.textAlign = 'center';

    this.ctx.fillStyle = theme.textColor;
    this.ctx.font = '700 32px "Outfit", "Plus Jakarta Sans", sans-serif';
    this.ctx.letterSpacing = '4px';
    this.ctx.fillText(title.toUpperCase(), W / 2, footerY + 40);

    this.ctx.fillStyle = theme.subTextColor;
    this.ctx.font = '400 18px "Outfit", "Plus Jakarta Sans", sans-serif';
    this.ctx.letterSpacing = '2px';
    this.ctx.fillText(`✦  ${dateText}  ✦`, W / 2, footerY + 80);

    this.ctx.restore();
  }

  // 3. Single Polaroid Style
  renderSingle(snapshots, theme, filter, title, dateText, useLive = false) {
    const W = 800;
    const H = 1000;
    this.canvas.width = W;
    this.canvas.height = H;

    this.drawBackground(theme, W, H);

    const padX = 50;
    const padTop = 50;
    const photoW = W - padX * 2;
    const photoH = 720;

    const snap = snapshots[0];
    const source = this.resolvePhotoSource(snap, useLive);
    if (source) {
      this.drawPhoto(source, padX, padTop, photoW, photoH, filter.filter, 12);
    }

    // Bottom caption
    const footerY = padTop + photoH + 45;
    this.ctx.save();
    this.ctx.textAlign = 'center';

    this.ctx.fillStyle = theme.textColor;
    this.ctx.font = '700 28px "Outfit", "Plus Jakarta Sans", sans-serif';
    this.ctx.letterSpacing = '3px';
    this.ctx.fillText(title.toUpperCase(), W / 2, footerY + 30);

    this.ctx.fillStyle = theme.subTextColor;
    this.ctx.font = '400 16px "Outfit", "Plus Jakarta Sans", sans-serif';
    this.ctx.letterSpacing = '2px';
    this.ctx.fillText(`✦  ${dateText}  ✦`, W / 2, footerY + 70);

    this.ctx.restore();
  }

  // Render stickers on top of the strip
  renderStickers(stickers) {
    this.ctx.save();
    stickers.forEach((s) => {
      this.ctx.save();
      const x = s.relX * this.canvas.width;
      const y = s.relY * this.canvas.height;
      this.ctx.translate(x, y);
      if (s.rotation) this.ctx.rotate((s.rotation * Math.PI) / 180);

      this.ctx.font = `${s.size || 48}px sans-serif`;
      this.ctx.textAlign = 'center';
      this.ctx.textBaseline = 'middle';
      this.ctx.fillText(s.emoji, 0, 0);

      this.ctx.restore();
    });
    this.ctx.restore();
  }

  /**
   * Export the current canvas as a PNG download
   */
  download(filename = 'photobooth-strip.png') {
    const link = document.createElement('a');
    link.download = filename;
    link.href = this.canvas.toDataURL('image/png', 1.0);
    link.click();
  }

  downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.download = filename;
    link.href = url;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }

  /**
   * Export animated Live Photo strip as video (MP4 / WebM)
   */
  async exportVideo({
    durationMs = 2800,
    filename = 'photobooth-live.mp4',
    onProgress = null,
  }) {
    const mimeType = getSupportedVideoMimeType();
    if (!mimeType) {
      throw new Error('Perekam video tidak didukung di browser ini.');
    }

    const stream = this.canvas.captureStream(30);
    const recorder = new MediaRecorder(stream, {
      mimeType,
      videoBitsPerSecond: 4000000,
    });

    const chunks = [];
    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) chunks.push(e.data);
    };

    return new Promise((resolve, reject) => {
      recorder.onstop = () => {
        const ext = mimeType.includes('mp4') ? 'mp4' : 'webm';
        const finalFilename = filename.replace(/\.[^/.]+$/, '') + '.' + ext;
        const blob = new Blob(chunks, { type: mimeType });
        this.downloadBlob(blob, finalFilename);
        resolve({ blob, filename: finalFilename });
      };

      recorder.onerror = (err) => reject(err);

      recorder.start();

      const startTime = Date.now();
      const interval = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(100, Math.round((elapsed / durationMs) * 100));
        if (onProgress) onProgress(progress);
        if (elapsed >= durationMs) {
          clearInterval(interval);
          if (recorder.state === 'recording') {
            recorder.stop();
          }
        }
      }, 100);
    });
  }

  /**
   * Export animated Live Photo strip as GIF
   */
  async exportGif({
    fps = 10,
    durationMs = 2400,
    scale = 0.45,
    filename = 'photobooth-live.gif',
    onProgress = null,
  }) {
    const gif = GIFEncoder();
    const totalFrames = Math.round((durationMs / 1000) * fps);
    const frameDelay = Math.round(1000 / fps);

    // Scaled offscreen canvas to keep GIF generation swift and file size lightweight
    const scaledCanvas = document.createElement('canvas');
    scaledCanvas.width = Math.round(this.canvas.width * scale);
    scaledCanvas.height = Math.round(this.canvas.height * scale);
    const sCtx = scaledCanvas.getContext('2d');

    for (let frameIndex = 0; frameIndex < totalFrames; frameIndex++) {
      sCtx.clearRect(0, 0, scaledCanvas.width, scaledCanvas.height);
      sCtx.drawImage(this.canvas, 0, 0, scaledCanvas.width, scaledCanvas.height);

      const imageData = sCtx.getImageData(0, 0, scaledCanvas.width, scaledCanvas.height);
      const { data, width, height } = imageData;

      const palette = quantize(data, 256);
      const index = applyPalette(data, palette);

      gif.writeFrame(index, width, height, {
        palette,
        delay: frameDelay,
      });

      if (onProgress) {
        onProgress(Math.round(((frameIndex + 1) / totalFrames) * 100));
      }

      await new Promise((r) => setTimeout(r, frameDelay));
    }

    gif.finish();
    const bytes = gif.bytes();
    const blob = new Blob([bytes], { type: 'image/gif' });
    this.downloadBlob(blob, filename);
    return { blob, filename };
  }

  getDataURL() {
    return this.canvas.toDataURL('image/png', 1.0);
  }
}

