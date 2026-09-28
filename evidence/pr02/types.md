# Основные топики из PRO2

## 1. cmd_vel
### Тип - с помощью *ros2 topic type /cmd_vel*:
geometry_msgs/msg/Twist

## 2. /turtle1/cmd_vel/
### Тип - с помощью *ros2 topic type /turtle/cmd_vel*:
geometry_msgs/msg/Twist


## Назначение:
Назначение у этих топиков - общее - задает структуру где определены поля линейной скорости и угловой скорости по x, y и z <br>
для описания движения черепахи<br>

// This expresses velocity in free space broken into its linear and angular parts. <br>

Vector3  linear<br>
        float64 x<br>
        float64 y<br>
        float64 z<br>
Vector3  angular<br>
        float64 x<br>
        float64 y<br>
        float64 z<br>