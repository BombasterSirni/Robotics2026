# PR02. Публикация в топики и диагностика связей

Результат работы с `turtlesim` в ROS 2 Jazzy: сборка кастомного пакета, запуск через launch-файл и демонстрация важности точного именования топиков для доставки сообщений.

## Среда
Ubuntu 24.04, ROS 2 Jazzy. Рабочая директория: `/home/covo43k/study/Robotics2026`. Домен: `ROS_DOMAIN_ID=25`.

## Ход работы

### 1. Сборка и запуск
Собираем пакет `turtle_bringup` (с симлинками) и запускаем симуляцию через launch-файл. Лог сборки сохраняется в `evidence/pr02/build-empty.txt`.

```bash
colcon build --symlink-install --packages-select turtle_bringup \
  > evidence/pr02/build-empty.txt 2>&1

ros2 launch turtle_bringup sim.launch.py
```

В отдельном терминале убеждаемся, что нода поднялась:
```bash
ros2 node list --no-daemon --spin-time 2 > evidence/pr02/node-list-active.txt
```

### 2. Изучение интерфейсов
Проверяем структуру управляющего сообщения `Twist` и тип текущей позы черепахи. Результаты сохраняются в соответствующие файлы в папке `evidence/pr02/`.

```bash
ros2 interface show geometry_msgs/msg/Twist > evidence/pr02/interface-twist.txt
ros2 topic type /turtle1/pose > evidence/pr02/topic-type-pose.txt
ros2 topic echo /turtle1/pose --once > evidence/pr02/echo-pose-once.txt
```

### 3. Воспроизведение сбоя (Wrong Topic)
Черепаха слушает топик `/turtle1/cmd_vel`. Мы намеренно публикуем команды управления в неверный глобальный топик `/cmd_vel`, не ожидая подписчиков (`--wait-matching-subscriptions 0`).

**Терминал A (публикация):**
```bash
timeout 5s ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \
  /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 1.0}, angular: {z: 0.5}}' \
  > evidence/pr02/pub-wrong-loop.txt 2>&1
```

**Терминал B (диагностика):**
Пока публикация идет (или сразу после), проверяем состояние правильного топика. Видим, что подписчик есть, а издателя нет — связь разорвана.
```bash
ros2 topic info /turtle1/cmd_vel --verbose > evidence/pr02/info-turtle-cmdvel-broken.txt
```
*Результат:* Черепаха неподвижна. В логах видно `Publisher count: 0`.

### 4. Исправление (Correct Topic)
Меняем имя топика на корректное `/turtle1/cmd_vel` и отправляем команду один раз.

```bash
ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 1.0}, angular: {z: 0.5}}' \
  > evidence/pr02/pub-correct-once.txt
```
*Результат:* Черепаха начинает движение.

## Причина сбоя
Ошибка в имени топика. Нода `turtlesim` подписана на namespace-специфичный топик `/turtle1/cmd_vel`, тогда как publisher отправлял данные в root-топик `/cmd_vel`. ROS 2 требует строгого совпадения имен каналов для установления соединения между Publisher и Subscriber.

## Проверка отчёта
Из корня репозитория запустите проверку структуры доказательств:
```bash
python3 .course-kit/v1/tools/check_practice.py PR02 --submission .
```