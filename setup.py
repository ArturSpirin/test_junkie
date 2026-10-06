import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="test_junkie",
    version="0.9a4",
    author="Artur Spirin",
    author_email="as.no.replies@gmail.com",
    description="Modern Testing Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.test-junkie.com/",
    packages=setuptools.find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities"
    ],
    install_requires=["psutil", "appdirs", "colorama", "coverage"],
    keywords=["automation", "testing", "tests", "test-runner"],
    entry_points={
          'console_scripts': [
              'tj3 = test_junkie.__main__:main',
              'tj = test_junkie.__main__:main'
          ]
    },
)
