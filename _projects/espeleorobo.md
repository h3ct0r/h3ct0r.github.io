---
layout: page
title: EspeleoRobô
description: A ground robot for inspecting caves, galleries, ducts and other confined spaces, developed with Vale and ITV.
years: 2016–2023
role: Coordinator, 2018–2023
category: earlier
importance: 1
---

The EspeleoRobô was developed by Vale, the Instituto Tecnológico Vale (ITV) and SENAI to help Vale's speleologists map caves faster and without exposing people to the risks of confined spaces. It has reconfigurable locomotion for rough terrain and carries LiDAR, cameras and gas sensors.

From 2018 to 2023 I coordinated the project on mapping, localization, path planning and navigation for autonomous operation of the robot. That work produced, among others:

- LiDAR SLAM fused with wheel odometry and inertial data for geometrically poor spaces ([EKF-LOAM](https://doi.org/10.1109/tase.2022.3169442), IEEE T-ASE 2022);
- indoor localization and navigation control, a Best Student Paper finalist at IEEE CASE 2020;
- semi-autonomous inspection and mapping in confined spaces ([JINT 2021](https://doi.org/10.1007/s10846-021-01321-5));
- radio-aware path planning, antenna steering for teleoperation, and tethers for communication in deep galleries;
- related devices for inspecting small-diameter pipes.

The robot is covered by patent applications in the United States, Canada and Australia (*Multi-terrain inspection robotic device and methods for configuring and guiding the same*, Vale S.A. and SENAI), and its ROS software is [open source](https://github.com/ITVRoC/espeleo). This line of work continues at [MIRA]({{ '/research/mira/' | relative_url }}).

{% include project_publications.html tag="espeleorobo" %}
