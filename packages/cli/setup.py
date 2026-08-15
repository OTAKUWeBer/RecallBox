from setuptools import setup, find_packages

setup(
    name="recallbox-cli",
    version="0.1.0",
    description="RecallBox CLI: Local-first personal memory system",
    packages=find_packages(),
    install_requires=[
        "typer>=0.12.0",
        "rich>=13.7.0",
        "httpx>=0.27.0"
    ],
    entry_points={
        "console_scripts": [
            "recallbox=recallbox_cli.main:app"
        ]
    }
)
