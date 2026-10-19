"""Тесты чистой функции команды и проверки параметров."""

import math

from patrol.patrol import select_command, timer_period, validate_parameter
import pytest
from turtlesim.msg import Pose


def test_missing_pose_gives_zero_command():
    """До первой позы команда нулевая."""
    command = select_command(None, 0.8, -0.4)
    assert command.linear.x == 0.0
    assert command.angular.z == 0.0
    assert command.linear.y == 0.0


def test_pose_uses_parameters():
    """Обычное сообщение Pose даёт команду из параметров."""
    command = select_command(Pose(x=5.5, y=5.5, theta=0.0), 0.8, -0.4)
    assert command.linear.x == 0.8
    assert command.angular.z == -0.4


def test_command_is_clamped():
    """Команда ограничивается допустимыми диапазонами."""
    command = select_command(Pose(), linear_x=2.0, angular_z=-3.0)
    assert command.linear.x == 1.0
    assert command.angular.z == -1.0


def test_valid_frequency_change():
    """Смена 10 -> 5 Гц допустима и даёт новый период таймера."""
    assert validate_parameter('publish_hz', 5.0) is None
    assert timer_period(10.0) == pytest.approx(0.1)
    assert timer_period(5.0) == pytest.approx(0.2)


def test_zero_frequency_rejected():
    """Нулевая частота отклоняется: период был бы бесконечным."""
    assert validate_parameter('publish_hz', 0.0) is not None


def test_negative_frequency_rejected():
    """Отрицательная частота отклоняется."""
    assert validate_parameter('publish_hz', -5.0) is not None


def test_nan_frequency_rejected():
    """Значение NaN отклоняется как не конечное число."""
    assert validate_parameter('publish_hz', math.nan) is not None


def test_speed_and_turn_limits():
    """Скорость и поворот проверяются по своим диапазонам."""
    assert validate_parameter('linear_speed', 0.0) is None
    assert validate_parameter('linear_speed', 1.0) is None
    assert validate_parameter('linear_speed', 1.01) is not None
    assert validate_parameter('turn_rate', -1.0) is None
    assert validate_parameter('turn_rate', -1.01) is not None
