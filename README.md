# PR03. Первая нода: поза и команда

Нода `patrol` для ROS 2 Jazzy: подписка на позу `turtlesim`, таймер 0.1 с и публикация
команды `Twist`. Показан разрыв имён (`cmd_vel` против `/turtle1/cmd_vel`) и его
исправление через remap при запуске.

## Среда

Linux Mint 22.3 (Ubuntu 24.04 noble), ROS 2 Jazzy (ros-core 0.11.0, turtlesim 1.8.4),
Python 3.12.3. Рабочая директория: `/home/covo43k/study/Robotics2026`, домен
`ROS_DOMAIN_ID=25`. Course kit: `v1-w04`, sha256
`fec6b4e886c19146078bf69fbf90a19279a4cd33f656642395350b299efeb226`.
Полные данные — `evidence/pr03/environment.json`.

## Состав

- `src/patrol/patrol/patrol.py` — нода: подписка `turtlesim/msg/Pose` на `/turtle1/pose`
  (callback только запоминает сообщение), таймер 0.1 с, издатель `geometry_msgs/msg/Twist`
  в относительный `cmd_vel`, чистая функция `select_command`;
- `src/patrol/test/test_patrol.py` — тесты чистой функции (нет позы, обычное сообщение,
  ограничение команды);
- `.github/workflows/ci.yml` — сборка и `colcon test` в ROS 2 Jazzy, затем
  `check_practice.py PR03` на зафиксированном course kit.

## Ход работы

### 1. Сборка и тесты

```bash
colcon build --symlink-install --packages-select patrol
source install/setup.bash
/usr/bin/python3 -m pytest src/patrol/test
colcon test --packages-select patrol --event-handlers console_direct+
colcon test-result --verbose
```

Логи: `evidence/pr03/build.txt`, `evidence/pr03/tests.txt`.

### 2. Воспроизведение сбоя

Терминал 1: `ros2 run turtlesim turtlesim_node`. Терминал 2: `ros2 run patrol patrol`.

Издатель уходит в `/cmd_vel` (1 издатель, 0 подписчиков), тогда как turtlesim слушает
`/turtle1/cmd_vel` (0 издателей, 1 подписчик). Поза не меняется — черепашка неподвижна.
Логи: `topic-list-broken.txt`, `cmdvel-info-broken.txt`, `turtle1-cmdvel-info-broken.txt`,
`node-info-patrol-broken.txt`, `pose-broken-t0.txt`, `pose-broken-t3.txt`.

### 3. Исправление remap-ом

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

Топик `/cmd_vel` из графа исчезает, у `/turtle1/cmd_vel` 1 издатель (patrol) и
1 подписчик (turtlesim); черепашка движется по кривой (`linear.x=0.5`, `angular.z=0.3`).
Логи: `topic-list-fixed.txt`, `turtle1-cmdvel-info-fixed.txt`, `echo-cmdvel-once.txt`,
`pose-fixed-t0.txt`, `pose-fixed-t3.txt`.

### 4. Частота команды

```bash
ros2 topic hz /turtle1/cmd_vel
```

За прогон ~10 с: `average rate: 10.000`, период 0.099–0.101 с при заявленных 0.1 с —
`evidence/pr03/cmdvel-hz-10s.txt`.

### 5. Остановка

SIGINT (Ctrl+C) завершает ноду с кодом 0 (`patrol-fixed-log.txt`), но черепашка проходит
ещё ≈0.6 единицы и глохнет своим сторожевым таймером (1 с без команд) —
`evidence/pr03/pose-after-stop.txt`.

Разбор ролей `init`, `spin`, callback и Ctrl+C, а также причина дефекта —
`evidence/pr03/demo.md`.
