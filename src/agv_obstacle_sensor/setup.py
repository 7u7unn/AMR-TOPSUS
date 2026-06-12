from setuptools import setup
import os
from glob import glob

package_name = 'agv_obstacle_sensor'

# Construct data_files carefully so entries are always (target, files)
data_files_list = []
if os.path.exists('resource/' + package_name):
    data_files_list.append(('share/ament_index/resource_index/packages', ['resource/' + package_name]))
elif os.path.exists('resource'):
    # fallback: include any resource file named after package
    data_files_list.append(('share/ament_index/resource_index/packages', ['resource/' + package_name]))
data_files_list.append(('share/' + package_name, ['package.xml']))
data_files_list.append((os.path.join('share', package_name, 'launch'), glob('launch/*.py')))

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=data_files_list,
    install_requires=['setuptools', 'pyserial'],
    zip_safe=True,
    maintainer='you',
    maintainer_email='you@example.com',
    description=('Auto-detect and read dual 7-channel obstacle sensors (front/back).'),
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'agv_obstacle_sensor_node = agv_obstacle_sensor.obstacle_node:main',
        ],
    },
)
