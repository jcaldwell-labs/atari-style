#version 330 core
/*
 * Fluid Lattice Fragment Shader
 *
 * Simulates water ripple effects with procedural wave interference.
 * Uses multiple overlapping circular waves to create fluid-like motion.
 *
 * Note: This is a procedural approximation. For true wave equation simulation,
 * use ping-pong buffers with fluid_sim.frag (Phase 5).
 *
 * Uniforms:
 *   iTime       - Animation time
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (rain_rate, wave_speed, drop_strength, damping)
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
        // Water (blue-cyan-white)
        vec3 a = vec3(0.0, 0.2, 0.4);
        vec3 b = vec3(0.2, 0.4, 0.5);
        vec3 c = vec3(1.0, 1.0, 0.5);
        vec3 d = vec3(0.0, 0.1, 0.2);
        return palette(t, a, b, c, d);
    } else if (mode == 1) {
        // Mercury (silver-gray)
        vec3 a = vec3(0.4, 0.4, 0.45);
        vec3 b = vec3(0.3, 0.3, 0.35);
        vec3 c = vec3(1.0, 1.0, 1.0);
        vec3 d = vec3(0.0, 0.05, 0.1);
        return palette(t, a, b, c, d);
    } else if (mode == 2) {
        // Lava (red-orange-yellow)
        vec3 a = vec3(0.5, 0.2, 0.0);
        vec3 b = vec3(0.5, 0.3, 0.1);
        vec3 c = vec3(1.0, 0.8, 0.4);
        vec3 d = vec3(0.0, 0.1, 0.2);
        return palette(t, a, b, c, d);
    } else {
        // Grayscale ripples
        return vec3(t * 0.8 + 0.1);
    }
}

// Hash function for pseudo-random drop positions
float hash(float n) {
    return fract(sin(n) * 43758.5453123);
}

vec2 hash2(float n) {
    return vec2(hash(n), hash(n + 57.0));
}

// Single wave ripple from a point
float ripple(vec2 uv, vec2 center, float time, float speed, float strength) {
    float dist = length(uv - center);
    float wave = sin(dist * 20.0 - time * speed * 10.0) * strength;

    // Decay with distance and time since drop
    float decay = exp(-dist * 2.0) * exp(-time * 0.5);

    return wave * decay;
}

void main() {
    // Extract parameters
    float rainRate = iParams.x;         // How often drops occur (0.1 = sparse, 0.5 = heavy)
    float waveSpeed = iParams.y;        // How fast waves propagate
    float dropStrength = iParams.z;     // Amplitude of drops
    float damping = iParams.w;          // How quickly waves decay (higher = less damping)

    // Scale damping for shader (CPU uses 0.95-0.99, we need inverse behavior)
    float dampingFactor = 1.0 - (1.0 - damping) * 2.0;
    dampingFactor = max(0.1, dampingFactor);

    // UV coordinates
    vec2 uv = fragCoord;

    // Aspect ratio correction
    uv.x *= iResolution.x / iResolution.y;

    // Accumulate waves from multiple drops
    float totalWave = 0.0;

    // Number of concurrent drops based on rain rate
    int numDrops = int(5.0 + rainRate * 15.0);

    for (int i = 0; i < 20; i++) {
        if (i >= numDrops) break;

        // Each drop has a different timing cycle
        float dropCycle = 3.0 + hash(float(i)) * 2.0;  // 3-5 second cycles
        float dropPhase = hash(float(i) * 7.0);

        // Time within this drop's cycle
        float dropTime = mod(iTime + dropPhase * dropCycle, dropCycle);

        // Drop position (pseudo-random but repeatable)
        vec2 dropPos = hash2(float(i) * 13.0 + floor((iTime + dropPhase * dropCycle) / dropCycle) * 0.1);

        // Center the drop positions
        dropPos = dropPos * 0.8 + 0.1;  // Keep drops away from edges
        dropPos.x *= iResolution.x / iResolution.y;  // Aspect correction

        // Add this drop's ripple
        float strength = dropStrength * (0.5 + hash(float(i) * 31.0) * 0.5);
        totalWave += ripple(uv, dropPos, dropTime, waveSpeed, strength) * dampingFactor;
    }

    // Add subtle base waves for ambient motion
    totalWave += sin(uv.x * 10.0 + iTime * waveSpeed) * 0.05;
    totalWave += sin(uv.y * 12.0 + iTime * waveSpeed * 1.1) * 0.04;

    // Map wave height to visual
    // Positive values = peaks (lighter), negative = troughs (darker)
    float normalizedWave = totalWave * 0.5 + 0.5;
    normalizedWave = clamp(normalizedWave, 0.0, 1.0);

    // Get color
    vec3 color = getColor(normalizedWave, iColorMode);

    // Add specular highlights on wave peaks
    float highlight = smoothstep(0.6, 0.9, normalizedWave);
    color += vec3(highlight * 0.3);

    // Add shadow in troughs
    float shadow = smoothstep(0.4, 0.1, normalizedWave);
    color *= 1.0 - shadow * 0.3;

    fragColor = vec4(color, 1.0);
}
