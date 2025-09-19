from setuptools import setup, find_packages

setup(
    name="gemspa_cli",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Command-line interface for GEMspa single-particle tracking analysis",
    # If you have a README.md, you can include it here; otherwise, use a short description.
    long_description="",
    long_description_content_type='text/plain',
    url="https://github.com/yourusername/gemspa_cli",
    packages=find_packages(),
    include_package_data=True,
    scripts=[
        'bin/GEMspa-CLI.py'
    ],
    install_requires=[
        'numpy>=1.21.0,<1.25.0',
        'pandas>=1.3.0,<2.0.0',
        'scipy>=1.7.0,<2.0.0',
        'matplotlib>=3.4.0,<4.0.0',
        'seaborn>=0.11.0,<1.3.0',
        'scikit-image>=0.19.0,<0.21.0',
        'tifffile>=2020.12.8,<2022.0.0',
        'nd2reader>=3.0.0,<4.0.0',
        'joblib>=1.2.0,<2.0.0',
        'numba>=0.55.0,<0.60.0'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
