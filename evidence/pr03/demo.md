# ПР03. Разбор ноды `patrol`, дефекта и остановки

Прогон 2026-10-05: Linux Mint 22.3 (Ubuntu 24.04), ROS 2 Jazzy, `ROS_DOMAIN_ID=25`,
turtlesim 1.8.4, `turtlesim/msg/Pose` (см. `environment.json`, `pose-type.txt`).

## 1. Как устроена нода

`src/patrol/patrol/patrol.py`:

- `rclpy.init(args=args)` — создаёт контекст rclpy и разбирает `--ros-args`. Здесь же
  применяется remap: `-r cmd_vel:=/turtle1/cmd_vel` меняет имя топика **на уровне CLI**,
  код ноды при этом не меняется. До `init` создавать ноды нельзя.
- `Patrol.__init__` — три сущности: подписка `Pose` на `/turtle1/pose`
  (сохраняется в поле `self._pose_sub`; без ссылки на объект подписку уничтожит
  сборщик мусора), издатель `Twist` в относительное имя `cmd_vel` и таймер 0.1 с.
- `rclpy.spin(node)` — блокирующий цикл обработки: по приходу сообщения вызывается
  `_on_pose`, по таймеру — `_on_timer`. Пока `spin` не вернулся, нода жива.
- `_on_pose` не публикует ничего, только запоминает последнее сообщение. Так частота
  позы (turtlesim публикует её ~62.5 Гц) не влияет на частоту команд: команды выдаёт
  таймер.
- `_on_timer` — `select_command(self._pose)`, чистая функция: пока позы нет (`None`),
  возвращается нулевой `Twist`; после первой позы — `linear.x=0.5`, `angular.z=0.3`,
  ограниченные диапазонами `[0, 0.5]` и `[-1, 1]`. Чистота функции проверяется
  тестами `test_missing_pose_gives_zero_command`, `test_pose_gives_constant_command`,
  `test_command_is_clamped` (`tests.txt`).
- Ctrl+C — SIGINT. В rclpy это `KeyboardInterrupt` (при внешнем shutdown дополнительно
  `ExternalShutdownException`), `spin` возвращает управление, и `finally` освобождает
  ресурсы: `node.destroy_node()` и `rclpy.try_shutdown()`. Важно: `try_shutdown()`,
  а не `shutdown()` — при уже начатом завершении повторный `shutdown()` даёт
  `RCLError: failed to shutdown: rcl_shutdown already called` и выход с кодом 1.
  Итог обоих прогонов — `exit code: 0` (`patrol-broken-log.txt`, `patrol-fixed-log.txt`).
- Нода **не** публикует нулевую команду на выходе: тормозит сам turtlesim — см. п. 4.

## 2. Сбой: относительное имя `cmd_vel`

Запуск без remap (`ros2 run patrol patrol`), turtlesim работает:

```
ros2 node list           -> /patrol, /turtlesim                    (node-list-broken.txt)
ros2 topic list          -> ... /cmd_vel, /turtle1/cmd_vel ...     (topic-list-broken.txt)
ros2 topic info /cmd_vel -v
    Type: geometry_msgs/msg/Twist
    Publisher count: 1     (Node name: patrol)
    Subscription count: 0                                      (cmdvel-info-broken.txt)
ros2 topic info /turtle1/cmd_vel -v
    Publisher count: 0
    Subscription count: 1  (Node name: turtlesim)        (turtle1-cmdvel-info-broken.txt)
ros2 node info /patrol
    Publishers: /cmd_vel: geometry_msgs/msg/Twist    (node-info-patrol-broken.txt)
```

`ros2 topic echo /cmd_vel --once` показывает `x: 0.5`, `z: 0.3` (`echo-cmdvel-broken.txt`):
команда считается и публикуется, но у `/cmd_vel` нет слушателей. Поза при этом не
меняется вовсе — за 3 с между выборками одинаковые значения
`x=5.544444561004639, y=5.544444561004639, theta=0.0` (`pose-broken-t0.txt`,
`pose-broken-t3.txt`). Черепашка неподвижна.

## 3. Исправление remap-ом

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

```
ros2 topic list          -> /turtle1/cmd_vel, ...  (/cmd_vel отсутствует)  (topic-list-fixed.txt)
ros2 topic info /turtle1/cmd_vel -v
    Publisher count: 1     (Node name: patrol)
    Subscription count: 1  (Node name: turtlesim)   (turtle1-cmdvel-info-fixed.txt)
ros2 topic echo /turtle1/cmd_vel --once -> x: 0.5, z: 0.3             (echo-cmdvel-once.txt)
```

Поза поехала: `(6.669164, 8.437393, theta=2.395200)` на одной выборке и
`(7.064710, 6.537017, theta=1.152015)` через ~5 с (`pose-fixed-t0.txt`, `pose-fixed-t3.txt`),
в `Pose` видны `linear_velocity: 0.5`, `angular_velocity: 0.3`. Угол проходит через
границу ±π и остаётся нормированным.

Реальная частота команды за ~10 с (`ros2 topic hz /turtle1/cmd_vel`):

```
average rate: 10.000
    min: 0.099s max: 0.101s std dev: 0.00026s window: 96     (cmdvel-hz-10s.txt)
```

то есть при заявленном периоде 0.1 с поток стабильно 10 Гц.

## 4. Остановка: `Ctrl+C` ≠ мгновенное торможение

После SIGINT нода завершается с кодом 0, но черепашка проходит ещё часть пути:

```
pose-fixed-t3.txt       x: 7.064710   y: 6.537017    theta: 1.152015
--- t+0.0s после SIGINT ---  x: 7.204896  y: 7.125177  theta: 1.516815
    linear_velocity: 0.0   angular_velocity: 0.0
--- t+0.5…t+4.0s ---         те же значения                (pose-after-stop.txt)
```

Смещение между последней выборкой работающей ноды и первой после SIGINT — 0.60 единицы
при команде 0.5 ед/с, то есть черепашка двигалась ещё ~1 с, после чего скорости стали
нулевыми и поза замерла. Это не команда торможения от ноды: turtlesim сам гасит скорости,
если команды не приходили дольше 1 с — `turtlesim/src/turtle.cpp`, ветка `jazzy`:
`velocityCallback` пишет `last_command_time_`, а в `update()` стоит
`if (nh_->now() - last_command_time_ > rclcpp::Duration(1.0, 0)) { lin_vel_x_ = 0.0; lin_vel_y_ = 0.0; ang_vel_ = 0.0; }`.
Поэтому останавливать ноду следует и ждать остановки turtlesim, а не считать выход
процесса мгновенным торможением.

## 5. Что подтверждено чем

| Утверждение | Доказательство |
| --- | --- |
| Без позы команда нулевая; после — 0.5/0.3; ограничение работает | тесты (`tests.txt`) |
| Без remap связь разорвана, поза не меняется | `topic-list-broken.txt`, `cmdvel-info-broken.txt`, `turtle1-cmdvel-info-broken.txt`, `pose-broken-t0/t3.txt` |
| Remap связывает ноду с turtlesim, черепашка едет | `topic-list-fixed.txt`, `turtle1-cmdvel-info-fixed.txt`, `pose-fixed-t0/t3.txt` |
| Поток команды 10 Гц за 10 с | `cmdvel-hz-10s.txt` |
| Ctrl+C: выход 0, тормозит turtlesim своим таймаутом | `patrol-*-log.txt`, `pose-after-stop.txt` |
| Пакет собирается, линтеры и тесты проходят | `build.txt`, `tests.txt` |
