from setuptools import setup, find_packages

setup(
    name="mcode-web-deploy",
    version="0.1.0",
    description="Zero-token, direct static web deployment tool for MiniMax (mcode) space hosting",
    long_description=open("README.md", "r", encoding="utf-8").read() if open("README.md").readable() else "",
    long_description_content_type="text/markdown",
    author="wurong",
    url="https://github.com/wurong98/mcode-web-deploy",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "mcode-deploy=mcode_web_deploy.cli:main",
        ],
    },
)
