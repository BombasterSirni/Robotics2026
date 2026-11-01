from glob import glob

from setuptools import find_packages, setup

package_name = 'course_description'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/urdf', glob('urdf/*.xacro')),
        ('share/' + package_name + '/launch', glob('launch/*launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='covo43k',
    maintainer_email='covo4ek42@gmail.com',
    description='Описание Ackermann-робота: URDF/Xacro и tf2-дерево (ПР06)',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
)
