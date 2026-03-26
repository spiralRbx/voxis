from __future__ import annotations

import json
import subprocess
import textwrap
from pathlib import Path


def run_node(script: str) -> str:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def test_browser_api_limits_clamp_gain_and_compressor_values() -> None:
    output = run_node(textwrap.dedent(
        """
        import { effects, buildEffectState } from "./api/voxis-realtime-effects.js";

        const state = buildEffectState([
          effects.gain({
            value: 4.0,
            limits: { min: 0.0, max: 2.0 },
          }),
          effects.compressor({
            thresholdDb: -100.0,
            ratio: 99.0,
            limits: {
              thresholdDb: { min: -48.0, max: -1.0 },
              ratio: { min: 1.0, max: 12.0 },
            },
          }),
        ]);

        console.log(JSON.stringify({
          inputGain: state.runtime.inputGain,
          thresholdDb: state.dynamicsConfig.compressor.thresholdDb,
          ratio: state.dynamicsConfig.compressor.ratio,
        }));
        """
    ))
    data = json.loads(output)

    assert data["inputGain"] == 2.0
    assert data["thresholdDb"] == -48.0
    assert data["ratio"] == 12.0


def test_browser_api_hard_clamps_manual_runtime_gain_injection() -> None:
    output = run_node(textwrap.dedent(
        """
        import { buildEffectState } from "./api/voxis-realtime-effects.js";

        const state = buildEffectState([
          {
            stage: "runtime",
            key: "inputGain",
            config: 999.0,
          },
        ]);

        console.log(JSON.stringify({ inputGain: state.runtime.inputGain }));
        """
    ))
    data = json.loads(output)

    assert data["inputGain"] == 4.0


def test_browser_api_collects_app_side_limit_warnings() -> None:
    output = run_node(textwrap.dedent(
        """
        import { effects, buildEffectStateWithWarnings } from "./api/voxis-realtime-effects.js";

        const result = buildEffectStateWithWarnings([
          effects.gain({
            value: 4.0,
            limits: { min: 0.0, max: 2.0 },
          }),
        ]);

        console.log(JSON.stringify({
          warnings: result.warnings,
          inputGain: result.state.runtime.inputGain,
        }));
        """
    ))
    data = json.loads(output)

    assert data["inputGain"] == 2.0
    assert len(data["warnings"]) == 1
    assert data["warnings"][0]["source"] == "javascript"
    assert data["warnings"][0]["parameter"] == "value"
    assert "exceeded app limits" in data["warnings"][0]["message"]


def test_create_locked_control_relocks_dom_value_and_attributes() -> None:
    output = run_node(textwrap.dedent(
        """
        import { createLockedControl } from "./api/voxis-realtime-controls.js";

        const listeners = {};
        const input = {
          value: "4",
          min: "0",
          max: "4",
          step: "0.5",
          addEventListener(name, callback) {
            listeners[name] = callback;
          },
          setAttribute(name, value) {
            this[name] = String(value);
          },
        };
        const output = { textContent: "" };

        const control = createLockedControl({
          input,
          output,
          min: 0.0,
          max: 2.0,
          step: 0.1,
          format: (value) => `${value.toFixed(1)}x`,
        });

        input.max = "99";
        input.value = "4";
        const normalized = control.read();

        console.log(JSON.stringify({
          normalized,
          inputValue: input.value,
          inputMax: input.max,
          outputText: output.textContent,
          hasInputListener: typeof listeners.input === "function",
        }));
        """
    ))
    data = json.loads(output)

    assert data["normalized"] == 2.0
    assert data["inputValue"] == "2"
    assert data["inputMax"] == "2"
    assert data["outputText"] == "2.0x"
    assert data["hasInputListener"] is True


def test_native_wasm_exposes_limits_and_warning_buffer() -> None:
    output = run_node(textwrap.dedent(
        """
        import fs from "node:fs";

        const wasmBytes = fs.readFileSync("./api/voxis-realtime-dynamics.wasm");
        const { instance } = await WebAssembly.instantiate(wasmBytes, {
          env: {
            emscripten_notify_memory_growth() {},
          },
        });
        if (typeof instance.exports.__wasm_call_ctors === "function") {
          instance.exports.__wasm_call_ctors();
        }
        const decoder = new TextDecoder("utf-8");
        const readString = (pointer, length) =>
          decoder.decode(new Uint8Array(instance.exports.memory.buffer, pointer, length));

        const handle = instance.exports.voxis_rt_create(44100, 2, 256);
        instance.exports.voxis_rt_clear_warnings(handle);
        instance.exports.voxis_rt_set_compressor(handle, 1, -120.0, 99.0, -5.0, 9000.0, 80.0);

        const warningPointer = instance.exports.voxis_rt_get_warning_ptr(handle);
        const warningLength = instance.exports.voxis_rt_get_warning_length(handle);
        const limitsPointer = instance.exports.voxis_rt_get_limits_json_ptr();
        const limitsLength = instance.exports.voxis_rt_get_limits_json_length();

        console.log(JSON.stringify({
          warning: readString(warningPointer, warningLength),
          limits: JSON.parse(readString(limitsPointer, limitsLength)),
        }));

        instance.exports.voxis_rt_destroy(handle);
        """
    ))
    data = json.loads(output)

    assert "Compressor parameter" in data["warning"]
    assert "Allowed range" in data["warning"]
    assert data["limits"]["scope"] == "voxis-native-realtime"
    assert "compressorFamily" in data["limits"]["effects"]
    assert "mix" in data["limits"]["parameterRules"]
