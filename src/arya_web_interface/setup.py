from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'arya_web_interface'


def collect_data_files(source_dir, install_dir):
    """Collect files while preserving their directory layout in install space."""
    data_files = []
    if not os.path.isdir(source_dir):
        return data_files

    for root, _dirs, files in os.walk(source_dir):
        file_paths = [
            os.path.join(root, file_name)
            for file_name in files
        ]
        if not file_paths:
            continue

        relative_dir = os.path.relpath(root, source_dir)
        target_dir = install_dir if relative_dir == '.' else os.path.join(install_dir, relative_dir)
        data_files.append((target_dir, file_paths))

    return data_files


setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        # Resource index agar ROS 2 mengenali package ini
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),

        # File package.xml wajib untuk ROS 2
        ('share/' + package_name, ['package.xml']),

        # Semua launch file
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*.launch.py')),
    ]
    + collect_data_files(
        os.path.join(package_name, 'static'),
        os.path.join('share', package_name, 'static'),
    )
    + collect_data_files(
        os.path.join(package_name, 'templates'),
        os.path.join('share', package_name, 'templates'),
    ),
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='amr',
    maintainer_email='amr@example.com',
    description='Web interface for ARYA robot',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': [
            'web_node = arya_web_interface.web_node:main',
        ],
    },
)
