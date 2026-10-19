# ПР04. Параметры ноды patrol

Прогон: Linux Mint 22.3 (Ubuntu 24.04), ROS 2 Jazzy, `ROS_DOMAIN_ID=25`.
Системный пакет `ros-jazzy-turtlesim` на машине отсутствует, поэтому turtlesim 1.8.4
запущен из пакета, распакованного в `/home/covo43k/study/.ros-local` (CI ставит его
штатно через apt). Остальные данные среды — `environment.json`.

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run turtlesim turtlesim_node # терминал 1
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel # терминал 2
```

## 1. Объявленные параметры

```
$ ros2 param list /patrol
  linear_speed
  publish_hz
  start_type_description_service
  turn_rate
  use_sim_time

$ ros2 param get /patrol linear_speed   -> Double value is: 0.5
$ ros2 param get /patrol turn_rate      -> Double value is: 0.3
$ ros2 param get /patrol publish_hz     -> Double value is: 10.0
```

(`param-list.txt`, `param-defaults.txt`.)

## 2. Частота: 10 → 5 Гц

```
$ ros2 topic hz /turtle1/cmd_vel
average rate: 10.001
	min: 0.099s max: 0.100s std dev: 0.00018s window: 44          (hz-10.txt)

$ ros2 param set /patrol publish_hz 5.0
Set parameter successful                                         (param-set-5hz.txt)

$ ros2 topic hz /turtle1/cmd_vel
average rate: 5.000
	min: 0.199s max: 0.201s std dev: 0.00022s window: 24          (hz-5.txt)
```

В логе ноды видно пересоздание таймера, второго таймера нет:

```
[INFO] [patrol]: publish period 0.100 s (10 Hz)
[INFO] [patrol]: publish period 0.200 s (5 Hz)                   (patrol-log.txt)
```

## 3. Скорость

```
$ ros2 param set /patrol linear_speed 0.8
Set parameter successful                                          (param-set-speed.txt)

$ ros2 topic echo /turtle1/cmd_vel --once
linear:
  x: 0.8
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.3                                                          (echo-command.txt)
```

## 4. Отклонение недопустимых значений

| Команда | Ответ |
| --- | --- |
| `publish_hz 0.0` | `Setting parameter failed: publish_hz must be in [1.0, 30.0], got 0.0` |
| `publish_hz -1.0` | `Setting parameter failed: publish_hz must be in [1.0, 30.0], got -1.0` |
| `publish_hz 31.0` | `Setting parameter failed: publish_hz must be in [1.0, 30.0], got 31.0` |
| `publish_hz .nan` | `Setting parameter failed: publish_hz must be a finite number, got nan` |

Логи: `param-set-zero-rejected.txt`, `param-set-negative-rejected.txt`,
`param-set-too-high-rejected.txt`, `param-set-nan.txt`.

После отказа поток не изменился — 5.000 Гц (`hz-after-reject.txt`).

## 5. Дефект: проверка отключена (ветка `pr04-defect`)

Отдельный коммит `ebf499b6eb83346f2a999b2c2e216913fabe395a` отключает проверку в
`add_on_set_parameters_callback`. Та же последовательность команд:

```
$ ros2 param set /patrol publish_hz 5.0
Set parameter successful                       exit=0

$ ros2 param set /patrol publish_hz 0.0
                                               exit=124 (ответа нет, CLI ждёт)

$ ros2 node list
                                               (пусто)

$ ros2 param get /patrol publish_hz
Node not found

patrol processes: 0
```

Лог процесса (`defect-node-log.txt`):

```
[INFO] [patrol]: publish period 0.200 s (5 Hz)
Traceback (most recent call last):
  ...
  File ".../patrol.py", line 108, in _on_parameters_set
    self._start_timer()
  File ".../patrol.py", line 88, in _start_timer
    period = timer_period(self._publish_hz)
  File ".../patrol.py", line 48, in timer_period
    return 1.0 / hz
ZeroDivisionError: float division by zero
```

Исключение выходит из `rclpy.spin` и завершает процесс; `ros2 param set` не получает
ответ. Это и есть воспроизводимый отказ (`defect-validation-off-repro.txt`).

## 6. Возврат проверки: та же команда отклоняется

На ветке `pr04` (проверка включена) тот же тест:

```
$ ros2 param set /patrol publish_hz 5.0
Set parameter successful
$ ros2 param get /patrol publish_hz
Double value is: 5.0

$ ros2 param set /patrol publish_hz 0.0
Setting parameter failed: publish_hz must be in [1.0, 30.0], got 0.0
$ ros2 param get /patrol publish_hz
Double value is: 5.0

$ ros2 topic hz /turtle1/cmd_vel
average rate: 5.000
	min: 0.200s max: 0.200s std dev: 0.00017s window: 24

patrol processes: 1
```

Значение и поток остались прежними, нода жива (`defect-fixed-repro.txt`).

## 7. Готовые сервис и действие

```
$ ros2 service call /clear std_srvs/srv/Empty
response:
std_srvs.srv.Empty_Response()                                    (clear-service.txt)

$ ros2 action list -t
/turtle1/rotate_absolute [turtlesim/action/RotateAbsolute]        (action-list.txt)

$ ros2 action info /turtle1/rotate_absolute
Action clients: 0
Action servers: 1
    /turtlesim                                                    (action-info.txt)

$ ros2 interface show turtlesim/action/RotateAbsolute
# The desired heading in radians
float32 theta
---
# The angular displacement in radians to the starting position
float32 delta
---
# The remaining rotation in radians
float32 remaining                                                 (action-interface.txt)
```

`/clear` — сервис: запрос-ответ, клиент получает результат сразу и не может отменить
уже отправленный запрос. `/turtle1/rotate_absolute` — действие: клиент ставит цель
(`goal` — угол `theta`), получает промежуточный прогресс (`feedback` — `remaining`) и
может отменить выполнение до появления результата (`result` — `delta`).

## 8. Тесты

```
10 passed, 1 skipped                                   (pytest, tests.txt)
11 tests, 0 errors, 0 failures, 1 skipped              (colcon test-result)
```

Чистая функция проверена на 10→5 Гц, ноль, отрицательную частоту, NaN, а также на
границы скорости и поворота.
