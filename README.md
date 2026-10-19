# PR04. Параметризуем движение

Нода `patrol` из ПР03 с параметрами `linear_speed`, `turn_rate`, `publish_hz`: значения
проверяются до применения, допустимая смена частоты пересоздаёт таймер. Показан
воспроизводимый отказ при отключённой проверке и отклонение недопустимых значений.

## Среда

Linux Mint 22.3 (Ubuntu 24.04 noble), ROS 2 Jazzy (ros-core 0.11.0), turtlesim 1.8.4,
Python 3.12.3. Рабочая директория: `/home/covo43k/study/Robotics2026`, домен
`ROS_DOMAIN_ID=25`. Course kit: `v1-w07`, sha256
`001f7ec79674d09a0f7eff2ad0935f58c95101b0cf200425c368f41579d6a31c`.
Полные данные — `evidence/pr04/environment.json`.

Системный пакет `ros-jazzy-turtlesim` на машине отсутствует, поэтому для локального
прогона использован тот же пакет 1.8.4, распакованный из `.deb` в отдельный префикс
(CI ставит его штатно через apt).

## Состав

- `src/patrol/patrol/patrol.py` — нода: подписка `/turtle1/pose`, таймер публикации,
  параметры и проверка входа; чистые функции `validate_parameter`, `timer_period`,
  `select_command`;
- `src/patrol/test/test_patrol.py` — тесты команды и проверки параметров;
- `.github/workflows/ci.yml` — сборка, `colcon test` и `check_practice.py PR04`
  на зафиксированном ките `v1-w07`.

## Параметры

| Параметр | По умолчанию | Допустимо |
| --- | --- | --- |
| `linear_speed` | 0.5 м/с | 0–1 м/с |
| `turn_rate` | 0.3 рад/с | −1–1 рад/с |
| `publish_hz` | 10.0 Гц | 1–30 Гц |

Проверка выполняется в `add_on_set_parameters_callback` **до** применения: недопустимое
значение отклоняется с причиной, активное состояние не меняется. Принятые значения
применяются в `add_post_set_parameters_callback`; смена `publish_hz` уничтожает прежний
таймер (`destroy_timer`) и создаёт новый с периодом `1/publish_hz` — двух таймеров
одновременно не остаётся.

## Ход работы

### 1. Сборка и тесты

```bash
colcon build --symlink-install --packages-select patrol
source install/setup.bash
/usr/bin/python3 -m pytest src/patrol/test
colcon test --packages-select patrol --event-handlers console_direct+
colcon test-result --verbose
```

Логи: `evidence/pr04/build.txt`, `evidence/pr04/tests.txt`.

### 2. Параметры в работе

Нода запущена с remap, чтобы команда доходила до turtlesim:

```bash
ros2 run patrol patrol --ros-args -r cmd_vel:=/turtle1/cmd_vel
```

- `ros2 param list /patrol` — три параметра (`param-list.txt`);
- значения по умолчанию 0.5 / 0.3 / 10.0 (`param-defaults.txt`);
- `ros2 topic hz /turtle1/cmd_vel` до смены — 10.001 Гц (`hz-10.txt`);
- `ros2 param set /patrol publish_hz 5.0` → `Set parameter successful`, поток 5.000 Гц
  (`param-set-5hz.txt`, `hz-5.txt`), в логе ноды — новый период 0.200 с;
- `ros2 param set /patrol linear_speed 0.8` → в `/turtle1/cmd_vel` идёт `linear.x=0.8`
  (`param-set-speed.txt`, `echo-command.txt`).

### 3. Отклонение недопустимых значений

| Команда | Результат |
| --- | --- |
| `ros2 param set /patrol publish_hz 0.0` | `Setting parameter failed: publish_hz must be in [1.0, 30.0], got 0.0` |
| `ros2 param set /patrol publish_hz -1.0` | отклонено той же причиной |
| `ros2 param set /patrol publish_hz 31.0` | отклонено той же причиной |
| `ros2 param set /patrol publish_hz .nan` | `publish_hz must be a finite number, got nan` |

После отказа `publish_hz` остаётся 5.0, поток — 5.000 Гц (`hz-after-reject.txt`):
значение и активное состояние сохранены. Логи: `param-set-zero-rejected.txt`,
`param-set-negative-rejected.txt`, `param-set-too-high-rejected.txt`, `param-set-nan.txt`.

### 4. Дефект: проверка частоты отключена

В отдельной ветке `pr04-defect` (коммит с отключённой проверкой) значение `0.0`
доходит до таймера и воспроизводимо роняет ноду — см. `defect-validation-off-repro.txt`.
После возврата проверки та же команда отклоняется, значение и поток не меняются
(`defect-fixed-repro.txt`).

### 5. Готовые сервис и действие

- `ros2 service call /clear std_srvs/srv/Empty` → ответ `Empty_Response`
  (`clear-service.txt`);
- `ros2 action list -t` → `/turtle1/rotate_absolute [turtlesim/action/RotateAbsolute]`
  (`action-list.txt`, `action-info.txt`, `action-interface.txt`).

Сервис `/clear` — запрос-ответ: клиент вызывает его и сразу получает результат, без
промежуточных состояний. `/turtle1/rotate_absolute` — действие: клиент ставит цель
(`goal`, желаемый угол `theta`), получает промежуточный прогресс (`feedback`, `remaining`)
и может отменить выполнение до результата (`result`, `delta`).
