import versioneer
from setuptools import setup, find_packages

setup(
    name='dircompare',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    # Author details
    author='SLAC National Accelerator Laboratory',

    packages=find_packages(),
    package_dir={'dircompare':'dircompare', 'dircompare_launcher':'dircompare_launcher'},
    description='Compare child directory listings between two parent directories',
    url='https://github.com/hmbui/dircompare',
    entry_points={
        'gui_scripts': [
            'dircompare=dircompare_launcher.main:main'
        ]
    },
    license='BSD',
    include_package_data=True,
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ]
)
