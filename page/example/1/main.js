import { createLockedControl, createVoxisRealtimePlayer, effects } from "./api/voxis-realtime.js"

const $ = (selector) => document.querySelector(selector)

const fileInput = $('#editor-file-input')
const playerHost = $('#player-host')

const player = await createVoxisRealtimePlayer({ container: playerHost})

fileInput.addEventListener("change", async (event) => {
    const [file] = event.target.files || []
    if (!file) {
        return
    }
    await player.loadFile(file);
})

const gainControl = createLockedControl({
    input: '#gain-range',
    output: '#gain-value',
    min: 0.0,
    max: 2.0,
    step: 0.10,
    format: (value) => `${value.toFixed(1)}x`
})

function applyRealtimeEffects() {
    player.setEffects([
        effects.gain({
            value: gainControl.read(),
            limits: { min: 0.0, max: 2.0 }
        })
    ])
}

gainControl.element.addEventListener('input', applyRealtimeEffects)
applyRealtimeEffects()

