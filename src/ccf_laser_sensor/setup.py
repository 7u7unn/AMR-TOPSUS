from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'ccf_laser_sensor'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.py')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.com',
    description='ROS2 driver for CCF-LAS4-4M5-channel laser obstacle avoidance sensor',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'ccf_laser_node = ccf_laser_sensor.ccf_laser_node:main',
        ],
    },
)
