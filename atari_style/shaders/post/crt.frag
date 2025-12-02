#version 330 core
/*
 * CRT Post-Processing Shader
 *
 * Applies authentic retro CRT monitor effects:
 * - Scanlines with configurable intensity
 * - Barrel distortion (screen curvature)
 * - RGB chromatic aberration
 * - Aperture grille shadow mask
 * - Vignette darkening at edges
 * - Phosphor glow simulation
 *
 * Uniforms:
 *   iChannel0          - Input texture from previous pass
 *   iResolution        - Output resolution
 *   iTime              - Animation time (for flicker effects)
 *   scanlineIntensity  - Scanline darkness (0.0 = none, 1.0 = heavy)
 *   curvature          - Barrel distortion amount (0.0 = flat, 0.3 = curved)
 *   vignetteStrength   - Edge darkening (0.0 = none, 1.0 = heavy)
 *   rgbOffset          - Chromatic aberration (0.0 = none, 0.005 = visible)
 *   brightness         - Overall brightness multiplier
 *   shadowMask         - Shadow mask intensity (0.0 = none, 1.0 = heavy)
 */

uniform sampler2D iChannel0;
uniform vec2 iResolution;
uniform float iTime;

// CRT effect parameters
uniform float scanlineIntensity;   // 0.0 - 1.0
uniform float curvature;           // 0.0 - 0.3
uniform float vignetteStrength;    // 0.0 - 1.0
uniform float rgbOffset;           // 0.0 - 0.01
uniform float brightness;          // 0.8 - 1.5
uniform float shadowMask;          // 0.0 - 1.0
uniform float flickerAmount;       // 0.0 - 0.1 (subtle flicker)

in vec2 fragCoord;
out vec4 fragColor;

// Barrel distortion - curves the screen like an old CRT
vec2 barrelDistort(vec2 uv) {
    // Center coordinates around origin
    vec2 centered = uv * 2.0 - 1.0;

    // Calculate distance from center
    float r2 = dot(centered, centered);

    // Apply barrel distortion
    centered *= 1.0 + curvature * r2;

    // Map back to [0, 1]
    return centered * 0.5 + 0.5;
}

// Scanline effect - horizontal lines like a CRT
float scanline(vec2 uv) {
    // Create scanline pattern based on vertical position
    float line = sin(uv.y * iResolution.y * 3.14159);

    // Shape the scanline (make dark bands narrower)
    line = pow(abs(line), 0.8);

    // Interpolate between full brightness and scanline
    return mix(1.0, line, scanlineIntensity);
}

// RGB shadow mask - simulates aperture grille or slot mask
vec3 shadowMaskPattern(vec2 uv) {
    // Calculate which RGB sub-pixel we're on
    float x = mod(floor(uv.x * iResolution.x), 3.0);

    // Create RGB mask pattern
    vec3 mask;
    if (x < 1.0) {
        mask = vec3(1.0, 0.7, 0.7);  // Red column
    } else if (x < 2.0) {
        mask = vec3(0.7, 1.0, 0.7);  // Green column
    } else {
        mask = vec3(0.7, 0.7, 1.0);  // Blue column
    }

    // Interpolate with white based on shadow mask intensity
    return mix(vec3(1.0), mask, shadowMask);
}

// Vignette - darkens the edges of the screen
float vignette(vec2 uv) {
    // Calculate distance from center
    vec2 centered = uv * 2.0 - 1.0;
    float dist = dot(centered, centered);

    // Smooth vignette falloff
    return 1.0 - dist * vignetteStrength;
}

// Subtle flicker to simulate CRT refresh
float flicker() {
    // High frequency flicker
    float f = sin(iTime * 120.0) * 0.5 + 0.5;
    return 1.0 - flickerAmount * f;
}

void main() {
    // Apply barrel distortion to UV coordinates
    vec2 uv = barrelDistort(fragCoord);

    // Check if we're outside the screen after distortion
    if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
        // Outside screen - render as black bezel
        fragColor = vec4(0.02, 0.02, 0.02, 1.0);
        return;
    }

    // Sample with RGB chromatic aberration
    vec3 col;
    if (rgbOffset > 0.0) {
        // Offset red and blue channels slightly
        col.r = texture(iChannel0, uv + vec2(rgbOffset, 0.0)).r;
        col.g = texture(iChannel0, uv).g;
        col.b = texture(iChannel0, uv - vec2(rgbOffset, 0.0)).b;
    } else {
        col = texture(iChannel0, uv).rgb;
    }

    // Apply scanlines
    col *= scanline(uv);

    // Apply shadow mask
    col *= shadowMaskPattern(uv);

    // Apply vignette
    col *= vignette(uv);

    // Apply flicker
    col *= flicker();

    // Apply brightness
    col *= brightness;

    // Slight bloom/glow effect (brighten bright areas slightly)
    float lum = dot(col, vec3(0.299, 0.587, 0.114));
    col += col * smoothstep(0.5, 1.0, lum) * 0.1;

    // Clamp to valid range
    col = clamp(col, 0.0, 1.0);

    fragColor = vec4(col, 1.0);
}
