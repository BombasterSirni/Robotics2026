"""Нода patrol: поза turtlesim, параметры движения и команда Twist."""

import math

from geometry_msgs.msg import Twist
from rcl_interfaces.msg import SetParametersResult
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from turtlesim.msg import Pose

# Значение по умолчанию для каждого параметра.
LINEAR_SPEED = 0.5
TURN_RATE = 0.3
PUBLISH_HZ = 10.0

# Имя параметра -> (значение по умолчанию, минимум, максимум).
PARAMETER_SPECS = {
    'linear_speed': (LINEAR_SPEED, 0.0, 1.0),
    'turn_rate': (TURN_RATE, -1.0, 1.0),
    'publish_hz': (PUBLISH_HZ, 1.0, 30.0),
}

# Допустимые диапазоны команды в Twist.
LINEAR_X_RANGE = (0.0, 1.0)
ANGULAR_Z_RANGE = (-1.0, 1.0)


def clamp(value, lower, upper):
    """Ограничить value отрезком [lower, upper]."""
    return max(lower, min(upper, value))


def validate_parameter(name, value):
    """Вернуть причину отказа для параметра name или None, если значение допустимо."""
    if name not in PARAMETER_SPECS:
        return f'unknown parameter: {name}'
    _, minimum, maximum = PARAMETER_SPECS[name]
    if not math.isfinite(value):
        return f'{name} must be a finite number, got {value!r}'
    if not minimum <= value <= maximum:
        return f'{name} must be in [{minimum}, {maximum}], got {value!r}'
    return None


def timer_period(hz):
    """Период таймера в секундах для частоты hz."""
    return 1.0 / hz


def select_command(pose, linear_x=LINEAR_SPEED, angular_z=TURN_RATE):
    """Собрать Twist для позы: нулевой без позы, иначе ограниченный."""
    command = Twist()
    if pose is None:
        return command
    command.linear.x = clamp(linear_x, *LINEAR_X_RANGE)
    command.angular.z = clamp(angular_z, *ANGULAR_Z_RANGE)
    return command


class Patrol(Node):
    """Подписка на позу, параметры движения и таймер публикации."""

    def __init__(self):
        super().__init__('patrol')
        self._pose = None
        self._linear_speed = LINEAR_SPEED
        self._turn_rate = TURN_RATE
        self._publish_hz = PUBLISH_HZ
        for name, (default, _, _) in PARAMETER_SPECS.items():
            self.declare_parameter(name, default)

        # Подписка хранится полем: иначе её уничтожит сборщик мусора.
        self._pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self._on_pose, 10)
        # Относительное имя: с /turtle1/cmd_vel его связывает только remap.
        self._cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self._timer = None
        self._start_timer()

        self.add_on_set_parameters_callback(self._on_set_parameters)
        self.add_post_set_parameters_callback(self._on_parameters_set)

    def _start_timer(self):
        """Пересоздать таймер: прежний останавливается, двух одновременно нет."""
        if self._timer is not None:
            self.destroy_timer(self._timer)
        period = timer_period(self._publish_hz)
        self._timer = self.create_timer(period, self._on_timer)
        self.get_logger().info(
            f'publish period {period:.3f} s ({self._publish_hz:g} Hz)')

    def _on_set_parameters(self, params):
        """Отклонить недопустимые значения до применения."""
        for param in params:
            try:
                value = float(param.value)
            except (TypeError, ValueError):
                return SetParametersResult(
                    successful=False, reason=f'{param.name} must be a number')
            reason = validate_parameter(param.name, value)
            if reason is not None:
                self.get_logger().warning(f'rejected {param.name}: {reason}')
                return SetParametersResult(successful=False, reason=reason)
        return SetParametersResult(successful=True)

    def _on_parameters_set(self, params):
        """Применить принятые значения; смена частоты пересоздаёт таймер."""
        for param in params:
            if param.name == 'linear_speed':
                self._linear_speed = float(param.value)
            elif param.name == 'turn_rate':
                self._turn_rate = float(param.value)
            elif param.name == 'publish_hz':
                hz = float(param.value)
                if hz != self._publish_hz:
                    self._publish_hz = hz
                    self._start_timer()

    def _on_pose(self, msg):
        """Запомнить последнюю позу, ничего не публикуя."""
        self._pose = msg

    def _on_timer(self):
        """Опубликовать команду по последней позе и текущим параметрам."""
        self._cmd_pub.publish(
            select_command(self._pose, self._linear_speed, self._turn_rate))


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
