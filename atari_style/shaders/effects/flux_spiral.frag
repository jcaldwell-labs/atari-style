#version 330 core
/*
 * Flux-Spiral Composite Fragment Shader
 *
 * Combines fluid/wave simulation with spiral pattern where the
 * fluid wave energy modulates the spiral's rotation speed and
 * visual intensity.
 *
 * Uniforms:
 *   iTime       - Animation time
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (wave_freq, base_rotation, modulation_strength, num_spirals)
 *   iColorMode  - Color palette selector (0-3)
 */

uniform float iTime;
uniform vec2 iResolution;
uniform vec4 iParams;
uniform int iColorMode;

in vec2 fragCoord;
out vec4 fragColor;

const float PI = 3.14159265358979323846;
const float TAU = 6.28318530717958647692;

// Cosine-based color palette
vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(TAU * (c * t + d));
}

vec3 getColor(float t, int mode) {
    if (mode == 0) {
        // Aqua vortex
        vec3 a = vec3(0.0, 0.3, 0.5);
        vec3 b = vec3(0.3, 0.4, 0.4);
        vec3 c = vec3(1.0, 1.0, 0.5);
        vec3 d = vec3(0.0, 0.15, 0.3);
        return palette(t, a, b, c, d);
    } else if (mode == 1) {
        // Psychedelic spiral
        vec3 a = vec3(0.5);
        vec3 b = vec3(0.5);
        vec3 c = vec3(1.0);
        vec3 d = vec3(0.0, 0.33, 0.67);
        return palette(t, a, b, c, d);
    } else if (mode == 2) {
        // Energy vortex (purple-cyan)
        vec3 a = vec3(0.3, 0.2, 0.5);
        vec3 b = vec3(0.3, 0.4, 0.4);
        vec3 c = vec3(1.0, 1.0, 0.5);
        vec3 d = vec3(0.5, 0.2, 0.7);
        return palette(t, a, b, c, d);
    } else {
        // Monochrome wave
        return vec3(t * 0.9 + 0.1);
    }
}

// Hash function for pseudo-random values
float hash(float n) {
    return fract(sin(n) * 43758.5453123);
}

vec2 hash2(float n) {
    return vec2(hash(n), hash(n + 57.0));
}

// Compute wave energy at a point (simplified fluid simulation)
float computeWaveEnergy(vec2 uv, float freq, float t) {
    float energy = 0.0;

    // Multiple wave sources
    for (int i = 0; i < 5; i++) {
        float dropCycle = 2.0 + hash(float(i)) * 2.0;
        float dropPhase = hash(float(i) * 7.0);
        float dropTime = mod(t + dropPhase * dropCycle, dropCycle);

        vec2 dropPos = hash2(float(i) * 13.0 + floor((t + dropPhase * dropCycle) / dropCycle) * 0.1);
        dropPos = dropPos * 0.6 + 0.2;

        float dist = length(uv - dropPos);
        float wave = sin(dist * 20.0 * freq - dropTime * 10.0);
        float decay = exp(-dist * 3.0) * exp(-dropTime * 0.8);

        energy += abs(wave * decay);
    }

    return clamp(energy, 0.0, 1.0);
}

// Get global wave energy (average across field)
float getGlobalWaveEnergy(float freq, float t) {
    float total = 0.0;
    total += computeWaveEnergy(vec2(0.3, 0.3), freq, t);
    total += computeWaveEnergy(vec2(0.5, 0.5), freq, t);
    total += computeWaveEnergy(vec2(0.7, 0.7), freq, t);
    return total / 3.0;
}

void main() {
    // Extract parameters
    float waveFreq = iParams.x;              // Wave frequency (default ~0.3)
    float baseRotation = iParams.y;          // Base rotation speed (default ~1.0)
    float modStrength = iParams.z;           // How much waves affect spiral
    float numSpirals = max(1.0, iParams.w * 10.0);  // Number of spiral arms

    // Get wave energy modulation
    float waveEnergy = getGlobalWaveEnergy(waveFreq, iTime);

    // Modulate rotation speed based on wave energy
    float rotationSpeed = baseRotation + waveEnergy * modStrength * 3.0;

    // Center coordinate system
    vec2 uv = fragCoord - 0.5;
    uv.x *= iResolution.x / iResolution.y;

    // Convert to polar coordinates
    float r = length(uv);
    float theta = atan(uv.y, uv.x);

    // Calculate spiral with modulated rotation
    float tightness = 8.0;
    float rotation = iTime * rotationSpeed;
    float spiral = sin(theta * numSpirals + r * tightness - rotation);
    float spiralVal = spiral * 0.5 + 0.5;

    // Compute local wave effect for visual texture
    float localWave = computeWaveEnergy(fragCoord, waveFreq * 0.5, iTime);

    // Combine spiral and wave patterns
    float combined = spiralVal * (0.7 + localWave * 0.3);

    // Add color cycling based on energy
    float colorT = fract(combined + waveEnergy * 0.2 + iTime * 0.1);

    // Get color
    vec3 color = getColor(colorT, iColorMode);

    // Add energy-based brightness modulation
    float brightness = 0.8 + waveEnergy * 0.4;
    color *= brightness;

    // Vignette effect
    float vignette = 1.0 - smoothstep(0.5, 1.2, r);
    color *= vignette;

    // Add wave highlights
    color += vec3(localWave * 0.2) * getColor(0.5, iColorMode);

    fragColor = vec4(color, 1.0);
}
