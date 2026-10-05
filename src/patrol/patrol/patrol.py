"""Нода patrol: следит за позой turtlesim и выдаёт команду Twist."""

from geometry_msgs.msg import Twist
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim.msg import Pose

# Допустимые диапазоны команды (ПР03, ограничение в чистой функции).
LINEAR_X_RANGE = (0.0, 0.5)
ANGULAR_Z_RANGE = (-1.0, 1.0)

# Постоянная команда после получения первой позы.
LINEAR_X = 0.5
ANGULAR_Z = 0.3

# Период таймера публикации, с.
TIMER_PERIOD = 0.1


def clamp(value, lower, upper):
    """Ограничить value отрезком [lower, upper]."""
    return max(lower, min(upper, value))


def select_command(pose, linear_x=LINEAR_X, angular_z=ANGULAR_Z):
    """Собрать Twist для позы: нулевой без позы, иначе постоянный и ограниченный."""
    command = Twist()
    if pose is None:
        return command
    command.linear.x = clamp(linear_x, *LINEAR_X_RANGE)
    command.angular.z = clamp(angular_z, *ANGULAR_Z_RANGE)
    return command


class Patrol(Node):
    """Подписка на позу, таймер 0.1 с и публикация команды."""

    def __init__(self):
        super().__init__('patrol')
        self._pose = None
        # Подписка хранится полем: иначе её уничтожит сборщик мусора.
        self._pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self._on_pose, 10)
        # Относительное имя: с /turtle1/cmd_vel его связывает только remap.
        self._cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self._timer = self.create_timer(TIMER_PERIOD, self._on_timer)

    def _on_pose(self, msg):
        """Запомнить последнюю позу, ничего не публикуя."""
        self._pose = msg

    def _on_timer(self):
        """Опубликовать команду, выбранную чистой функцией."""
        self._cmd_pub.publish(select_command(self._pose))


def main(args=None):
    """Запустить ноду и держать её до Ctrl+C (SIGINT) или SIGTERM."""
    rclpy.init(args=args)
    node = Patrol()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
