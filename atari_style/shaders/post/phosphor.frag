#version 330 core
/*
 * Phosphor Persistence Post-Processing Shader
 *
 * Simulates the phosphor decay effect of CRT monitors where
 * bright pixels leave a fading trail. The phosphor coating
 * continues to glow briefly after the electron beam moves on,
 * creating the characteristic "ghosting" effect.
 *
 * This effect is especially visible on:
 * - Fast-moving objects (motion blur effect)
 * - Bright elements against dark backgrounds
 * - Text scrolling on terminals
 *
 * Uniforms:
 *   iChannel0        - Current frame texture
 *   iChannel1        - Previous frame texture (for persistence)
 *   iResolution      - Output resolution
 *   iTime            - Animation time (for subtle flicker)
 *   persistence      - How long the glow persists (0.0 = none, 0.95 = heavy)
 *   glowIntensity    - Brightness of the glow trail (0.0 - 2.0)
 *   colorBleed       - RGB decay rate difference (0.0 = uniform, 0.5 = colored trails)
 *   burnIn           - Static element burn-in simulation (0.0 - 0.3)
 *
 * Technical note: Requires ping-pong framebuffer setup - the previous
 * frame output must be fed back as iChannel1.
 */

uniform sampler2D iChannel0;    // Current frame
uniform sampler2D iChannel1;    // Previous frame (for persistence feedback)
uniform vec2 iResolution;
uniform float iTime;

// Phosphor effect parameters
uniform float persistence;      // 0.0 - 0.95 (how long glow lasts)
uniform float glowIntensity;    // 0.5 - 2.0 (brightness of trail)
uniform float colorBleed;       // 0.0 - 0.5 (RGB decay difference)
uniform float burnIn;           // 0.0 - 0.3 (static element persistence)

in vec2 fragCoord;
out vec4 fragColor;

// Different phosphor types have different decay characteristics
// P22 (common color TV): Green fastest, Blue slowest
// P31 (green monochrome): Single color, medium persistence
vec3 getPhosphorDecay(float baseDecay) {
    // RGB decay rates - blue phosphors typically last longer
    return vec3(
        baseDecay - colorBleed * 0.3,  // Red decays faster
        baseDecay,                      // Green is reference
        baseDecay + colorBleed * 0.2   // Blue decays slower
    );
}

// Subtle noise for more organic phosphor behavior
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

void main() {
    vec2 uv = fragCoord;

    // Sample current and previous frames
    vec3 current = texture(iChannel0, uv).rgb;
    vec3 previous = texture(iChannel1, uv).rgb;

    // Calculate phosphor decay rates per channel
    vec3 decay = getPhosphorDecay(persistence);

    // Add slight per-pixel variation for organic feel
    float noise = hash(uv * iResolution + iTime) * 0.02;
    decay = clamp(decay + noise, 0.0, 0.99);

    // Apply persistence: blend previous frame with decay
    vec3 persistent = previous * decay;

    // Combine current frame with persistent glow
    // Current frame always shows at full brightness
    // Glow adds on top where previous was brighter
    vec3 glow = max(persistent - current, vec3(0.0)) * glowIntensity;
    vec3 combined = current + glow;

    // Burn-in effect: very slowly accumulate static bright areas
    // This simulates the permanent damage from static images
    float brightness = dot(current, vec3(0.299, 0.587, 0.114));
    float prevBrightness = dot(previous, vec3(0.299, 0.587, 0.114));

    // Burn-in only accumulates for consistently bright pixels
    float staticScore = step(0.8, brightness) * step(0.8, prevBrightness);
    vec3 burnInContribution = current * staticScore * burnIn * 0.01;

    // Final output with persistence
    // We output max of current and decayed previous for smooth trails
    vec3 result = max(combined, persistent * 0.9);
    result += burnInContribution;

    // Subtle phosphor glow bloom (bright areas spread slightly)
    if (glowIntensity > 0.5) {
        vec2 texel = 1.0 / iResolution;
        vec3 bloom = vec3(0.0);
        float bloomWeight = 0.0;

        // Sample neighboring pixels for bloom
        for (float x = -1.0; x <= 1.0; x += 1.0) {
            for (float y = -1.0; y <= 1.0; y += 1.0) {
                vec2 offset = vec2(x, y) * texel;
                vec3 sample_col = texture(iChannel1, uv + offset).rgb;
                float weight = 1.0 / (1.0 + length(vec2(x, y)));
                bloom += sample_col * weight;
                bloomWeight += weight;
            }
        }
        bloom /= bloomWeight;

        // Add subtle bloom to persistent glow
        float bloomAmount = (glowIntensity - 0.5) * 0.2;
        result = mix(result, max(result, bloom), bloomAmount);
    }

    // Clamp to valid range
    result = clamp(result, 0.0, 1.0);

    fragColor = vec4(result, 1.0);
}
