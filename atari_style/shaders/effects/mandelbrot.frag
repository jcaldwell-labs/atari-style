#version 330 core
/*
 * Mandelbrot Set Fragment Shader
 *
 * GPU-accelerated version of the Mandelbrot zoomer animation.
 * Uses smooth coloring with exterior distance estimation for
 * anti-aliased edges at high zoom levels.
 *
 * Uniforms:
 *   iTime       - Animation time for color cycling
 *   iResolution - Viewport resolution (width, height)
 *   iParams     - (zoom, centerX, centerY, maxIterations)
 *   iColorMode  - Color palette selector (0-3)
 */

uniform float iTime;
uniform vec2 iResolution;
uniform vec4 iParams;
uniform int iColorMode;

in vec2 fragCoord;
out vec4 fragColor;

// Cosine-based color palette (Inigo Quilez)
vec3 palette(float t, vec3 a, vec3 b, vec3 c, vec3 d) {
    return a + b * cos(6.28318 * (c * t + d));
}

// Different color schemes
vec3 getColor(float t, int mode) {
    if (mode == 0) {
        // Classic blue-cyan-white (matches CPU version aesthetic)
        vec3 a = vec3(0.0, 0.2, 0.4);
        vec3 b = vec3(0.3, 0.4, 0.5);
        vec3 c = vec3(1.0, 1.0, 1.0);
        vec3 d = vec3(0.0, 0.1, 0.2);
        return palette(t, a, b, c, d);
    } else if (mode == 1) {
        // Fire (red-yellow-white)
        vec3 a = vec3(0.5, 0.1, 0.0);
        vec3 b = vec3(0.5, 0.4, 0.2);
        vec3 c = vec3(1.0, 1.0, 0.5);
        vec3 d = vec3(0.0, 0.25, 0.5);
        return palette(t, a, b, c, d);
    } else if (mode == 2) {
        // Psychedelic rainbow
        vec3 a = vec3(0.5);
        vec3 b = vec3(0.5);
        vec3 c = vec3(1.0);
        vec3 d = vec3(0.0, 0.33, 0.67);
        return palette(t, a, b, c, d);
    } else {
        // Grayscale
        float v = pow(t, 0.5);
        return vec3(v);
    }
}

void main() {
    // Extract parameters
    float zoom = iParams.x;
    vec2 center = iParams.yz;
    float maxIter = iParams.w;

    // Map fragment coordinate to complex plane
    // fragCoord is already in [0, 1] from vertex shader
    vec2 uv = fragCoord - 0.5;

    // Aspect ratio correction for terminal display
    // Terminal chars are ~2x taller than wide, so when the GPU frame
    // is mapped to terminal, X gets compressed. We pre-stretch X here.
    // Standard aspect: uv.x *= iResolution.x / iResolution.y
    // Terminal correction: multiply by additional 2.0 for char aspect
    float terminalCharAspect = 2.0;  // Chars are 2x taller than wide
    uv.x *= (iResolution.x / iResolution.y) * terminalCharAspect;

    // Apply zoom and centering
    vec2 c = center + uv * (3.0 / zoom);

    // Mandelbrot iteration
    vec2 z = vec2(0.0);
    float iter = 0.0;

    // Main iteration loop
    for (int i = 0; i < 500; i++) {
        if (float(i) >= maxIter) break;

        // Escape condition: |z|^2 > 4
        float z2 = dot(z, z);
        if (z2 > 256.0) break;  // Use larger escape radius for smooth coloring

        // z = z^2 + c
        z = vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + c;
        iter += 1.0;
    }

    // Determine color
    vec3 color;

    if (iter >= maxIter) {
        // Inside the set - deep blue/black
        color = vec3(0.0, 0.0, 0.1);
    } else {
        // Outside - smooth coloring with continuous potential
        // Smooth iteration count using potential function
        float log_zn = log(dot(z, z)) / 2.0;
        float nu = log(log_zn / log(2.0)) / log(2.0);
        float smoothIter = iter + 1.0 - nu;

        // Use log scale for better color distribution across iteration ranges
        // This spreads colors more evenly instead of compressing them
        float t = log(smoothIter + 1.0) / log(maxIter + 1.0);

        // Multiply by a factor to get more color bands visible
        t = t * 3.0;

        // Add time-based color cycling - faster and more noticeable
        t = fract(t + iTime * 0.3);

        color = getColor(t, iColorMode);
    }

    fragColor = vec4(color, 1.0);
}
