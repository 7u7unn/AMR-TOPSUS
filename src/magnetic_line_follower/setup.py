from setuptools import setup
import os
from glob import glob

package_name = 'magnetic_line_follower'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include launch files if any are added in the future
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools', 'pyserial'],
    zip_safe=True,
    maintainer='arya',
    maintainer_email='arya@ympif.com',
    description='Line following control and Modbus port auto-detection for CCF-NS16 16-bit magnetic navigation sensor.',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'line_follower = magnetic_line_follower.line_follower_node:main',
            'path_recorder = magnetic_line_follower.path_recorder:main',
            'mag_line_keeper = magnetic_line_follower.mag_line_keeper:main',
        ],
    },
)
