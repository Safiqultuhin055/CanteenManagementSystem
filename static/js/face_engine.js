/* Shared face-api.js helper for registration (admin) and recognition (POS).
 *
 * Requires face-api.min.js loaded first and window.FACE_MODEL_URL set to the
 * static model directory, e.g. "/static/vendor/face-api/model".
 *
 * Camera note: getUserMedia only works on a secure context — https:// or
 * localhost/127.0.0.1. On a plain-http LAN host (e.g. http://192.168.x:port)
 * the browser blocks the camera; serve over HTTPS in production.
 */
(function () {
  'use strict';

  var modelsReady = false;
  var loadingPromise = null;

  function isSecure() {
    return window.isSecureContext ||
      location.protocol === 'https:' ||
      location.hostname === 'localhost' ||
      location.hostname === '127.0.0.1';
  }

  function loadModels() {
    if (modelsReady) return Promise.resolve();
    if (loadingPromise) return loadingPromise;
    if (typeof faceapi === 'undefined') {
      return Promise.reject(new Error('face-api library not loaded'));
    }
    var url = window.FACE_MODEL_URL;
    loadingPromise = Promise.all([
      faceapi.nets.tinyFaceDetector.loadFromUri(url),
      faceapi.nets.faceLandmark68Net.loadFromUri(url),
      faceapi.nets.faceRecognitionNet.loadFromUri(url)
    ]).then(function () {
      modelsReady = true;
    });
    return loadingPromise;
  }

  function startCamera(videoEl) {
    if (!isSecure()) {
      return Promise.reject(new Error(
        'Camera needs HTTPS or localhost. Open via https:// or 127.0.0.1.'));
    }
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      return Promise.reject(new Error('Camera not supported in this browser'));
    }
    return navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } },
      audio: false
    }).then(function (stream) {
      videoEl.srcObject = stream;
      return new Promise(function (resolve) {
        videoEl.onloadedmetadata = function () {
          videoEl.play().then(function () { resolve(stream); })
            .catch(function () { resolve(stream); });
        };
      });
    });
  }

  function stopCamera(stream) {
    if (!stream) return;
    stream.getTracks().forEach(function (t) { t.stop(); });
  }

  var _opts = null;
  function detectorOptions() {
    if (!_opts) _opts = new faceapi.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.5 });
    return _opts;
  }

  // Returns a plain Array(128) descriptor, or null if no single face found.
  function captureDescriptor(videoEl) {
    return faceapi
      .detectSingleFace(videoEl, detectorOptions())
      .withFaceLandmarks()
      .withFaceDescriptor()
      .then(function (res) {
        if (!res || !res.descriptor) return null;
        return Array.prototype.slice.call(res.descriptor);
      });
  }

  // Average several descriptors element-wise into one Array(128).
  function averageDescriptors(list) {
    if (!list.length) return null;
    var n = list[0].length;
    var out = new Array(n).fill(0);
    list.forEach(function (d) {
      for (var i = 0; i < n; i++) out[i] += d[i];
    });
    for (var i = 0; i < n; i++) out[i] /= list.length;
    return out;
  }

  window.FaceEngine = {
    isSecure: isSecure,
    loadModels: loadModels,
    startCamera: startCamera,
    stopCamera: stopCamera,
    captureDescriptor: captureDescriptor,
    averageDescriptors: averageDescriptors
  };
})();
