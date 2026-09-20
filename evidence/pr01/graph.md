# Команды и их выводы:

## 1. Список активных нод и их роли:

```bash
ros2 node list --no-daemon --spin-time 2
```

### Результат:
/teleop_turtle - Нода телеуправления черепашкой с клавиатуры
/turtlesim - Нода симулятор черепашки

## 2. Список всех топиков с их типами:

```bash
ros2 topic list -t
```

### Результат:
/parameter_events [rcl_interfaces/msg/ParameterEvent]
/rosout [rcl_interfaces/msg/Log]
/turtle1/cmd_vel [geometry_msgs/msg/Twist]
/turtle1/color_sensor [turtlesim/msg/Color]
/turtle1/pose [turtlesim/msg/Pose]

## 3. Информация о нодах

### Информация о turtlesim

```bash
ros2 node info /turtlesim
```

#### Результат:
/turtlesim
  Subscribers:
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /turtle1/cmd_vel: geometry_msgs/msg/Twist
  Publishers:
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /rosout: rcl_interfaces/msg/Log
    /turtle1/color_sensor: turtlesim/msg/Color
    /turtle1/pose: turtlesim/msg/Pose
  Service Servers:
    /clear: std_srvs/srv/Empty
    /kill: turtlesim/srv/Kill
    /reset: std_srvs/srv/Empty
    /spawn: turtlesim/srv/Spawn
    /turtle1/set_pen: turtlesim/srv/SetPen
    /turtle1/teleport_absolute: turtlesim/srv/TeleportAbsolute
    /turtle1/teleport_relative: turtlesim/srv/TeleportRelative
    /turtlesim/describe_parameters: rcl_interfaces/srv/DescribeParameters
    /turtlesim/get_parameter_types: rcl_interfaces/srv/GetParameterTypes
    /turtlesim/get_parameters: rcl_interfaces/srv/GetParameters
    /turtlesim/get_type_description: type_description_interfaces/srv/GetTypeDescription
    /turtlesim/list_parameters: rcl_interfaces/srv/ListParameters
    /turtlesim/set_parameters: rcl_interfaces/srv/SetParameters
    /turtlesim/set_parameters_atomically: rcl_interfaces/srv/SetParametersAtomically
  Service Clients:

  Action Servers:
    /turtle1/rotate_absolute: turtlesim/action/RotateAbsolute
  Action Clients:


### Информация о turtle_teleop:

```bash
ros2 node info /teleop_turtle
```

#### Результат:
/teleop_turtle
  Subscribers:
    /parameter_events: rcl_interfaces/msg/ParameterEvent
  Publishers:
    /parameter_events: rcl_interfaces/msg/ParameterEvent
    /rosout: rcl_interfaces/msg/Log
    /turtle1/cmd_vel: geometry_msgs/msg/Twist
  Service Servers:
    /teleop_turtle/describe_parameters: rcl_interfaces/srv/DescribeParameters
    /teleop_turtle/get_parameter_types: rcl_interfaces/srv/GetParameterTypes
    /teleop_turtle/get_parameters: rcl_interfaces/srv/GetParameters
    /teleop_turtle/get_type_description: type_description_interfaces/srv/GetTypeDescription
    /teleop_turtle/list_parameters: rcl_interfaces/srv/ListParameters
    /teleop_turtle/set_parameters: rcl_interfaces/srv/SetParameters
    /teleop_turtle/set_parameters_atomically: rcl_interfaces/srv/SetParametersAtomically
  Service Clients:

  Action Servers:

  Action Clients:
    /turtle1/rotate_absolute: turtlesim/action/RotateAbsolute



## 4. Типы топиков

### a. turtle1/pose

```bash
ros2 topic type /turtle1/pose
```

#### Результат:
turtlesim/msg/Pose


### b. Тип топика /parameters_events

```bash
ros2 topic type /parameters_events
```

#### Результат:
rcl_interfaces/msg/ParameterEvent


### c. Тип топика /rosout

```bash
ros2 topic type /rosout
```

#### Результат:
rcl_interfaces/msg/Log


### d. Тип топика /turtle1/cmd_vel

```bash
ros2 topic type /turtle1/cmd_vel
```

#### Результат:
geometry_msgs/msg/Twist


### d. Тип топика /turtle1/color_sensor

```bash
ros2 topic type /turtle1/color_sensor
```

#### Результат:
turtlesim/msg/Color

## 5. Замеры частоты публикации

```bash
ros2 topic hz /turtle1/pose
```

### Результат замеров:

Длительность замера - 10 сек (10 логов)
average rate: 62.494
	min: 0.015s max: 0.017s std dev: 0.00049s window: 64
average rate: 62.501
	min: 0.015s max: 0.017s std dev: 0.00048s window: 127
average rate: 62.484
	min: 0.015s max: 0.017s std dev: 0.00047s window: 190
average rate: 62.493
	min: 0.015s max: 0.017s std dev: 0.00047s window: 253
average rate: 62.490
	min: 0.015s max: 0.017s std dev: 0.00046s window: 316
average rate: 62.496
	min: 0.015s max: 0.017s std dev: 0.00045s window: 379
average rate: 62.493
	min: 0.015s max: 0.017s std dev: 0.00045s window: 442
average rate: 62.497
	min: 0.015s max: 0.017s std dev: 0.00045s window: 505
average rate: 62.500
	min: 0.014s max: 0.017s std dev: 0.00045s window: 568
average rate: 62.498
	min: 0.014s max: 0.017s std dev: 0.00045s window: 631


## 6. До / Сбой / После 

Под сбоем имеется ввиду смена домена №25 на №23, из-за чего связь между участниками домена №25 turtlesim и turtlesim_teleop нарушается, из-за чего второй (teleop нода) не может управлять первым через домен

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

**Мы не меняем симулятор или не переустанавливаем ROS, потому что сбой заключался всего лишь в несоответствии доменов между общающимися участниками-нодами. Достаточно рестартнуть teleop под нужным доменом и все**
