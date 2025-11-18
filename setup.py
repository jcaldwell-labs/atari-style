from setuptools import setup, find_packages

setup(
    name="atari-style",
    version="0.1.0",
    description="Atari-style terminal games and demos with joystick support",
    packages=find_packages(),
    install_requires=[
        "pygame>=2.5.0",
        "blessed>=1.20.0",
    ],
    entry_points={
        'console_scripts': [
            'atari-style=atari_style.main:main',
        ],
    },
    python_requires='>=3.8',
)
