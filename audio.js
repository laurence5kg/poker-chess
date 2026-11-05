// Audio Engine using Web Audio API for zero external dependencies
class SoundFX {
    constructor() {
        this.ctx = null;
        this.enabled = true;
        this._setupGestureUnlock();
    }

    _setupGestureUnlock() {
        if (typeof window === 'undefined') return;
        const unlock = () => {
            this.init();
            window.removeEventListener('pointerdown', unlock, true);
            window.removeEventListener('touchstart', unlock, true);
            window.removeEventListener('click', unlock, true);
        };
        window.addEventListener('pointerdown', unlock, true);
        window.addEventListener('touchstart', unlock, true);
        window.addEventListener('click', unlock, true);
    }

    init() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) {
                this.ctx = new AudioCtx();
            }
        }
        if (this.ctx && this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    playMove() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(180, now);
        osc.frequency.exponentialRampToValueAtTime(110, now + 0.08);
        gain.gain.setValueAtTime(0.2, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.08);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.08);
    }

    playCardFlip() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(320, now);
        osc.frequency.exponentialRampToValueAtTime(540, now + 0.07);
        gain.gain.setValueAtTime(0.18, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.07);
        osc.connect(gain);
        gain.connect(this.ctx.destination);
        osc.start(now);
        osc.stop(now + 0.07);
    }

    playClash() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        // Metallic sword-strike effect using high frequency decay
        const osc1 = this.ctx.createOscillator();
        const osc2 = this.ctx.createOscillator();
        const gain = this.ctx.createGain();
        osc1.type = 'sawtooth';
        osc2.type = 'square';
        osc1.frequency.setValueAtTime(880, now);
        osc1.frequency.exponentialRampToValueAtTime(220, now + 0.22);
        osc2.frequency.setValueAtTime(1240, now);
        osc2.frequency.exponentialRampToValueAtTime(440, now + 0.22);
        gain.gain.setValueAtTime(0.3, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.22);
        osc1.connect(gain);
        osc2.connect(gain);
        gain.connect(this.ctx.destination);
        osc1.start(now);
        osc2.start(now);
        osc1.stop(now + 0.22);
        osc2.stop(now + 0.22);
    }

    playBomb() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        // Deep noise blast simulation
        const bufferSize = this.ctx.sampleRate * 0.45;
        const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
        const data = buffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (this.ctx.sampleRate * 0.1));
        }
        const noise = this.ctx.createBufferSource();
        noise.buffer = buffer;
        const filter = this.ctx.createBiquadFilter();
        filter.type = 'lowpass';
        filter.frequency.setValueAtTime(350, now);
        filter.frequency.exponentialRampToValueAtTime(60, now + 0.45);
        const gain = this.ctx.createGain();
        gain.gain.setValueAtTime(0.6, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.45);
        noise.connect(filter);
        filter.connect(gain);
        gain.connect(this.ctx.destination);
        noise.start(now);
    }

    playDefuse() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        [523.25, 659.25, 783.99, 1046.50].forEach((freq, idx) => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, now + idx * 0.06);
            gain.gain.setValueAtTime(0.2, now + idx * 0.06);
            gain.gain.exponentialRampToValueAtTime(0.01, now + idx * 0.06 + 0.18);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(now + idx * 0.06);
            osc.stop(now + idx * 0.06 + 0.18);
        });
    }

    playVictory() {
        if (!this.enabled) return;
        this.init();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const notes = [
            { f: 523.25, d: 0.12 },
            { f: 659.25, d: 0.12 },
            { f: 783.99, d: 0.15 },
            { f: 1046.50, d: 0.45 }
        ];
        let t = now;
        notes.forEach(n => {
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(n.f, t);
            gain.gain.setValueAtTime(0.35, t);
            gain.gain.exponentialRampToValueAtTime(0.01, t + n.d);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start(t);
            osc.stop(t + n.d);
            t += n.d * 0.9;
        });
    }
}

window.soundFX = new SoundFX();
