import streamlit as st
import streamlit.components.v1 as components

# 1. 스트림릿 페이지 설정 (제목 및 레이아웃)
st.set_page_config(page_title="FNF Arrow Edition", layout="centered")

st.title("🎮 FNF Arrow Edition")
st.write("코딩을 몰라도 브라우저에서 바로 즐기는 리듬 게임!")

# 2. 게임 HTML/JavaScript 소스 코드
game_html = """
<div id="game-container" style="text-align: center; background-color: #111; padding: 20px; border-radius: 10px; width: 450px; margin: 0 auto; font-family: sans-serif; color: white; box-shadow: 0 0 20px rgba(255, 0, 127, 0.5);">
    <h3 style="color: #ff007f; margin-top: 0; text-shadow: 0 0 10px #ff007f;">FNF Arrow Edition (HARDCORE)</h3>
    <p style="font-size: 14px; color: #aaa; margin-bottom: 5px;">화면 클릭 후 <span style="color:#00ffff; font-weight:bold;">A S K L</span> 키를 누르세요!</p>
    <p style="font-size: 12px; color: #ff4500; margin-top: 0;">목표: 10,000점 | 허용 MISS: 7회 미만</p>
    <div style="display: flex; justify-content: space-around; font-size: 20px; font-weight: bold; margin-bottom: 10px;">
        <div style="color: #00ffcc;" id="score-display">SCORE: 0</div>
        <div style="color: #ff3333;" id="life-display">LIFE: ❤️ 7</div>
    </div>
    <div style="font-size: 24px; font-weight: bold; height: 35px; margin-bottom: 15px; color: #ff007f; text-shadow: 0 0 8px #ff007f;" id="combo-display">클릭하여 시작</div>
    
    <canvas id="gameCanvas" width="400" height="500" style="border: 3px solid #333; background-color: #0d0d14; border-radius: 5px; cursor: pointer;"></canvas>
</div>

<script>
(function() {
    const canvas = document.getElementById('gameCanvas');
    const ctx = canvas.getContext('2d');
    const scoreDisplay = document.getElementById('score-display');
    const comboDisplay = document.getElementById('combo-display');
    const lifeDisplay = document.getElementById('life-display');

    let score = 0;
    let lastCheckedMilestone = 0;
    let praiseTimer = 0;
    let combo = 0;
    let lives = 7;
    let gameStarted = false;
    let gameOver = false;
    let gameWon = false;

    const NUM_LANES = 4;
    const LANE_WIDTH = 100;
    const JUDGE_LINE_Y = 100; 
    
    const KEYS = ['a', 's', 'k', 'l'];
    const LANE_COLORS = ['#FF1493', '#00FFFF', '#00FF00', '#FF4500']; 
    const ARROWS = ['◀', '▼', '▲', '▶']; 
    
    let keyPressed = [false, false, false, false];
    let notes = [];
    let spawnTimer = 0;
    let musicTimer = 0;

    let bgPulse = 0;
    let audioCtx = null;

    function playBeat(freq, duration, type="square") {
        if (!audioCtx) return;
        try {
            let osc = audioCtx.createOscillator();
            let gain = audioCtx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
            gain.gain.setValueAtTime(0.12, audioCtx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
            osc.connect(gain);
            gain.connect(audioCtx.destination);
            osc.start();
            osc.stop(audioCtx.currentTime + duration);
        } catch(e) { }
    }

    function updateMusic() {
        musicTimer++;
        if (musicTimer % 12 === 0) {
            let beatCount = musicTimer / 12;
            if (beatCount % 4 === 0) {
                playBeat(85, 0.2, "sine");
            } else if (beatCount % 4 === 2) {
                playBeat(160, 0.15, "triangle");
            }
            let notes_freq = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25];
            let f = notes_freq[Math.floor(Math.random() * notes_freq.length)];
            if (beatCount % 2 === 0) {
                playBeat(f, 0.12, "square");
            }
        }
    }

    canvas.addEventListener('click', () => {
        if (!gameStarted) {
            gameStarted = true;
            gameOver = false;
            gameWon = false;
            score = 0;
            lastCheckedMilestone = 0;
            praiseTimer = 0;
            combo = 0;
            lives = 7;
            notes = [];
            musicTimer = 0;
            scoreDisplay.innerText = "SCORE: 0";
            lifeDisplay.innerText = "LIFE: ❤️ 7";
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
            comboDisplay.innerText = "START!!";
            comboDisplay.style.color = "#00ffcc";
            gameLoop();
        } else if (gameOver || gameWon) {
            gameStarted = false;
            ctx.fillStyle = '#0d0d14';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#00ffcc';
            ctx.font = 'bold 22px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('CLICK TO RESTART', canvas.width / 2, canvas.height / 2);
        }
    });

    window.addEventListener('keydown', (e) => {
        if (!gameStarted || gameOver || gameWon) return;
        const key = e.key.toLowerCase();
        const index = KEYS.indexOf(key);
        if (index !== -1) {
            if (!keyPressed[index]) {
                keyPressed[index] = true;
                checkHit(index);
            }
        }
    });

    window.addEventListener('keyup', (e) => {
        if (!gameStarted || gameOver || gameWon) return;
        const key = e.key.toLowerCase();
        const index = KEYS.indexOf(key);
        if (index !== -1) {
            keyPressed[index] = false;
        }
    });

    function reduceLife() {
        lives--;
        if (lives <= 0) {
            lives = 0;
            gameOver = true;
        }
        lifeDisplay.innerText = "LIFE: " + "❤️".repeat(lives) + (lives === 0 ? "❌ GAME OVER" : "");
    }

    function checkHit(lane) {
        let hitDetected = false;
        for (let i = 0; i < notes.length; i++) {
            if (notes[i].lane === lane) {
                let distance = Math.abs(notes[i].y - JUDGE_LINE_Y);
                if (distance < 50) { 
                    score += 100;
                    combo += 1;
                    playBeat(587.33, 0.05, "sine");
                    if (distance < 22) {
                        comboDisplay.innerText = "SICK!! (" + combo + ")";
                        comboDisplay.style.color = "#00ffff";
                    } else {
                        comboDisplay.innerText = "GOOD (" + combo + ")";
                        comboDisplay.style.color = "#00ff00";
                    }
                    scoreDisplay.innerText = "SCORE: " + score;
                    
                    let currentMilestone = Math.floor(score / 1000);
                    if (currentMilestone > lastCheckedMilestone && score < 10000) {
                        lastCheckedMilestone = currentMilestone;
                        praiseTimer = 45;
                        comboDisplay.innerText = "🎉 잘했어요! 🎉";
                        comboDisplay.style.color = "#ffff00";
                        playBeat(880, 0.15, "triangle");
                    }
                    if (score >= 10000) {
                        gameWon = true;
                    }
                    notes.splice(i, 1);
                    hitDetected = true;
                    break;
                }
            }
        }
        if (!hitDetected) {
            combo = 0;
            comboDisplay.innerText = "MISS";
            comboDisplay.style.color = "#ff0055";
            playBeat(110, 0.12, "sawtooth"); 
            reduceLife();
        }
    }

    function drawArrow(x, y, lane, color, isFrame) {
        ctx.font = "bold 65px sans-serif"; 
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        if (isFrame) {
            ctx.strokeStyle = color;
            ctx.lineWidth = keyPressed[lane] ? 6 : 3;
            ctx.fillStyle = keyPressed[lane] ? color + '44' : 'transparent';
            ctx.strokeText(ARROWS[lane], x, y);
            if (keyPressed[lane]) {
                ctx.fillText(ARROWS[lane], x, y);
            }
        } else {
            ctx.fillStyle = color;
            ctx.shadowBlur = 15; 
            ctx.shadowColor = color;
            ctx.fillText(ARROWS[lane], x, y);
            ctx.shadowBlur = 0;
        }
    }

    function gameLoop() {
        ctx.fillStyle = '#0a0a10';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        if (!gameOver && !gameWon) {
            updateMusic();
        }

        bgPulse += 0.5;
        ctx.strokeStyle = 'rgba(255, 0, 127, 0.05)';
        ctx.lineWidth = 2;
        for (let y = 0; y < canvas.height; y += 40) {
            ctx.beginPath();
            ctx.moveTo(0, (y + bgPulse) % canvas.height);
            ctx.lineTo(canvas.width, (y + bgPulse) % canvas.height);
            ctx.stroke();
        }

        ctx.strokeStyle = 'rgba(0, 255, 204, 0.2)';
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(0, JUDGE_LINE_Y);
        ctx.lineTo(canvas.width, JUDGE_LINE_Y);
        ctx.stroke();

        for (let i = 0; i < NUM_LANES; i++) {
            if (keyPressed[i]) {
                let gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
                gradient.addColorStop(0, LANE_COLORS[i] + '33');
                gradient.addColorStop(1, 'transparent');
                ctx.fillStyle = gradient;
                ctx.fillRect(i * LANE_WIDTH, 0, LANE_WIDTH, canvas.height);
            }
            ctx.strokeStyle = 'rgba(45, 45, 61, 0.5)';
            ctx.lineWidth = 1;
            ctx.strokeRect(i * LANE_WIDTH, 0, LANE_WIDTH, canvas.height);
        }

        for (let i = 0; i < NUM_LANES; i++) {
            let laneCenterX = i * LANE_WIDTH + (LANE_WIDTH / 2);
            let frameColor = keyPressed[i] ? LANE_COLORS[i] : '#444454';
            drawArrow(laneCenterX, JUDGE_LINE_Y, i, frameColor, true);
        }

        if (gameOver) {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#ff0055';
            ctx.font = 'bold 40px sans-serif';
            ctx.fillText('FAIL... 😢', canvas.width / 2, canvas.height / 2 - 20);
            ctx.fillStyle = '#ffffff';
            ctx.font = '20px sans-serif';
            ctx.fillText('7번 이상 놓쳤습니다.', canvas.width / 2, canvas.height / 2 + 30);
            ctx.font = '16px sans-serif';
            ctx.fillStyle = '#888';
            ctx.fillText('화면을 클릭하여 재시작', canvas.width / 2, canvas.height / 2 + 80);
            comboDisplay.innerText = "GAME OVER";
            comboDisplay.style.color = "#ff0055";
            return; 
        }

        if (gameWon) {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.85)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#00ffcc';
            ctx.font = 'bold 40px sans-serif';
            ctx.fillText('STAGE CLEAR! 🎉', canvas.width / 2, canvas.height / 2 - 20);
            ctx.fillStyle = '#ffffff';
            ctx.font = '20px sans-serif';
            ctx.fillText('최종 점수: ' + score, canvas.width / 2, canvas.height / 2 + 30);
            ctx.font = '16px sans-serif';
            ctx.fillStyle = '#888';
            ctx.fillText('화면을 클릭하여 재시작', canvas.width / 2, canvas.height / 2 + 80);
            comboDisplay.innerText = "VICTORY!!";
            comboDisplay.style.color = "#00ffcc";
            playBeat(880, 0.2, "sine");
            return; 
        }

        spawnTimer++;
        if (spawnTimer > 12) { 
            let randomLane = Math.floor(Math.random() * NUM_LANES);
            notes.push({ lane: randomLane, y: canvas.height + 40, speed: 11 });
            spawnTimer = 0;
        }

        for (let i = notes.length - 1; i >= 0; i--) {
            notes[i].y -= notes[i].speed; 
            let laneCenterX = notes[i].lane * LANE_WIDTH + (LANE_WIDTH / 2);
            drawArrow(laneCenterX, notes[i].y, notes[i].lane, LANE_COLORS[notes[i].lane], false);

            if (notes[i].y < 30) {
                notes.splice(i, 1);
                combo = 0;
                comboDisplay.innerText = "MISS";
                comboDisplay.style.color = "#ff0055";
                playBeat(100, 0.1, "sawtooth");
                reduceLife(); 
            }
        }

        if (praiseTimer > 0) {
            ctx.save();
            ctx.font = 'bold 44px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillStyle = '#ffff00';
            ctx.shadowBlur = 20;
            ctx.shadowColor = '#ffff00';
            ctx.fillText('잘했어요! 👍', canvas.width / 2, canvas.height / 2 + 50);
            ctx.restore();
            praiseTimer--;
        }

        requestAnimationFrame(gameLoop);
    }

    ctx.fillStyle = '#0d0d14';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#00ffcc';
    ctx.font = 'bold 22px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('CLICK TO START GAME', canvas.width / 2, canvas.height / 2);
})();
</script>
"""

# 3. 스트림릿 컴포넌트로 HTML 삽입 (여백 확보를 위해 크기 600x700으로 지정)
components.html(game_html, height=700, width=600)
