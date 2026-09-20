# ПР01. Окружение и граф ROS 2

Результат работы с `turtlesim` в ROS 2 Lyrical: запуск готовых нод,
наблюдение графа, измерение частоты позы и опыт с `ROS_DOMAIN_ID`.

- [Граф, измерения и объяснение сбоя](evidence/pr01/graph.md)
- [Окружение](evidence/pr01/environment.json)
- [Отчёт ROS Doctor](evidence/pr01/doctor.txt)
- [Сводный отчёт для проверки](evidence/pr01/report.json)
- [Использование ИИ](AI_USAGE.md)
- [Workflow GitVerse](.github/workflows/pr01.yml)

## Среда

Ubuntu 24.04, ROS 2 Jazzy, Gazebo Jetty 10.4.0.

## Исправный граф

В A запускаю симулятор:

```bash
ros2 run turtlesim turtlesim_node
```

В B запускаю управление и нажимаю стрелки, оставляя фокус в терминале B:

```bash
ros2 run turtlesim turtle_teleop_key
```

В C сохраняю сведения:

```bash
mkdir -p evidence/pr01
ros2 doctor --report > evidence/pr01/doctor.txt 2>&1
ros2 node list --no-daemon --spin-time 2 > evidence/pr01/nodes-before.txt
ros2 topic list -t > evidence/pr01/topics.txt
ros2 node info /turtlesim > evidence/pr01/turtlesim-info.txt
ros2 node info /teleop_turtle > evidence/pr01/teleop-info.txt
ros2 topic type /turtle1/pose > evidence/pr01/pose-type.txt
POSE_TYPE=$(cat evidence/pr01/pose-type.txt)
ros2 topic echo /turtle1/pose --once > evidence/pr01/pose-before.txt
```

## До / Сбой / После

### До (домен №25) - в терминале C:

```bash
export ROS_DOMAIN_ID=25
ros2 node list --no-daemon --spin-time 2
printf 'exit=%s\n' "$?"
```

Вывод:
/teleop_turtle
/turtlesim
exit=0

То есть внутри одного домена мы видим обе ноды, и если запустить обе, то можно поуправлять turtlesim с помощью teleop

### Сбой (№25 -> №23) - в терминале C:

Turtlesim и teleop ноды теперь  в разных доменах (turtlesim в №25, а teleop в №23)
```bash
export ROS_DOMAIN_ID=25
ros2 node list --no-daemon --spin-time 2
printf 'exit=%s\n' "$?"
```

Вывод:
/turtlesim
exit=130

### После (вернул teleop в №25 домен) - в терминале C:

```bash
export ROS_DOMAIN_ID=25
ros2 node list --no-daemon --spin-time 2
printf 'exit=%s\n' "$?"
```

Вывод:
/teleop_turtle
/turtlesim
exit=0

Значения, сравнение трёх состояний и причина сбоя находятся в
[graph.md](evidence/pr01/graph.md). Скриншоты сняты с окна turtlesim;
проверка доставки основана на выводе CLI и кодах завершения.


## Проверка отчёта

Из корня репозитория, уже на хосте с Python 3 и Git:

```bash
curl -fsSLo course-kit.tar.gz \
  https://ros.lms.ci.nsu.ru/downloads/robotics-course-kit-v1-w01-57866a9c98fa.tar.gz
printf '%s  %s\n' \
  57866a9c98fa3abdec27b35a180697ee680bfb0f05cc015970ce306d6d849fea \
  course-kit.tar.gz | sha256sum -c -
mkdir -p .course-kit
tar -xzf course-kit.tar.gz -C .course-kit
python3 -m json.tool evidence/pr01/environment.json > /dev/null
python3 .course-kit/v1/tools/check_practice.py PR01 --submission .
```

Комплект `v1-w01` зафиксирован по неизменяемому URL и SHA-256. Каталог
`.course-kit/` не входит в Git. Workflow GitVerse использует тот же архив,
проверяет JSON, совпадение digest и контракт evidence. Для ПР01 ROS в CI
не запускается: живой опыт выполнен локально.

В истории два коммита: первый содержит этот README и workflow, второй —
`evidence/pr01/` и `AI_USAGE.md`. Поле `report.commit` указывает на первый.
После push во вкладке **CI/CD** должен завершиться run второго коммита.
Ссылки на репозиторий, полный SHA этого коммита и успешный run составляют сдачу.
Проверка на GitVerse выполняется после публикации;
