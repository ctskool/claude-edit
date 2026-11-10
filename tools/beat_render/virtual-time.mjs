// Exact copy of the virtual time shim from HyperFrames 0.8.184, unchanged in 0.9.13; package unchanged.
function buildVirtualTimeShim(options) {
  const seedRandomFromFrame = options.seedRandomFromFrame === true;
  const seededRandomBlock = seedRandomFromFrame ? String.raw`
  // Seeded Math.random / crypto.getRandomValues, keyed by virtual time.
  // Mulberry32: single uint32 state, deterministic, fast.
  var rngState = 0;
  function mulberry32() {
    rngState |= 0; rngState = (rngState + 0x6D2B79F5) | 0;
    var t = rngState;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  function reseedRngFromTime(ms) {
    var ms32 = Math.max(0, Math.floor(Number(ms) || 0)) | 0;
    // Knuth's multiplicative hash + golden-ratio offset gives a well-
    // distributed seed even for frame 0 (otherwise rngState=0 degenerates
    // the PRNG's first few outputs).
    rngState = (Math.imul(ms32, -1640531527) + 0x9E3779B9) | 0;
  }
  reseedRngFromTime(0);
  try {
    Math.random = function() { return mulberry32(); };
  } catch (e) {}
  if (window.crypto && typeof window.crypto.getRandomValues === "function") {
    try {
      var __seededGetRandomValues = function(arr) {
        if (!arr || typeof arr.byteLength !== "number" || !arr.buffer) return arr;
        var byteLen = arr.byteLength;
        if (byteLen <= 0) return arr;
        var view = new DataView(arr.buffer, arr.byteOffset, byteLen);
        var i = 0;
        for (; i + 4 <= byteLen; i += 4) {
          var word = ((mulberry32() * 4294967296) >>> 0);
          view.setUint32(i, word, true);
        }
        for (; i < byteLen; i++) {
          view.setUint8(i, (mulberry32() * 256) | 0);
        }
        return arr;
      };
      window.crypto.getRandomValues = __seededGetRandomValues;
    } catch (e) {}
  }
` : "";
  const seekToTimeReseedCall = seedRandomFromFrame ? "reseedRngFromTime(safeTimeMs);\n      " : "";
  return String.raw`(function() {
  if (window.__HF_VIRTUAL_TIME__) return;

  var virtualNowMs = 0;
  var rafId = 1;
  var rafQueue = [];
  var OriginalDate = Date;
  var originalSetTimeout = window.setTimeout.bind(window);
  var originalClearTimeout = window.clearTimeout.bind(window);
  var originalSetInterval = window.setInterval.bind(window);
  var originalClearInterval = window.clearInterval.bind(window);
  var originalRequestAnimationFrame = window.requestAnimationFrame
    ? window.requestAnimationFrame.bind(window)
    : null;
  var originalCancelAnimationFrame = window.cancelAnimationFrame
    ? window.cancelAnimationFrame.bind(window)
    : null;
${seededRandomBlock}
  function flushAnimationFrame() {
    if (!rafQueue.length) return;
    var current = rafQueue.slice();
    rafQueue.length = 0;
    for (var i = 0; i < current.length; i++) {
      var entry = current[i];
      if (entry.cancelled) continue;
      try {
        entry.callback(virtualNowMs);
      } catch {}
    }
  }

  function VirtualDate() {
    var args = Array.prototype.slice.call(arguments);
    if (!(this instanceof VirtualDate)) {
      return OriginalDate.apply(null, args.length ? args : [virtualNowMs]);
    }
    var instance = args.length ? new (Function.prototype.bind.apply(OriginalDate, [null].concat(args)))() : new OriginalDate(virtualNowMs);
    Object.setPrototypeOf(instance, VirtualDate.prototype);
    return instance;
  }

  VirtualDate.prototype = OriginalDate.prototype;
  Object.setPrototypeOf(VirtualDate, OriginalDate);
  VirtualDate.now = function() { return virtualNowMs; };
  VirtualDate.parse = OriginalDate.parse.bind(OriginalDate);
  VirtualDate.UTC = OriginalDate.UTC.bind(OriginalDate);

  try {
    Object.defineProperty(window, "Date", {
      configurable: true,
      writable: true,
      value: VirtualDate,
    });
  } catch {}

  if (window.performance && typeof window.performance.now === "function") {
    try {
      Object.defineProperty(window.performance, "now", {
        configurable: true,
        value: function() { return virtualNowMs; },
      });
    } catch {}
  }

  window.requestAnimationFrame = function(callback) {
    if (typeof callback !== "function") return 0;
    var entry = { id: rafId++, callback: callback, cancelled: false };
    rafQueue.push(entry);
    return entry.id;
  };
  window.cancelAnimationFrame = function(id) {
    for (var i = 0; i < rafQueue.length; i++) {
      if (rafQueue[i].id === id) {
        rafQueue[i].cancelled = true;
      }
    }
  };

  window.__HF_VIRTUAL_TIME__ = {
    originalSetTimeout: originalSetTimeout,
    originalClearTimeout: originalClearTimeout,
    originalSetInterval: originalSetInterval,
    originalClearInterval: originalClearInterval,
    originalRequestAnimationFrame: originalRequestAnimationFrame,
    originalCancelAnimationFrame: originalCancelAnimationFrame,
    seekToTime: function(nextTimeMs) {
      var safeTimeMs = Math.max(0, Number(nextTimeMs) || 0);
      virtualNowMs = safeTimeMs;
      ${seekToTimeReseedCall}flushAnimationFrame();
      return virtualNowMs;
    },
    getTime: function() {
      return virtualNowMs;
    },
  };
})();`;
}
export {buildVirtualTimeShim};