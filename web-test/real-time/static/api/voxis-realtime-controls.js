function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function toFiniteNumber(value, fallback) {
  const number = Number(value);
  return Number.isFinite(number) ? number : Number(fallback);
}

function resolveElement(target, label) {
  if (!target) {
    throw new Error(`Missing Voxis realtime control ${label}.`);
  }
  if (typeof target === "string") {
    if (typeof document === "undefined") {
      throw new Error(`Cannot resolve selector ${target} without a document.`);
    }
    const element = document.querySelector(target);
    if (!element) {
      throw new Error(`Could not find element for selector ${target}.`);
    }
    return element;
  }
  return target;
}

function quantize(value, step, min) {
  if (!(step > 0.0)) {
    return value;
  }
  const offset = (value - min) / step;
  return min + Math.round(offset) * step;
}

function normalizeValue(value, config) {
  const numeric = toFiniteNumber(value, config.fallback);
  const quantized = quantize(numeric, config.step, config.min);
  const clamped = clamp(quantized, config.min, config.max);
  return Number(clamped.toFixed(config.precision));
}

function getPrecision(step) {
  if (!Number.isFinite(step) || step <= 0.0) {
    return 6;
  }
  const text = String(step);
  if (!text.includes(".")) {
    return 0;
  }
  return Math.min(8, text.length - text.indexOf(".") - 1);
}

function assignNumericAttribute(element, name, value) {
  const text = String(value);
  if (name in element) {
    element[name] = text;
  }
  if (typeof element.setAttribute === "function") {
    element.setAttribute(name, text);
  }
}

export function createLockedControl({
  input,
  output = null,
  min = 0.0,
  max = 1.0,
  step = 0.01,
  fallback = min,
  format = (value) => String(value),
  onChange = null,
  listen = true,
} = {}) {
  const inputElement = resolveElement(input, "input");
  const outputElement = output ? resolveElement(output, "output") : null;
  const config = {
    min: Math.min(toFiniteNumber(min, 0.0), toFiniteNumber(max, 1.0)),
    max: Math.max(toFiniteNumber(min, 0.0), toFiniteNumber(max, 1.0)),
    step: Math.max(0.0, toFiniteNumber(step, 0.0)),
    fallback: toFiniteNumber(fallback, min),
    precision: getPrecision(toFiniteNumber(step, 0.0)),
  };

  function lockAttributes() {
    assignNumericAttribute(inputElement, "min", config.min);
    assignNumericAttribute(inputElement, "max", config.max);
    if (config.step > 0.0) {
      assignNumericAttribute(inputElement, "step", config.step);
    }
  }

  function render(value) {
    const normalized = normalizeValue(value, config);
    assignNumericAttribute(inputElement, "value", normalized);
    if ("value" in inputElement) {
      inputElement.value = String(normalized);
    }
    if (outputElement) {
      outputElement.textContent = format(normalized);
    }
    return normalized;
  }

  function read() {
    lockAttributes();
    return render(inputElement.value);
  }

  function write(value) {
    lockAttributes();
    return render(value);
  }

  const control = {
    element: inputElement,
    output: outputElement,
    min: config.min,
    max: config.max,
    step: config.step,
    read,
    write,
    lock() {
      lockAttributes();
      return render(inputElement.value);
    },
    get value() {
      return read();
    },
  };

  if (listen && typeof inputElement.addEventListener === "function") {
    const handleChange = () => {
      const value = read();
      if (typeof onChange === "function") {
        onChange(value, control);
      }
    };
    inputElement.addEventListener("input", handleChange);
    inputElement.addEventListener("change", handleChange);
  }

  control.lock();

  return control;
}
