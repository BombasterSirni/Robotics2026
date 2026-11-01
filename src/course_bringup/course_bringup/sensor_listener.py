"""Нода sensor_listener: подписчик sensor_pose с настраиваемым QoS."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy
from rclpy.qos import HistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from turtlesim.msg import Pose

# Допустимые имена надёжности для параметра reliability.
RELIABILITY_CHOICES = {
    'reliable': ReliabilityPolicy.RELIABLE,
    'best_effort': ReliabilityPolicy.BEST_EFFORT,
}


class SensorListener(Node):
    """Подписка на относительный sensor_pose с выбранной надёжностью."""

    def __init__(self):
        super().__init__('sensor_listener')
        self.declare_parameter('reliability', 'reliable')
        name = str(self.get_parameter('reliability').value)
        if name not in RELIABILITY_CHOICES:
            self.get_logger().warning(
                f'unknown reliability {name!r}, using best_effort')
            name = 'best_effort'
        self._reliability = name
        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=10,
            reliability=RELIABILITY_CHOICES[name],
            durability=DurabilityPolicy.VOLATILE,
        )
        self._received = 0
        self._sensor_sub = self.create_subscription(
            Pose, 'sensor_pose', self._on_pose, qos)
        self._report_timer = self.create_timer(1.0, self._report)
        self.get_logger().info(f'sensor_listener reliability: {name}')

    def _on_pose(self, msg):
        """Посчитать принятые сообщения."""
        self._received += 1

    def _report(self):
        """Лог раз в секунду: сколько сообщений дошло до подписчика."""
        self.get_logger().info(
            f'{self._reliability}: received {self._received} messages')


def main(args=None):
    """Запустить ноду и держать её до Ctrl+C (SIGINT) или SIGTERM."""
    rclpy.init(args=args)
    node = SensorListener()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
