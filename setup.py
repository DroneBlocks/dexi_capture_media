from setuptools import setup, find_packages
import os
from glob import glob

package_name = 'dexi_capture_media'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Dennis Baldwin',
    maintainer_email='db@droneblocks.io',
    description='Capture photos and record video on DEXI from the web GCS or an RC switch',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'capture_media_node = dexi_capture_media.capture_media_node:main',
        ],
    },
)
