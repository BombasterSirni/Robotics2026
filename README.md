# PR06. Модель робота, tf2 и QoS преобразований

Параметризованная URDF/Xacro-модель Ackermann-робота в `course_description`: корпус,
камера, лидар, IMU и четыре колеса в одном дереве tf2. `robot_state_publisher`
публикует фиксированные связи на `/tf_static` с `transient local`, поэтому поздний
подписчик получает преобразования, а подписчик с `volatile` — нет.

## Среда

Linux Mint 22.3 (Ubuntu 24.04 noble), ROS 2 Jazzy (ros-core 0.11.0), `xacro` 2.1.1,
`robot_state_publisher` 3.3.4, tf2 0.36.23, Python 3.12.3. Прогон выполнен в
`ROS_DOMAIN_ID=27`. Course kit: `v1-w08`, sha256
`aea8efd0a51668af63f2e475b82bfa28bd76c21f20d8afea6b136d43a56a88fb`.

В этой среде `ros-jazzy-xacro` и `ros-jazzy-ros2bag` не были установлены, поэтому
`xacro` взят из `.deb` в `/home/covo43k/study/.ros-local`; CI ставит их через apt.
`ros-jazzy-rviz2` не установлен, поэтому проверка выполнена через `check_urdf`, тесты и
живые `tf2_echo`/`view_frames`; launch поддерживает `rviz:=true`.

CI сначала скачивает кит с `ros.lms.ci.nsu.ru`. Если раннер не может разрешить этот
хост (`curl: (6) Could not resolve host`), используется байт-в-байт копия архива из
`ci/course-kit/`; в обоих случаях проверяется один и тот же sha256, то есть проверяется
ровно зафиксированная ревизия `v1-w08`.

## Состав

- `src/course_description/urdf/vehicle.urdf.xacro` — модель: Xacro-параметры
  `base_length/base_width/base_height`, `track`, `wheelbase`, `wheel_radius`,
  `wheel_width`, смещения сенсоров; макросы корпуса, колеса и сенсора;
- `src/course_description/launch/description.launch.py` — `robot_state_publisher`
  с `robot_description` из `xacro`, RViz по аргументу `rviz:=true`;
- `src/course_description/test/test_description.py` — 9 структурных тестов;
- `.github/workflows/ci.yml` — установка ROS 2, разворот модели + `check_urdf`,
  `colcon test`, `check_practice.py PR06` на ките `v1-w08`.

## Ход работы

### 1. Сборка, разворот и проверка структуры

```bash
colcon build --symlink-install
source install/setup.bash
xacro src/course_description/urdf/vehicle.urdf.xacro > /tmp/vehicle.urdf
check_urdf /tmp/vehicle.urdf
colcon test --packages-select course_description
```

`check_urdf`: `root Link: base_link has 7 child(ren)` (камера, лидар, IMU и 4 колеса),
дерево связно и ациклично. Тесты проверяют единственного родителя у каждого звена,
связность, ожидаемых родителей сенсоров, смещения, параметры базы/колеи/радиуса,
наличие `visual`/`collision` и физическую допустимость инерции. Логи:
`evidence/pr06/model-check.txt`, `evidence/pr06/tests.txt`.

### 2. Запуск и QoS преобразований

```bash
ros2 launch course_description description.launch.py        # rviz:=true при наличии RViz
ros2 topic info /tf_static --verbose
timeout 4 ros2 topic echo /tf_static --once \
  --qos-durability transient_local --qos-reliability reliable   # преобразования, exit=0
timeout 4 ros2 topic echo /tf_static --once \
  --qos-durability volatile --qos-reliability reliable          # пусто, exit=124
ros2 run tf2_ros tf2_echo base_link lidar_link                  # Translation: [-0.050, 0.000, 0.450]
ros2 run tf2_tools view_frames
```

`/tf_static`: издатель `/robot_state_publisher`, `Reliability: RELIABLE`,
`Durability: TRANSIENT_LOCAL`. `/tf` (профиль снят при публикации `joint_states`):
`RELIABLE` + `VOLATILE`. Логи: `evidence/pr06/tf-qos.txt`, `tf2-echo.txt`, `frames.gv`;
владельцы и ожидаемые преобразования — `evidence/pr06/frames.md`.

### 3. Дефект: неверный родитель лидара

В отдельной ветке `pr06-defect` у `lidar_link` родителем сделан `camera_link` при том же
смещении в Xacro. `check_urdf` такое дерево принимает, но тест ожидаемого родителя и
тест абсолютного положения падают, а `tf2_echo base_link lidar_link` показывает
`[0.230, 0.000, 0.830]` вместо `[-0.050, 0.000, 0.450]` — лидар уезжает в точку над
камерой. После возврата связи те же тесты снова зелёные (`model-check.txt`).
