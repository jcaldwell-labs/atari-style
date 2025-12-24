"""Zone mode runner for embedding atari-style demos in zones.

This module provides a headless mode for running parametric animations
that outputs ANSI frames to stdout for capture by parent processes.

Supports live parameter control via JSON commands on stdin.

Usage:
    python -m atari_style.zone_mode plasma --width 80 --height 24
    python -m atari_style.zone_mode lissajous --width 60 --height 20 --fps 10

Parameter Control:
    Send JSON to stdin: {"command": "set_param", "param": "speed", "value": 2.5}
"""

import argparse
import time
import sys
import json
import threading
import socket
from .core.zone_renderer import ZoneRenderer
from .demos.visualizers.screensaver import (
    LissajousCurve,
    SpiralAnimation,
    CircleWaveAnimation,
    PlasmaAnimation,
)


# Available animations
ANIMATIONS = {
    'plasma': PlasmaAnimation,
    'lissajous': LissajousCurve,
    'spiral': SpiralAnimation,
    'waves': CircleWaveAnimation,
}


def handle_control_socket(animation, stop_event, control_port):
    """Background thread that listens on a TCP socket for parameter control commands.

    Args:
        animation: Animation object to control
        stop_event: Threading event to signal shutdown
        control_port: TCP port to listen on
    """
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('localhost', control_port))
        server.listen(5)
        server.settimeout(0.5)  # Allow periodic checking of stop_event

        while not stop_event.is_set():
            try:
                client, addr = server.accept()
                client.settimeout(2.0)

                try:
                    # Read command from client (single line)
                    data = b""
                    while b'\n' not in data and len(data) < 4096:
                        chunk = client.recv(1024)
                        if not chunk:
                            break
                        data += chunk

                    if data:
                        line = data.decode('utf-8', errors='replace').strip()
                        try:
                            cmd = json.loads(line)

                            if cmd.get('command') == 'set_param':
                                param = cmd.get('param')
                                value = cmd.get('value')

                                if param and value is not None:
                                    # Set parameter
                                    if hasattr(animation, 'set_param'):
                                        animation.set_param(param, value)
                                        response = json.dumps({"status": "ok", "param": param, "value": value})
                                    elif hasattr(animation, param):
                                        setattr(animation, param, value)
                                        response = json.dumps({"status": "ok", "param": param, "value": value})
                                    else:
                                        response = json.dumps({"status": "error", "message": f"Unknown param: {param}"})

                                    client.sendall(response.encode('utf-8') + b'\n')

                        except json.JSONDecodeError:
                            client.sendall(b'{"status":"error","message":"Invalid JSON"}\n')
                        except Exception as e:
                            client.sendall(f'{{"status":"error","message":"{e}"}}\n'.encode('utf-8'))

                finally:
                    client.close()

            except socket.timeout:
                continue  # No connection - check stop_event and retry
            except Exception:
                continue  # Other errors - continue running

    finally:
        try:
            server.close()
        except:
            pass


def run_zone_animation(animation_name: str, width: int = 80, height: int = 24, fps: int = 20, control_port: int = None):
    """Run an animation in zone mode with live parameter control.

    Args:
        animation_name: Name of the animation to run
        width: Zone width in characters
        height: Zone height in characters
        fps: Frames per second
        control_port: TCP port for parameter control (optional)
    """
    if animation_name not in ANIMATIONS:
        print(f"Error: Unknown animation '{animation_name}'", file=sys.stderr)
        print(f"Available: {', '.join(ANIMATIONS.keys())}", file=sys.stderr)
        sys.exit(1)

    # Create renderer and animation
    renderer = ZoneRenderer(width=width, height=height)
    animation_class = ANIMATIONS[animation_name]
    animation = animation_class(renderer)

    # Start control socket handler thread if port specified
    stop_event = threading.Event()
    command_thread = None

    if control_port:
        command_thread = threading.Thread(
            target=handle_control_socket,
            args=(animation, stop_event, control_port),
            daemon=True
        )
        command_thread.start()
        print(f"[CONTROL] Listening on port {control_port}", file=sys.stderr)

    # Animation loop
    frame_time = 1.0 / fps
    t = 0.0

    try:
        while True:
            start = time.time()

            # Clear and draw
            renderer.clear_buffer()
            animation.draw(t)
            renderer.render()

            # Update time
            t += frame_time

            # Sleep to maintain frame rate
            elapsed = time.time() - start
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    except BrokenPipeError:
        # Parent process closed pipe - normal exit
        pass
    finally:
        stop_event.set()
        if command_thread:
            command_thread.join(timeout=1.0)


def main():
    """Main entry point for zone mode."""
    # Fix Windows encoding for Unicode characters (block chars, box drawing, etc.)
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(
        description='Run atari-style animations in zone mode for embedding'
    )
    parser.add_argument(
        'animation',
        choices=list(ANIMATIONS.keys()),
        help='Animation to run'
    )
    parser.add_argument(
        '--width',
        type=int,
        default=80,
        help='Zone width in characters (default: 80)'
    )
    parser.add_argument(
        '--height',
        type=int,
        default=24,
        help='Zone height in characters (default: 24)'
    )
    parser.add_argument(
        '--fps',
        type=int,
        default=20,
        help='Frames per second (default: 20)'
    )
    parser.add_argument(
        '--control-port',
        type=int,
        default=None,
        help='TCP port for parameter control (optional)'
    )

    args = parser.parse_args()

    run_zone_animation(
        args.animation,
        width=args.width,
        height=args.height,
        fps=args.fps,
        control_port=args.control_port
    )


if __name__ == '__main__':
    main()
