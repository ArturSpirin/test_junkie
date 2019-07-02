import sys

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="test_junkie",
    version="0.7a0",
    author="Artur Spirin",
    author_email="as.no.replies@gmail.com",
    description="Modern Testing Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.test-junkie.com/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"
    ],
    install_requires=["statistics", "psutil", "appdirs", "configparser",
                      "colorama", "coverage"],
    keywords=["automation", "testing", "tests", "test-runner"],
    entry_points={
          'console_scripts': [
              'tj2 = test_junkie.__main__:main' if sys.version_info[0] < 3 else 'tj3 = test_junkie.__main__:main',
              'tj = test_junkie.__main__:main'
          ]
    },
)
