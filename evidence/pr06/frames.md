# ПР06. Системы координат и владельцы преобразований

Прогон 2026-11-01, ROS_DOMAIN_ID=27, Jazzy, `robot_state_publisher` из
`src/course_description/urdf/vehicle.urdf.xacro` (развёрнут `xacro`).

## Дерево преобразований

Корень — `base_link` (родителя нет). Остальные звенья имеют ровно одного родителя,
дерево связно и ациклично (`check_urdf`: `root Link: base_link has 7 child(ren)`).

| Родитель | Дочернее звено | Тип связи | Ожидаемое преобразование (xyz, м) | Владелец публикации |
| --- | --- | --- | --- | --- |
| — | `base_link` | — | корень дерева | — |
| `base_link` | `camera_link` | fixed | `0.28 0.0 0.38` | `/robot_state_publisher` → `/tf_static` |
| `base_link` | `lidar_link` | fixed | `-0.05 0.0 0.45` | `/robot_state_publisher` → `/tf_static` |
| `base_link` | `imu_link` | fixed | `0.0 0.0 0.24` | `/robot_state_publisher` → `/tf_static` |
| `base_link` | `front_left_wheel` | continuous | `0.40 0.31 0.0`, ось `0 1 0` | `/robot_state_publisher` → `/tf` (только при публикации `joint_states`) |
| `base_link` | `front_right_wheel` | continuous | `0.40 -0.31 0.0`, ось `0 1 0` | то же |
| `base_link` | `rear_left_wheel` | continuous | `-0.40 0.31 0.0`, ось `0 1 0` | то же |
| `base_link` | `rear_right_wheel` | continuous | `-0.40 -0.31 0.0`, ось `0 1 0` | то же |

Единственный издатель в этой работе — `/robot_state_publisher`: он публикует фиксированные
связи на `/tf_static` сразу, а связи колёс — на `/tf` при поступлении `joint_states`.
Своих издателей `/tf` нет, поэтому два источника одного преобразования получить нельзя.
В `view_frames` broadcaster показан как `default_authority` — это заглушка инструмента,
фактический издатель берётся из `ros2 topic info /tf_static --verbose`.

`tf2_echo base_link lidar_link` подтверждает точку лидара:
`Translation: [-0.050, 0.000, 0.450]` (файл `tf2-echo.txt`), а `view_frames` —
родителей `camera_link`, `lidar_link`, `imu_link` = `base_link` (`frames.gv`).

## Профили QoS

| Топик | Reliability | Durability | Что это значит |
| --- | --- | --- | --- |
| `/tf_static` | RELIABLE | TRANSIENT_LOCAL | издатель хранит последнее сообщение, поздний подписчик с тем же профилем получает преобразования (`exit=0` в `tf-qos.txt`) |
| `/tf` | RELIABLE | VOLATILE | прошлые сообщения не сохраняются; подписчик получает только новые (профиль снят при публикации `joint_states`) |

Это согласуется с характером данных: фиксированные связи не меняются, поэтому их можно
отдать один раз и хранить; подвижные обновляются непрерывно, и хранить их историю
бессмысленно — важна только свежая пара «время — преобразование».

## Замечания

- `kdl_parser` предупреждает, что у корневого `base_link` задана инерция: KDL игнорирует
  инерцию корня. Это предупреждение, а не ошибка: дерево и преобразования корректны,
  масса корня нужна описанию, а не KDL.
- RViz в этой среде недоступен (`ros-jazzy-rviz2` не установлен), поэтому проверка
  выполнена структурно (`check_urdf`, тесты) и через живые `tf2_echo`/`view_frames`;
  launch поддерживает `rviz:=true` для машины с RViz.
