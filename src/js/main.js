// Main Application Controller for Lumi Booth
import '../style.css';
import confetti from 'canvas-confetti';
import { CameraManager } from './camera.js';
import { BackgroundSegmenter } from './segmenter.js';
import { CaptureManager } from './capture.js';
import { StripRenderer, FRAME_THEMES, PHOTO_FILTERS } from './stripRenderer.js';
import { playChime } from './audio.js';

// DOM Elements
const captureView = document.getElementById('captureView');
const studioView = document.getElementById('studioView');

const viewfinderCanvas = document.getElementById('viewfinderCanvas');
const webcamVideo = document.getElementById('webcamVideo');
const flashOverlay = document.getElementById('flashOverlay');
const countdownOverlay = document.getElementById('countdownOverlay');
const countdownNumber = document.getElementById('countdownNumber');
const countdownLabel = document.getElementById('countdownLabel');
const shotProgressPill = document.getElementById('shotProgressPill');
const shotProgressText = document.getElementById('shotProgressText');
const shotDots = document.getElementById('shotDots');

const cameraSelect = document.getElementById('cameraSelect');
const btnMirror = document.getElementById('btnMirror');

const bgTabs = document.querySelectorAll('.bg-tab-btn');
const bgTabContents = document.querySelectorAll('.bg-tab-content');
const presetsGrid = document.getElementById('presetsGrid');
const blurButtons = document.querySelectorAll('.blur-btn');
const uploadDropzone = document.getElementById('uploadDropzone');
const bgFileInput = document.getElementById('bgFileInput');
const uploadDropText = document.getElementById('uploadDropText');

const modeButtons = document.querySelectorAll('.mode-btn');
const timerButtons = document.querySelectorAll('.timer-btn');
const btnShutter = document.getElementById('btnShutter');
const shutterBtnText = document.getElementById('shutterBtnText');

const stripCanvas = document.getElementById('stripCanvas');
const stripCanvasWrapper = document.getElementById('stripCanvasWrapper');
const swatchesGrid = document.getElementById('swatchesGrid');
const filtersGrid = document.getElementById('filtersGrid');
const stickersTray = document.getElementById('stickersTray');
const stickerCountHint = document.getElementById('stickerCountHint');
const stripTitleInput = document.getElementById('stripTitleInput');
const btnDownload = document.getElementById('btnDownload');
const btnRetake = document.getElementById('btnRetake');

// Live Photo Elements
const liveIndicatorPill = document.getElementById('liveIndicatorPill');
const livePhotoToggle = document.getElementById('livePhotoToggle');
const livePlaybackBar = document.getElementById('livePlaybackBar');
const btnToggleLivePlay = document.getElementById('btnToggleLivePlay');
const livePlayBtnLabel = document.getElementById('livePlayBtnLabel');
const liveExportRow = document.getElementById('liveExportRow');
const btnDownloadVideo = document.getElementById('btnDownloadVideo');
const btnDownloadGif = document.getElementById('btnDownloadGif');

// Export Modal Elements
const exportModalOverlay = document.getElementById('exportModalOverlay');
const exportModalTitle = document.getElementById('exportModalTitle');
const exportModalDesc = document.getElementById('exportModalDesc');
const exportProgressBar = document.getElementById('exportProgressBar');
const exportProgressPercent = document.getElementById('exportProgressPercent');

// App State
const state = {
  currentMode: '4-cut', // '4-cut' | 'grid-2x2' | 'single'
  timerSeconds: 3,
  isLivePhotoEnabled: true,
  isLivePlaying: true,
  isHoverPlaying: false,
  liveAnimId: null,

  // Studio customization state
  capturedSnapshots: [],
  selectedTheme: 'white',
  selectedFilter: 'normal',
  stripTitle: 'PHOTOBOOTH MEMORIES',
  stickers: [],
};

// Instances
const cameraManager = new CameraManager(webcamVideo);
const segmenter = new BackgroundSegmenter(viewfinderCanvas, webcamVideo);
const captureManager = new CaptureManager(segmenter, flashOverlay);
const stripRenderer = new StripRenderer();

// ============================================================================
// Initialization
// ============================================================================
async function initApp() {
  setupEventListeners();

  // 1. Initialize MediaPipe
  segmenter.init().then(() => {
    segmenter.start();
  });

  // 2. Try to start camera
  await startWebcam();
}

// Start webcam feed and populate device selector
async function startWebcam(deviceId = null) {
  const success = await cameraManager.start(deviceId);
  if (success) {
    // Populate cameras
    const devices = await cameraManager.getDevices();
    cameraSelect.innerHTML = '<option value="">Pilih Kamera...</option>';
    devices.forEach((d, i) => {
      const opt = document.createElement('option');
      opt.value = d.deviceId;
      opt.textContent = d.label || `Kamera ${i + 1}`;
      if (d.deviceId === cameraManager.currentDeviceId) {
        opt.selected = true;
      }
      cameraSelect.appendChild(opt);
    });
  } else {
    console.warn('Kamera tidak tersedia atau izin kamera belum diberikan.');
  }
}

// ============================================================================
// Event Listeners Setup
// ============================================================================
function setupEventListeners() {
  // 1. Mirror toggle
  btnMirror.addEventListener('click', () => {
    const isMirrored = cameraManager.toggleMirror();
    segmenter.setMirrored(isMirrored);
    btnMirror.classList.toggle('active', isMirrored);
  });

  // 2. Camera select
  cameraSelect.addEventListener('change', (e) => {
    if (e.target.value) {
      startWebcam(e.target.value);
    }
  });

  // 4. Background Tabs
  bgTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      bgTabs.forEach((t) => t.classList.remove('active'));
      bgTabContents.forEach((c) => c.classList.remove('active'));

      tab.classList.add('active');
      const targetId = tab.dataset.tab;
      document.getElementById(targetId)?.classList.add('active');

      if (targetId === 'tab-none') {
        clearActiveBgSelections();
        segmenter.setMode('none');
      }
    });
  });

  // 5. Blur Options
  blurButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      clearActiveBgSelections();
      btn.classList.add('active');
      const blurType = btn.dataset.blur;
      segmenter.setMode(blurType);
    });
  });

  // 6. Preset Backgrounds
  presetsGrid.addEventListener('click', (e) => {
    const item = e.target.closest('.bg-preset-item');
    if (!item) return;

    clearActiveBgSelections();
    item.classList.add('active');
    const presetSrc = item.dataset.preset;
    segmenter.setMode('preset', presetSrc);
  });

  // 7. Custom Image Upload
  uploadDropzone.addEventListener('click', () => {
    bgFileInput.click();
  });

  bgFileInput.addEventListener('change', (e) => {
    const file = e.target.files?.[0];
    if (file) {
      handleCustomBgFile(file);
    }
  });

  // Drag & drop support
  uploadDropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadDropzone.style.borderColor = 'var(--accent-primary)';
  });
  uploadDropzone.addEventListener('dragleave', () => {
    uploadDropzone.style.borderColor = '';
  });
  uploadDropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadDropzone.style.borderColor = '';
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      handleCustomBgFile(file);
    }
  });

  // 7b. Anti-Leak Precision Level
  const antiLeakButtons = document.querySelectorAll('.anti-leak-btn');
  const antiLeakHint = document.getElementById('antiLeakHint');
  antiLeakButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      antiLeakButtons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      const level = btn.dataset.level;
      segmenter.setAntiLeakLevel(level);

      if (level === 'ultra') {
        antiLeakHint.textContent = 'Ultra (Ketat)';
      } else if (level === 'normal') {
        antiLeakHint.textContent = 'Lembut (Alami)';
      } else {
        antiLeakHint.textContent = 'Tinggi (Rapi)';
      }
    });
  });

  // 8. Shooting Mode Selection
  modeButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      modeButtons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      state.currentMode = btn.dataset.mode;

      if (state.currentMode === 'single') {
        shutterBtnText.textContent = 'Mulai Foto (1 Pose)';
      } else {
        shutterBtnText.textContent = 'Mulai Foto (4 Pose)';
      }
    });
  });

  // 9. Timer Selection
  timerButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      timerButtons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      state.timerSeconds = parseInt(btn.dataset.timer, 10);
    });
  });

  // 10. Shutter Button
  btnShutter.addEventListener('click', () => {
    triggerCaptureSession();
  });

  // 11. Studio View: Frame Swatches
  swatchesGrid.addEventListener('click', (e) => {
    const btn = e.target.closest('.swatch-btn');
    if (!btn) return;

    document.querySelectorAll('.swatch-btn').forEach((s) => s.classList.remove('active'));
    btn.classList.add('active');
    state.selectedTheme = btn.dataset.theme;
    updateStudioPreview();
  });

  // 12. Studio View: Photo Filters
  filtersGrid.addEventListener('click', (e) => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;

    document.querySelectorAll('.filter-btn').forEach((f) => f.classList.remove('active'));
    btn.classList.add('active');
    state.selectedFilter = btn.dataset.filter;
    updateStudioPreview();
  });

  // 13. Studio View: Stickers
  stickersTray.addEventListener('click', (e) => {
    const btn = e.target.closest('.sticker-btn');
    if (!btn) return;

    const emoji = btn.dataset.emoji;
    addSticker(emoji);
  });

  // 14. Title input change
  stripTitleInput.addEventListener('input', (e) => {
    state.stripTitle = e.target.value.trim() || 'PHOTOBOOTH MEMORIES';
    updateStudioPreview(state.isLivePlaying || state.isHoverPlaying);
  });

  // 15. Download Strip (PNG)
  btnDownload.addEventListener('click', () => {
    const filename = `lumibooth-${state.currentMode}-${Date.now()}.png`;
    stripRenderer.download(filename);
  });

  // 15b. Live Photo Toggle
  livePhotoToggle?.addEventListener('change', (e) => {
    state.isLivePhotoEnabled = e.target.checked;
    liveIndicatorPill?.classList.toggle('active', state.isLivePhotoEnabled);
  });

  // 15c. Live Playback Toggle Button
  btnToggleLivePlay?.addEventListener('click', () => {
    if (state.isLivePlaying) {
      stopLivePlayback(false);
    } else {
      startLivePlayback(false);
    }
  });

  // 15d. Hover & Touch Live Interaction on Strip
  stripCanvasWrapper?.addEventListener('mouseenter', () => {
    if (hasLiveVideos() && !state.isLivePlaying) {
      startLivePlayback(true);
    }
  });

  stripCanvasWrapper?.addEventListener('mouseleave', () => {
    if (state.isHoverPlaying) {
      stopLivePlayback(true);
    }
  });

  stripCanvasWrapper?.addEventListener('pointerdown', () => {
    if (hasLiveVideos() && !state.isLivePlaying) {
      startLivePlayback(true);
    }
  });

  stripCanvasWrapper?.addEventListener('pointerup', () => {
    if (state.isHoverPlaying) {
      stopLivePlayback(true);
    }
  });

  // 15e. Export Live Video (MP4 / WebM)
  btnDownloadVideo?.addEventListener('click', async () => {
    showExportModal('Merekam Live Video...', 'Mengompilasi animasi strip HD bergerak dengan efek & stiker...');
    try {
      startLivePlayback(false);
      await stripRenderer.exportVideo({
        durationMs: 2800,
        filename: `lumibooth-live-${Date.now()}.mp4`,
        onProgress: (p) => updateExportProgress(p),
      });
    } catch (err) {
      console.error('Video export error:', err);
      alert('Gagal mengunduh video: ' + (err.message || err));
    } finally {
      hideExportModal();
    }
  });

  // 15f. Export Animated GIF
  btnDownloadGif?.addEventListener('click', async () => {
    showExportModal('Membuat GIF Animasi...', 'Merender frame animasi strip dengan palet warna optimal...');
    try {
      startLivePlayback(false);
      await stripRenderer.exportGif({
        fps: 10,
        durationMs: 2400,
        scale: 0.45,
        filename: `lumibooth-live-${Date.now()}.gif`,
        onProgress: (p) => updateExportProgress(p),
      });
    } catch (err) {
      console.error('GIF export error:', err);
      alert('Gagal membuat GIF: ' + (err.message || err));
    } finally {
      hideExportModal();
    }
  });

  // 16. Retake / New Session
  btnRetake.addEventListener('click', () => {
    stopLivePlayback(false);
    state.capturedSnapshots.forEach((s) => {
      if (s.liveUrl) {
        URL.revokeObjectURL(s.liveUrl);
      }
    });
    state.capturedSnapshots = [];
    state.stickers = [];
    stickerCountHint.textContent = '0 stiker ditempelkan. Klik stiker untuk menambahkan ke strip.';

    studioView.classList.remove('active');
    captureView.classList.add('active');
  });
}

function clearActiveBgSelections() {
  blurButtons.forEach((b) => b.classList.remove('active'));
  document.querySelectorAll('.bg-preset-item').forEach((i) => i.classList.remove('active'));
}

function handleCustomBgFile(file) {
  const reader = new FileReader();
  reader.onload = (event) => {
    const img = new Image();
    img.onload = () => {
      clearActiveBgSelections();
      segmenter.setMode('custom', img);
      uploadDropText.textContent = `✓ ${file.name}`;
    };
    img.src = event.target.result;
  };
  reader.readAsDataURL(file);
}

// ============================================================================
// Capture Session Workflow
// ============================================================================
async function triggerCaptureSession() {
  btnShutter.disabled = true;
  countdownOverlay.classList.add('active');

  const totalShots = state.currentMode === 'single' ? 1 : 4;

  if (totalShots > 1) {
    shotProgressPill.style.display = 'flex';
    updateShotDots(1, totalShots);
  } else {
    shotProgressPill.style.display = 'none';
  }

  await captureManager.runSession({
    mode: state.currentMode,
    timerSeconds: state.timerSeconds,
    isLivePhoto: state.isLivePhotoEnabled,

    onCountdownTick: ({ count, shotIndex, totalShots, isPrep, isLiveActive }) => {
      countdownNumber.textContent = count;
      if (isPrep) {
        countdownLabel.textContent = `Bersiap untuk Pose ${shotIndex + 1}!`;
      } else {
        countdownLabel.textContent = `Pose ${shotIndex} dari ${totalShots}`;
      }
      updateShotDots(shotIndex, totalShots);

      if (state.isLivePhotoEnabled) {
        liveIndicatorPill?.classList.add('active');
      }
    },

    onShotTaken: ({ shotIndex, totalShots }) => {
      countdownNumber.textContent = '📸';
      countdownLabel.textContent = 'Tersenyum!';
      updateShotDots(shotIndex, totalShots);
    },

    onSessionComplete: (snapshots) => {
      countdownOverlay.classList.remove('active');
      shotProgressPill.style.display = 'none';
      btnShutter.disabled = false;

      state.capturedSnapshots = snapshots;
      openStudioView();
    },
  });
}

function updateShotDots(currentShot, total) {
  shotProgressText.textContent = `Foto ${currentShot} dari ${total}`;
  shotDots.innerHTML = '';
  for (let i = 1; i <= total; i++) {
    const dot = document.createElement('span');
    dot.className = `shot-dot ${i <= currentShot ? 'filled' : ''}`;
    shotDots.appendChild(dot);
  }
}

// ============================================================================
// Studio View & Rendering
// ============================================================================
function openStudioView() {
  captureView.classList.remove('active');
  studioView.classList.add('active');

  // Trigger celebration audio & confetti
  playChime();
  confetti({
    particleCount: 80,
    spread: 70,
    origin: { y: 0.6 },
    colors: ['#a855f7', '#ec4899', '#fef08a', '#60a5fa'],
  });

  const hasLive = hasLiveVideos();
  if (hasLive) {
    if (livePlaybackBar) livePlaybackBar.style.display = 'flex';
    if (liveExportRow) liveExportRow.style.display = 'grid';
    startLivePlayback(false);
  } else {
    if (livePlaybackBar) livePlaybackBar.style.display = 'none';
    if (liveExportRow) liveExportRow.style.display = 'none';
    updateStudioPreview(false);
  }
}

function hasLiveVideos() {
  return state.capturedSnapshots.some((s) => s.isLive && s.liveVideo);
}

function startLivePlayback(isHover = false) {
  if (!hasLiveVideos()) return;

  if (isHover) {
    state.isHoverPlaying = true;
  } else {
    state.isLivePlaying = true;
    btnToggleLivePlay?.classList.add('active');
    if (livePlayBtnLabel) livePlayBtnLabel.textContent = 'LIVE ON';
  }

  // Play all videos
  state.capturedSnapshots.forEach((s) => {
    if (s.liveVideo) {
      if (s.liveVideo.paused) {
        s.liveVideo.play().catch(() => {});
      }
    }
  });

  if (!state.liveAnimId) {
    const loop = () => {
      if (!state.isLivePlaying && !state.isHoverPlaying) {
        state.liveAnimId = null;
        return;
      }
      updateStudioPreview(true);
      state.liveAnimId = requestAnimationFrame(loop);
    };
    state.liveAnimId = requestAnimationFrame(loop);
  }
}

function stopLivePlayback(isHover = false) {
  if (isHover) {
    state.isHoverPlaying = false;
  } else {
    state.isLivePlaying = false;
    btnToggleLivePlay?.classList.remove('active');
    if (livePlayBtnLabel) livePlayBtnLabel.textContent = 'LIVE OFF';
  }

  if (!state.isLivePlaying && !state.isHoverPlaying) {
    if (state.liveAnimId) {
      cancelAnimationFrame(state.liveAnimId);
      state.liveAnimId = null;
    }
    state.capturedSnapshots.forEach((s) => {
      if (s.liveVideo) s.liveVideo.pause();
    });
    updateStudioPreview(false);
  }
}

function updateStudioPreview(useLive = false) {
  if (state.capturedSnapshots.length === 0) return;

  const renderedCanvas = stripRenderer.render({
    snapshots: state.capturedSnapshots,
    layout: state.currentMode,
    themeId: state.selectedTheme,
    filterId: state.selectedFilter,
    title: state.stripTitle,
    stickers: state.stickers,
    useLive,
  });

  // Draw rendered canvas to display canvas
  stripCanvas.width = renderedCanvas.width;
  stripCanvas.height = renderedCanvas.height;
  const ctx = stripCanvas.getContext('2d');
  ctx.drawImage(renderedCanvas, 0, 0);
}

// Export Modal Helpers
function showExportModal(title, desc) {
  if (exportModalTitle) exportModalTitle.textContent = title;
  if (exportModalDesc) exportModalDesc.textContent = desc;
  if (exportProgressBar) exportProgressBar.style.width = '0%';
  if (exportProgressPercent) exportProgressPercent.textContent = '0%';
  exportModalOverlay?.classList.add('active');
}

function updateExportProgress(percent) {
  if (exportProgressBar) exportProgressBar.style.width = `${percent}%`;
  if (exportProgressPercent) exportProgressPercent.textContent = `${percent}%`;
}

function hideExportModal() {
  exportModalOverlay?.classList.remove('active');
}

// Add a cute sticker with calculated positions along the photo strip
function addSticker(emoji) {
  if (state.stickers.length >= 12) {
    alert('Maksimal 12 stiker!');
    return;
  }

  // Generate aesthetic positions (near photo corners or borders)
  const marginPresets = [
    { x: 0.12, y: 0.18 },
    { x: 0.88, y: 0.22 },
    { x: 0.14, y: 0.42 },
    { x: 0.86, y: 0.46 },
    { x: 0.12, y: 0.65 },
    { x: 0.88, y: 0.69 },
    { x: 0.15, y: 0.88 },
    { x: 0.85, y: 0.88 },
  ];

  const posIndex = state.stickers.length % marginPresets.length;
  const basePos = marginPresets[posIndex];
  const jitterX = (Math.random() - 0.5) * 0.06;
  const jitterY = (Math.random() - 0.5) * 0.04;

  const newSticker = {
    emoji,
    relX: Math.max(0.08, Math.min(0.92, basePos.x + jitterX)),
    relY: Math.max(0.08, Math.min(0.92, basePos.y + jitterY)),
    size: 42 + Math.floor(Math.random() * 12),
    rotation: (Math.random() - 0.5) * 30, // -15 deg to +15 deg
  };

  state.stickers.push(newSticker);
  stickerCountHint.textContent = `${state.stickers.length} stiker ditempelkan.`;
  updateStudioPreview();
}

// Start app on DOMContentLoaded
window.addEventListener('DOMContentLoaded', () => {
  initApp();
});
