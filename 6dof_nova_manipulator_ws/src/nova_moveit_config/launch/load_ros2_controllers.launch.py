#!/usr/bin/env python3
"""
Launch ROS 2 controllers for the robot.

This script creates a launch description that starts the necessary controllers
for operating the robotic arm in a specific sequence.

Launched Controllers:
    1. Joint State Broadcaster: Publishes joint states to /joint_states
    2. Arm Controller: Controls the robot arm movements via /follow_joint_trajectory
    # 3. Gripper Action Controller: Controls gripper actions via /gripper_action (disabled: no gripper)

Launch Sequence:
    1. Joint State Broadcaster
    2. Arm Controller (starts after Joint State Broadcaster)
    # 3. Gripper Action Controller (starts after Arm Controller) (disabled: no gripper)

:author: Mahdi Momeni
:date: November 15, 2026
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Generate a launch description for sequentially starting robot controllers.

    Uses `controller_manager/spawner` so each controller waits for
    `/controller_manager` to become available and honors `use_sim_time`.

    Returns:
        LaunchDescription: Launch description containing sequenced controller starts
    """
    use_sim_time = LaunchConfiguration("use_sim_time")

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name="use_sim_time",
        default_value="false",
        choices=["true", "false"],
        description="Use simulation (Gazebo) clock if true",
    )

    # Start joint state broadcaster
    start_joint_state_broadcaster_cmd = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    # Start arm controller
    start_arm_controller_cmd = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "arm_controller",
            "--controller-manager",
            "/controller_manager",
        ],
        parameters=[{"use_sim_time": use_sim_time}],
        output="screen",
    )

    # Launch the arm controller only if joint_state_broadcaster succeeded
    def on_jsb_exit(event, _context):
        if event.returncode != 0:
            return [
                LogInfo(
                    msg=f"joint_state_broadcaster spawner exited with code {event.returncode}; skipping arm_controller."
                )
            ]
        return [start_arm_controller_cmd]

    load_arm_controller_cmd = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=start_joint_state_broadcaster_cmd,
            on_exit=on_jsb_exit,
        )
    )

    # Create the launch description and populate
    ld = LaunchDescription()

    # Add the actions to the launch description in sequence
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(start_joint_state_broadcaster_cmd)
    ld.add_action(load_arm_controller_cmd)

    return ld
