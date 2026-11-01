"""Единый запуск ПР05: turtlesim, patrol, pose_relay, listener и запись MCAP."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import ExecuteProcess
from launch.actions import LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch.substitutions import PythonExpression
from launch_ros.actions import Node

# Полное имя сенсорного топика из относительного имени и namespace.
SENSOR_TOPIC = PythonExpression(
    ["'/' + '", LaunchConfiguration('namespace'), "' + '/sensor_pose'"])


def generate_launch_description():
    """Собрать описание запуска с аргументами, remap и записью."""
    namespace = LaunchConfiguration('namespace')
    record = LaunchConfiguration('record')
    bag_dir = LaunchConfiguration('bag_dir')
    subscriber_reliability = LaunchConfiguration('subscriber_reliability')

    declarations = [
        DeclareLaunchArgument(
            'namespace', default_value='robot_a',
            description='Пространство имён системы'),
        DeclareLaunchArgument(
            'record', default_value='false',
            description='Записывать sensor_pose в MCAP (true/false)'),
        DeclareLaunchArgument(
            'bag_dir', default_value='evidence/pr05/bag',
            description='Каталог для записи MCAP'),
        DeclareLaunchArgument(
            'subscriber_reliability', default_value='reliable',
            description='Надёжность подписчика sensor_pose: reliable|best_effort'),
    ]

    logs = [
        LogInfo(msg=[
            'ПР05: namespace=', namespace,
            ', subscriber_reliability=', subscriber_reliability]),
        LogInfo(
            msg=['Запись потока в ', bag_dir],
            condition=IfCondition(record)),
    ]

    # turtlesim глобальный: поза публикуется в /turtle1/pose.
    turtlesim = Node(
        package='turtlesim',
        executable='turtlesim_node',
        name='turtlesim',
        output='screen',
    )

    # patrol живёт в namespace; его относительный cmd_vel уходит в turtlesim.
    patrol = Node(
        package='patrol',
        executable='patrol',
        namespace=namespace,
        output='screen',
        remappings=[('cmd_vel', '/turtle1/cmd_vel')],
    )

    # pose_relay публикует относительный sensor_pose -> /<namespace>/sensor_pose.
    relay = Node(
        package='course_bringup',
        executable='pose_relay',
        namespace=namespace,
        output='screen',
    )

    # Подписчик с настраиваемой надёжностью.
    listener = Node(
        package='course_bringup',
        executable='sensor_listener',
        namespace=namespace,
        output='screen',
        parameters=[{'reliability': subscriber_reliability}],
    )

    # Запись одного потока; при record:=false процесс не запускается.
    recorder = ExecuteProcess(
        name='sensor_pose_recorder',
        cmd=[
            'ros2', 'bag', 'record', '-s', 'mcap',
            '-o', bag_dir, '--topics', SENSOR_TOPIC,
        ],
        condition=IfCondition(record),
        output='screen',
    )

    return LaunchDescription([
        *declarations,
        *logs,
        turtlesim,
        patrol,
        relay,
        listener,
        recorder,
    ])
