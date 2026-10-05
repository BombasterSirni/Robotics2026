"""Тесты чистой функции выбора команды."""

from patrol.patrol import select_command
from turtlesim.msg import Pose


def test_missing_pose_gives_zero_command():
    """До первой позы команда нулевая."""
    command = select_command(None)
    assert command.linear.x == 0.0
    assert command.angular.z == 0.0
    assert command.linear.y == 0.0


def test_pose_gives_constant_command():
    """После обычного сообщения Pose выдаётся заданная команда."""
    command = select_command(Pose(x=5.5, y=5.5, theta=0.0))
    assert command.linear.x == 0.5
    assert command.angular.z == 0.3


def test_command_is_clamped():
    """Слишком большие по модулю значения ограничиваются диапазоном."""
    command = select_command(Pose(), linear_x=1.0, angular_z=-2.0)
    assert command.linear.x == 0.5
    assert command.angular.z == -1.0
