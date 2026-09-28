# ***1)*** **Команды:**
## *Команда - Назначение - Мой результат*

### 1. Команда pwd
#### Назначение:
Вывод полного пути до текущего рабочего каталога
#### Мой результат:
/home/covo43k/study/Robotics2026


### 2. Команда printenv ROS_DISTRO ROS_DOMAIN_ID
#### Назначение:
Вывод значения переменных среды ROS_DISTRO и ROS_DOMAIN_ID
#### Мой результат:
Jazzy
25


### 3.1 Команда colcon build --symlink-install --packages-select turtle_bringup \
#### Назначение:
Сборка пакета turtle_bringup, причем конкретно только одного (флаг --packages-select) + с созданием симлинков (вместо просто копирования) и перенос строки через "\"
#### Мой результат:
Starting >>> turtle_bringup
Finished <<< turtle_bringup [1.76s]

Summary: 1 package finished [1.95s]


### 3.2 Команда 2>&1 | tee evidence/pr02/build-empty.txt
#### Назначение:
2>&1 перенаправляет stderr (поток 2) в stdout (поток 1) -> с помощью | переносим вывод команды слева в команду справа "tee ..." -> tee получает вывод Команды 3.1 и отправляет его в терминал и в evidence/pr02/build-empty.txt
#### Мой результат:
Создался файл evidence/pr02/build-empty.txt и в нем:
Starting >>> turtle_bringup
Finished <<< turtle_bringup [1.76s]

Summary: 1 package finished [1.95s]

# ***2)*** **Цикл пакета**:

### 1. Старт - команда ros2 launch turtle_bringup sim.launch.py
#### Назначение:
ros2 launch считывает launch файл (sim.launch.py) где описан сценарий-пайплайн запуска симуляции черепахи, собирая при этом<br> turtlesim_bringup пакет с нодой черепахи
#### Мой результат:
[INFO] [launch]: All log files can be found below /home/covo43k/.ros/log/2026-09-28-00-15-29-073221-covo43k-Modern-15-B7M-59270 <br>
[INFO] [launch]: Default logging verbosity is set to INFO <br>
[INFO] [turtlesim_node-1]: process started with pid [59277] <br>
[turtlesim_node-1] [INFO] [1790529329.233283819] [turtlesim]: Starting turtlesim with node name /turtlesim <br>
[turtlesim_node-1] [INFO] [1790529329.237233128] [turtlesim]: Spawning turtle [turtle1] at x=[5.544445], y=[5.544445], theta=[0.000000] <br>

### 2. Проверка графа - ros2 node list --no-daemon --spin-time 2
#### Назначение:
Вывод списка активных нод в текущем домене (DOMAIN_ID=25)
#### Мой результат:
/turtlesim


### 3. Остановка - ctrl+c
#### Назначение:
Остановка активной ноды
#### Мой результат:
ros2 launch turtle_bringup sim.launch.py^C[WARNING] [launch]: user interrupted with ctrl-c (SIGINT)<br>
[turtlesim_node-1] [INFO] [1790529579.013636235] [rclcpp]: signal_handler(SIGINT/SIGTERM)<br>
[INFO] [turtlesim_node-1]: process has finished cleanly [pid 59277]<br>


# ***3)*** **До / Сбой / После:**

## Команды:

### 1. ros2 interface show geometry_msgs/msg/Twist
#### Назначение:
interface show позволяет детально изучить структуру данных внутри сообщения типа geometry_msgs/msg/Twist
#### Мой результат:
This expresses velocity in free space broken into its linear and angular parts.
Vector3  linear<br>
        float64 x<br>
        float64 y<br>
        float64 z<br>
Vector3  angular<br>
        float64 x<br>
        float64 y<br>
        float64 z<br>

### 2. ros2 topic type /turtle1/pose
#### Назначение:
Вывод типа топика /turtle1/pose
#### Мой результат:
turtlesim/msg/Pose


### 3. ros2 topic echo /turtle1/pose --once
#### Назначение:
"Подслушиваем" одно сообщение по топикку /turtle1/pose -> выводим в терминал
#### Мой результат:
x: 3.5364978313446045<br>
y: 7.529224395751953<br>
theta: -1.567191481590271<br>
linear_velocity: 0.0<br>
angular_velocity: 0.0<br>


### 4. ros2 topic pub --once /turtle1/cmd_vel geometry_msgs/msg/Twist \ '{linear: {x: 1.0}, angular: {z: 0.5}}'
#### Назначение:
Отправляем единожды в топик /turtle1/cmd_vel сообщение для turtlesim в виде типа geometry_msgs/msg/Twist, который turtlesim активно считывает для управления
#### Мой результат:
publisher: beginning loop
publishing #1: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, y=0.0, z=0.5))


### 5.  ros2 topic pub --rate 1 --wait-matching-subscriptions 0 \ /cmd_vel geometry_msgs/msg/Twist \ '{linear: {x: 1.0}, angular: {z: 0.5}}'    
#### Назначение:
Отправляем в топик /cmd_vel Twist-сообщение, не ожидая активных подписчиков, и мы так и будем пытаться в цикле стучаться в не тот топик<br>, который наша черепаха не слушает
#### Мой результат:
publisher: beginning loop<br>
publishing #1: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, <br> y=0.0, z=0.5))<br>

publishing #2: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0,<br> y=0.0, z=0.5))<br>

publishing #3: geometry_msgs.msg.Twist(linear=geometry_msgs.msg.Vector3(x=1.0, y=0.0, z=0.0), angular=geometry_msgs.msg.Vector3(x=0.0, <br> y=0.0, z=0.5))<br>
..... и так повторяется бесконечно раз <br>


### 6. ros2 topic info <название топика> --verbose
#### Назначение:
Выводим детальную информацию (с помощью --verbose) о текущем топике - какие сообщения через него проходят
#### Мой результат на cmd_vel
Type: geometry_msgs/msg/Twist<br>

Publisher count: 1<br>

Node name: _ros2cli_83638<br>
Node namespace: /<br>
Topic type: geometry_msgs/msg/Twist<br>
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a<br>
Endpoint type: PUBLISHER<br>
GID: 01.0f.62.ae.b6.46.59.24.00.00.00.00.00.00.07.03<br>
QoS profile:<br>
  Reliability: RELIABLE<br>
  History (Depth): UNKNOWN<br>
  Durability: VOLATILE<br>
  Lifespan: Infinite<br>
  Deadline: Infinite<br>
  Liveliness: AUTOMATIC<br>
  Liveliness lease duration: Infinite<br>

Subscription count: 0


## До:
1. Всё в одном домене 25<br>
2. В терминале A крутится собранный пакет черепахи<br>
3. В терминале B я запустил: <br>
```bash
ros2 topic pub --rate 1 --wait-matching-subscriptions 0   /turtle1/cmd_vel geometry_msgs/msg/Twist   '{linear: {x: 1.0}, angular: {z: 0.5}}'
```
4. В окне черепахи - она движется по кругу<br>
5. В терминале C после ввода: <br>
```bash
ros2 topic info /turtle1/cmd_vel --verbose
```
Вывод такой:<br>
Type: geometry_msgs/msg/Twist<br>

Publisher count: 1<br>

Node name: _ros2cli_87168<br>
Node namespace: /<br>
Topic type: geometry_msgs/msg/Twist<br>
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a<br>
Endpoint type: PUBLISHER<br>
GID: 01.0f.62.ae.80.54.b1.79.00.00.00.00.00.00.07.03<br>
QoS profile:<br>
  Reliability: RELIABLE<br>
  History (Depth): UNKNOWN<br>
  Durability: VOLATILE<br>
  Lifespan: Infinite<br>
  Deadline: Infinite<br>
  Liveliness: AUTOMATIC<br>
  Liveliness lease duration: Infinite<br>

Subscription count: 1<br>

Node name: turtlesim<br>
Node namespace: /<br>
Topic type: geometry_msgs/msg/Twist<br>
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a<br>
Endpoint type: SUBSCRIPTION<br>
GID: 01.0f.62.ae.d1.f6.83.94.00.00.00.00.00.00.1d.04<br>
QoS profile:<br>
  Reliability: RELIABLE<br>
  History (Depth): UNKNOWN<br>
  Durability: VOLATILE<br>
  Lifespan: Infinite<br>
  Deadline: Infinite<br>
  Liveliness: AUTOMATIC<br>
  Liveliness lease duration: Infinite<br>

6. Видно что связь между publisher (терминал B) и subcriber (терминал A) - и ее можно наблюдать в терминале C<br>

## Сбой:
#### Суть:
Указать название топика неверно: вместо /turtle1/cmd_vel указать просто cmd_vel
#### Итог:
Publisher (терминал B) отправляет Twist-сообщения в топик cmd_vel, когда как Subscriber (терминал A) слушает /turtle1/cmd_vel и не<br> получает данные сообщения<br>
поэтому черепаха не получает инструкции и не двигается<br>

```bash
ros2 topic info /turtle1/cmd_vel --verbose
``` 
##### Вывод:<br>
Type: geometry_msgs/msg/Twist<br>

Publisher count: 0<br>

Subscription count: 1<br>

Node name: turtlesim<br>
Node namespace: /<br>
Topic type: geometry_msgs/msg/Twist<br>
Topic type hash: RIHS01_9c45bf16fe0983d80e3cfe750d6835843d265a9a6c46bd2e609fcddde6fb8d2a<br>
Endpoint type: SUBSCRIPTION<br>
GID: 01.0f.62.ae.d1.f6.83.94.00.00.00.00.00.00.1d.04<br>
QoS profile:<br>
  Reliability: RELIABLE<br>
  History (Depth): UNKNOWN<br>
  Durability: VOLATILE<br>
  Lifespan: Infinite<br>
  Deadline: Infinite<br>
  Liveliness: AUTOMATIC<br>
  Liveliness lease duration: Infinite<br>


**То есть никто не отправляет соо по нужному топику, а черепаха ждет по нужному**


## После сбоя (Исправление):

### Способ фикса:
*Меняем в терминале B название топика на правильное - которое слушает черепаха*<br>
*А именно с /cmd_vel на /turtle1/cmd_vel*
