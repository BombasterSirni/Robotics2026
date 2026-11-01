"""Нода pose_relay: переиздаёт позу turtlesim в sensor_pose с best_effort."""

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy
from rclpy.qos import HistoryPolicy
from rclpy.qos import QoSProfile
from rclpy.qos import ReliabilityPolicy
from turtlesim.msg import Pose

# Сенсорный профиль: best_effort, как у реальных датчиков.
SENSOR_QOS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
    reliability=ReliabilityPolicy.BEST_EFFORT,
    durability=DurabilityPolicy.VOLATILE,
)


class PoseRelay(Node):
    """Подписка на глобальную позу и публикация относительного sensor_pose."""

    def __init__(self):
        super().__init__('pose_relay')
        self._published = 0
        self._relay_pub = self.create_publisher(Pose, 'sensor_pose', SENSOR_QOS)
        self._pose_sub = self.create_subscription(
            Pose, '/turtle1/pose', self._on_pose, 10)
        self._report_timer = self.create_timer(2.0, self._report)

    def _on_pose(self, msg):
        """Переиздать позу в сенсорный топик."""
        self._relay_pub.publish(msg)
        self._published += 1

    def _report(self):
        """Лог раз в 2 с: поток жив, даже если подписчик несовместим по QoS."""
        self.get_logger().info(
            f'published {self._published} poses to sensor_pose')


def main(args=None):
    """Запустить ноду и держать её до Ctrl+C (SIGINT) или SIGTERM."""
    rclpy.init(args=args)
    node = PoseRelay()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
