# PR05. Launch, QoS и повтор записи

Одна launch-команда поднимает систему в `/robot_a`: глобальный turtlesim, `patrol` из ПР04
с remap `cmd_vel` → `/turtle1/cmd_vel`, `pose_relay` (публикует относительный `sensor_pose`
с `best_effort`) и `sensor_listener` с настраиваемой надёжностью. `reliable`-подписчик
не получает сенсорный поток; после переключения на `best_effort` доставка восстанавливается
и на живом потоке, и на повторе MCAP-записи с тем же QoS override.

## Среда

Linux Mint 22.3 (Ubuntu 24.04 noble), ROS 2 Jazzy (ros-core 0.11.0), turtlesim 1.8.4,
rosbag2/ros2bag 0.26.11, Python 3.12.3. Course kit: `v1-w08`, sha256
`aea8efd0a51668af63f2e475b82bfa28bd76c21f20d8afea6b136d43a56a88fb`.

Прогон выполнен в `ROS_DOMAIN_ID=26` (чтобы не пересекаться с параллельной сессией в домене 25).
Системные пакеты `ros-jazzy-turtlesim` и `ros-jazzy-ros2bag` на машине отсутствуют, поэтому
для прогона использованы те же версии, распакованные из `.deb` в
`/home/covo43k/study/.ros-local`; CI ставит их штатно через apt. Полные данные —
`evidence/pr05/environment.json`.

## Состав

- `src/patrol/**` — нода с параметрами из ПР04;
- `src/course_bringup/launch/patrol.launch.py` — единый запуск с аргументами
  `namespace`, `record`, `bag_dir`, `subscriber_reliability`, remap и записью MCAP;
- `src/course_bringup/course_bringup/pose_relay.py` — `/turtle1/pose` → относительный
  `sensor_pose` с `best_effort`;
- `src/course_bringup/course_bringup/sensor_listener.py` — подписчик `sensor_pose`
  с параметром `reliability`;
- `config/qos-overrides.yaml` — профиль для повтора записи;
- `.github/workflows/ci.yml` — сборка, `colcon test` и `check_practice.py PR05`
  на ките `v1-w08`.

CI сначала скачивает кит с `ros.lms.ci.nsu.ru`. Если раннер не может разрешить этот
хост (`curl: (6) Could not resolve host`), используется байт-в-байт копия архива из
`ci/course-kit/`; в обоих случаях проверяется один и тот же sha256
`aea8efd0a51668af63f2e475b82bfa28bd76c21f20d8afea6b136d43a56a88fb`, то есть
проверяется ровно зафиксированная ревизия `v1-w08`.

## Ход работы

### 1. Сборка и тесты

```bash
colcon build --symlink-install
source install/setup.bash
/usr/bin/python3 -m pytest src/patrol/test
colcon test --event-handlers console_direct+
colcon test-result --verbose
```

Логи: `evidence/pr05/build.txt`, `evidence/pr05/tests.txt`.

### 2. Запуск системы

```bash
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=reliable record:=false
```

Граф: `/robot_a/patrol`, `/robot_a/pose_relay`, `/robot_a/sensor_listener` и глобальный
`/turtlesim`. Топик сенсора — `/robot_a/sensor_pose` (издатель `pose_relay`,
`Reliability: BEST_EFFORT`), команда `patrol` уходит в `/turtle1/cmd_vel` через remap,
запись выключена через `IfCondition`.

### 3. Сбой QoS

`reliable`-подписчик против `best_effort`-издателя: топик виден, сообщений нет.

```bash
ros2 topic list | grep sensor_pose                       # /robot_a/sensor_pose
ros2 topic info -v /robot_a/sensor_pose                  # pub BEST_EFFORT, sub RELIABLE
timeout 3s ros2 topic echo /robot_a/sensor_pose \
  --qos-reliability reliable --once                      # WARN incompatible QoS, exit=124
```

`pose_relay` публикует 123 → 498 сообщений, `sensor_listener` при этом пишет
`received 0 messages`, обе стороны в логе сообщают `incompatible QoS` с политикой
`RELIABILITY`. Лог: `evidence/pr05/qos-before.txt`.

### 4. Исправление и запись

```bash
ros2 launch course_bringup patrol.launch.py \
  namespace:=robot_a subscriber_reliability:=best_effort \
  record:=true bag_dir:=evidence/pr05/bag
```

Профили совместимы: издатель и подписчик `BEST_EFFORT`, recorder подписывается
`BEST_EFFORT`; `ros2 topic echo --qos-reliability best_effort --once` получает `Pose`,
`received` растёт 625 → 750. Запись `ros2 bag record -s mcap` идёт из launch.
Лог: `evidence/pr05/qos-after.txt`.

### 5. Повтор записи

```bash
ros2 bag play evidence/pr05/bag --qos-profile-overrides-path config/qos-overrides.yaml
ros2 topic echo /robot_a/sensor_pose --qos-reliability reliable --once     # WARN, exit=124
ros2 topic echo /robot_a/sensor_pose --qos-reliability best_effort --once   # Pose
ros2 bag info evidence/pr05/bag
```

Плеер печатает `Overriding QoS profile for topic /robot_a/sensor_pose`; поведение то же,
что на живом потоке. `ros2 bag info`: `bag_0.mcap`, `Storage id: mcap`, 12.32 с,
771 сообщение, один топик `/robot_a/sensor_pose` (`turtlesim/msg/Pose`).
`metadata.yaml` скопирован в `evidence/pr05/bag-metadata.yaml`.
