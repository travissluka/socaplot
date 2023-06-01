import setuptools  # type: ignore

setuptools.setup(
    name="socaplot",
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
    setup_requires=["setuptools-git-versioning"],
    setuptools_git_versioning={
        "enabled": True,
    },
    install_requires=[
#        'bespin @ git+ssh://git@github.com/travissluka/bespin@feature/soca',
#        'padme @ git+ssh://git@github.com/travissluka/padme@feature/soca',
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
