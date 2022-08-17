import setuptools  # type: ignore

setuptools.setup(
    name="socaplot",
    version="0.1.0",
    author="JCSDA",
    description="Plotting tools for soca-science using BESPIN/PADME packages",
    url="",
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        'Natural Language :: English',
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'bespin @ git+ssh://git@github.com/jcsda-internal/bespin@feature/soca',
        'padme @ git+ssh://git@github.com/jcsda-internal/padme@feature/soca',
        'click',
        'pyyaml',
    ],
    package_dir={"": "src"},
    packages = setuptools.find_packages(where='src'),
    package_data={"socaplot": [
        "config/*/*.yaml",
        ]},
    zip_safe=False,
    python_requires=">=3.7",
    entry_points={
        'console_scripts': [
            'socaplot=socaplot.bin.socaplot:cli',
        ]
    }
)
