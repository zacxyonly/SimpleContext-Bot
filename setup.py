from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name         = "simplecontext-bot",
    version      = "1.1.0",
    author       = "zacxyonly",
    description  = "🧠 AI Telegram Bot powered by SimpleContext — setup wizard included",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url          = "https://github.com/zacxyonly/SimpleContext-Bot",
    packages     = find_packages(),
    python_requires = ">=3.10",
    install_requires = [
        "python-telegram-bot>=21.0",
        "litellm>=1.40.0",
    ],
    entry_points = {
        "console_scripts": [
            "simplecontext-bot=simplecontext_bot.cli:main",
        ],
    },
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
