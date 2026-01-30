from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="simple-vcs",
    version="1.1.0",
    author="Muhammad Sufiyan Baig",
    author_email="send.sufiyan@gmail.com",
    description="A simple version control system with unique features for easy version management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/muhammadsufiyanbaig/simple_vcs",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "click>=7.0",
    ],
    entry_points={
        "console_scripts": [
            "svcs=simple_vcs.cli:main",
        ],
    },
)
