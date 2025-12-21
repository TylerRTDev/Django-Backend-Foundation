// Paste full JavaScript from canvas

const canvas = document.getElementById('binaryRain');
const ctx = canvas.getContext('2d');

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();

const binary = "010";
const binaryChars = binary.split("");
const particles = [];
// Adjust number of particles based on screen size
let maxParticles = 350;

if (window.innerWidth < 800) {
    maxParticles = 400;
} else if (window.innerWidth < 1200) {
    maxParticles;
}

class BinaryParticle {
    constructor() {
        this.baseX = Math.random() * canvas.width;
        this.baseY = Math.random() * canvas.height;
        this.x = this.baseX;
        this.y = this.baseY;
        this.char = binaryChars[Math.floor(Math.random() * binaryChars.length)];
        const fonts = ['JetBrains Mono', 'Goldman', 'Zen Dots', 'Press Start 2P'];
        this.fontFamily = fonts[Math.floor(Math.random() * fonts.length)];
        this.fontSize = 24 + Math.random() * 16;
        this.opacity = 0.3 + Math.random() * 0.5;
        this.baseOpacity = this.opacity;
        this.breatheSpeed = 0.004 + Math.random() * 0.01;
        this.breatheRadius = 90 + Math.random() * 50;
        this.hoverSpeed = 0.005 + Math.random() * 0.01;
        this.hoverRadius = 8 + Math.random() * 15;
        this.breathePhase = Math.random() * Math.PI * 2;
        this.hoverPhaseX = Math.random() * Math.PI * 2;
        this.hoverPhaseY = Math.random() * Math.PI * 2;
        this.scaleSpeed = 0.008 + Math.random() * 0.012;
        this.scalePhase = Math.random() * Math.PI * 2;
        this.baseScale = 0.8 + Math.random() * 0.4;
        this.time = 0;

        if (window.innerWidth < 800) {
            this.fontSize = 24 + Math.random() * 12;
            this.breatheRadius = 60 + Math.random() * 30;
            this.hoverRadius = 5 + Math.random() * 10;
            this.baseScale = 0.6 + Math.random() * 0.3;
        }
    }

    update() {
        this.time += 0.05;
        const breatheOffset = Math.sin(this.time * this.breatheSpeed + this.breathePhase) * this.breatheRadius;
        const hoverX = Math.sin(this.time * this.hoverSpeed + this.hoverPhaseX) * (this.hoverRadius * 2.5);
        const hoverY = Math.cos(this.time * this.hoverSpeed * 0.7 + this.hoverPhaseY) * (this.hoverRadius * 0.6);
        this.x = this.baseX + hoverX;
        this.y = this.baseY + breatheOffset + hoverY;
        const opacityPulse = Math.sin(this.time * this.breatheSpeed * 1.5 + this.breathePhase) * 0.2;
        this.opacity = this.baseOpacity + opacityPulse;
        const scalePulse = Math.sin(this.time * this.scaleSpeed + this.scalePhase) * 0.3;
        this.scale = this.baseScale + scalePulse;

        if (Math.random() < 0.002) {
            this.char = binaryChars[Math.floor(Math.random() * binaryChars.length)];
        }

        if (this.baseX < -50 || this.baseX > canvas.width + 50) {
            this.baseX = Math.random() * canvas.width;
        }
        if (this.baseY < -50 || this.baseY > canvas.height + 50) {
            this.baseY = Math.random() * canvas.height;
        }
    }

    draw() {
        ctx.save();
        ctx.globalAlpha = Math.max(0.1, Math.min(1, this.opacity));
        ctx.fillStyle = '#00ff41';
        ctx.translate(this.x, this.y);
        ctx.scale(this.scale, this.scale);
        ctx.translate(-this.x, -this.y);
        ctx.font = this.fontSize + 'px ' + this.fontFamily + ', monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.char, this.x, this.y);
        ctx.restore();
    }
}

function initParticles() {
    particles.length = 0;
    for (let i = 0; i < maxParticles; i++) {
        particles.push(new BinaryParticle());
    }
}
initParticles();

function drawHoveringBinary() {
    ctx.fillStyle = 'rgba(10, 14, 26, 0.03)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    particles.forEach(particle => {
        particle.update();
        particle.draw();
    });
}

function animate() {
    drawHoveringBinary();
    requestAnimationFrame(animate);
}
animate();

window.addEventListener('resize', function() {
    resizeCanvas();
    initParticles();
});

setInterval(() => {
    if (Math.random() < 0.05) {
        document.body.style.filter = 'hue-rotate(5deg)';
        setTimeout(() => {
            document.body.style.filter = 'none';
        }, 50);
    }
}, 8000);

document.addEventListener('DOMContentLoaded', function() {
    const terminal = document.querySelector('.terminal-window');
    terminal.style.opacity = '0';
    terminal.style.transform = 'translateY(20px)';
    setTimeout(() => {
        terminal.style.transition = 'all 1s ease';
        terminal.style.opacity = '1';
        terminal.style.transform = 'translateY(0)';
    }, 500);
});