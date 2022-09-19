"""A simple PyGame application

"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

# Arguments marked as "Required" below must be included for upload to PyPI.
# Fields marked as "Optional" may be commented out.

setup(
    name="simworld",
    version="1.0.0",
    description="A simple PyGame simulation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/coolbreezechloe/simworld",
    author="Chloe Beelby",
    author_email="CoolBreezeChloe@gmail.com",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.7, <4",
    install_requires=["pygame"],
    extras_require={
        "dev": ["coverage"],
        "test": ["coverage"],
    },
    package_data={
        "simworld": ["assets/*"],
    },
    entry_points={  # Optional
        "console_scripts": [
            "simworld=simworld.main:start_game",
        ],
    },
)
