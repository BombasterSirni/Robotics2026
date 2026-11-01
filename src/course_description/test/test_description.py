"""Структурные проверки URDF: связность дерева, родители звеньев, геометрия."""

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import xacro

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
URDF_PATH = PACKAGE_ROOT / 'urdf' / 'vehicle.urdf.xacro'

# Ожидаемое дерево: сенсоры висят на base_link фиксированными связями.
SENSOR_PARENTS = {
    'camera_link': 'base_link',
    'lidar_link': 'base_link',
    'imu_link': 'base_link',
}
SENSOR_XYZ = {
    'camera_link': (0.28, 0.0, 0.38),
    'lidar_link': (-0.05, 0.0, 0.45),
    'imu_link': (0.0, 0.0, 0.24),
}


@pytest.fixture(scope='module')
def robot():
    """Развернуть Xacro в URDF и разобрать XML."""
    return ET.fromstring(xacro.process_file(str(URDF_PATH)).toxml())


def link_names(robot):
    """Множество имён звеньев."""
    return {link.get('name') for link in robot.findall('link')}


def joints_by_child(robot):
    """Словарь: дочернее звено -> joint."""
    return {joint.find('child').get('link'): joint for joint in robot.findall('joint')}


def origin_xyz(joint):
    """Смещение joint как кортеж float."""
    origin = joint.find('origin')
    if origin is None:
        return (0.0, 0.0, 0.0)
    return tuple(float(value) for value in origin.get('xyz', '0 0 0').split())


def absolute_position(robot, link):
    """Сумма смещений от base_link до link (rpy у всех связей нулевой)."""
    joints = joints_by_child(robot)
    xyz = (0.0, 0.0, 0.0)
    current = link
    while current in joints:
        xyz = tuple(a + b for a, b in zip(xyz, origin_xyz(joints[current])))
        current = joints[current].find('parent').get('link')
    return xyz


def test_xacro_expands(robot):
    """Xacro разворачивается в один robot с непустым именем."""
    assert robot.tag == 'robot'
    assert robot.get('name') == 'course_ackermann'
    assert len(link_names(robot)) >= 8


def test_every_link_has_exactly_one_parent(robot):
    """У каждого звена, кроме base_link, ровно один родитель."""
    children = [joint.find('child').get('link') for joint in robot.findall('joint')]
    assert len(children) == len(set(children))
    assert 'base_link' not in children
    assert set(children) == link_names(robot) - {'base_link'}


def test_tree_is_connected_and_acyclic(robot):
    """Обход от base_link достигает всех звеньев без циклов."""
    edges = {}
    for joint in robot.findall('joint'):
        parent = joint.find('parent').get('link')
        edges.setdefault(parent, []).append(joint.find('child').get('link'))
    visited = set()
    stack = ['base_link']
    while stack:
        link = stack.pop()
        assert link not in visited, f'цикл в дереве на {link}'
        visited.add(link)
        stack.extend(edges.get(link, []))
    assert visited == link_names(robot)


def test_sensor_parents(robot):
    """Камера, лидар и IMU крепятся к base_link фиксированными связями."""
    joints = joints_by_child(robot)
    for link, parent in SENSOR_PARENTS.items():
        assert link in joints, f'нет связи для {link}'
        assert joints[link].get('type') == 'fixed'
        assert joints[link].find('parent').get('link') == parent


def test_sensor_offsets(robot):
    """Смещения сенсоров совпадают с параметрами Xacro."""
    joints = joints_by_child(robot)
    for link, expected in SENSOR_XYZ.items():
        assert origin_xyz(joints[link]) == pytest.approx(expected)


def test_sensor_absolute_positions(robot):
    """В дереве лидар стоит в своей точке, а не поверх camera_link."""
    for link, expected in SENSOR_XYZ.items():
        assert absolute_position(robot, link) == pytest.approx(expected)


def test_base_and_wheels_are_parameterised(robot):
    """Корпус и колёса соответствуют параметрам база/колея/радиус."""
    base = {link.get('name'): link for link in robot.findall('link')}['base_link']
    box = base.find('collision/geometry/box')
    assert [float(value) for value in box.get('size').split()] == pytest.approx(
        [1.05, 0.52, 0.22])

    wheel = {link.get('name'): link for link in robot.findall('link')}['front_left_wheel']
    cylinder = wheel.find('collision/geometry/cylinder')
    assert float(cylinder.get('radius')) == pytest.approx(0.12)
    assert float(cylinder.get('length')) == pytest.approx(0.07)

    joints = joints_by_child(robot)
    assert origin_xyz(joints['front_left_wheel'])[:2] == pytest.approx([0.40, 0.31])
    assert origin_xyz(joints['rear_right_wheel'])[:2] == pytest.approx([-0.40, -0.31])


def test_visual_and_collision_are_separate(robot):
    """У каждого звена есть отдельные visual и collision."""
    for link in robot.findall('link'):
        assert link.find('visual/geometry') is not None, link.get('name')
        assert link.find('collision/geometry') is not None, link.get('name')


def test_inertia_is_physically_possible(robot):
    """Массы положительны, тензор инерции физически возможен."""
    for link in robot.findall('link'):
        inertial = link.find('inertial')
        assert inertial is not None, link.get('name')
        mass = float(inertial.find('mass').get('value'))
        assert math.isfinite(mass) and mass > 0
        inertia = inertial.find('inertia')
        diagonal = [float(inertia.get(axis)) for axis in ('ixx', 'iyy', 'izz')]
        assert all(math.isfinite(value) and value > 0 for value in diagonal)
        for first in range(3):
            for second in range(first + 1, 3):
                third = 3 - first - second
                assert diagonal[first] + diagonal[second] >= diagonal[third] - 1e-12
