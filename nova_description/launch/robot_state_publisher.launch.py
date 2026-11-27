#!/usr/bin/env python3
"""
Launch RViz visualization for the Nova 3 robot.

This launch file sets up the complete visualization environment for the Nova 3 robot,
including robot state publisher, joint state publisher, and RViz2. It handles loading
and processing of URDF/XACRO files and controller configurations.

author: Mahdi Momeni
date: November 21, 2026
"""

import os
import tempfile

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, SetLaunchConfiguration
from launch.conditions import IfCondition
from launch.substitutions import (
    AndSubstitution,
    Command,
    LaunchConfiguration,
    NotSubstitution,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def process_ros2_controllers_config(context):
    """Generate a robot-specific ros2_controllers.yaml from the base template.

    Reads `config/nova/ros2_controllers_template.yaml` from `nova_moveit_config`,
    substitutes `${robot_name}`, and writes the output to a temporary directory
    (unless `controllers_file` was explicitly provided) so neither `src/` nor
    `install/` is mutated and any `robot_name` is supported.

    Args:
        context: Launch context containing configuration values

    Returns:
        list: Launch actions setting `controllers_file` if generated
    """
    explicit_file = LaunchConfiguration("controllers_file").perform(context)
    if explicit_file:
        return []

    robot_name = LaunchConfiguration("robot_name").perform(context)

    template_path = os.path.join(
        FindPackageShare("nova_moveit_config").perform(context),
        "config",
        "nova",
        "ros2_controllers_template.yaml",
    )
    with open(template_path, "r", encoding="utf-8") as file:
        template_content = file.read()

    processed_content = template_content.replace("${robot_name}", robot_name)

    output_dir = os.path.join(tempfile.gettempdir(), "nova_ros2_control")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{robot_name}_ros2_controllers.yaml")
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(processed_content)

    return [SetLaunchConfiguration("controllers_file", output_path)]


# Define the arguments for the XACRO file
ARGUMENTS = [
    DeclareLaunchArgument(
        "robot_name", default_value="nova", description="Name of the robot"
    ),
    DeclareLaunchArgument(
        "add_world",
        default_value="true",
        choices=["true", "false"],
        description="Whether to add world link",
    ),
    DeclareLaunchArgument(
        "base_link",
        default_value=[LaunchConfiguration("robot_name"), "_base_link"],
        description="Name of the base link",
    ),
    DeclareLaunchArgument(
        "base_type", default_value="g_shape", description="Type of the base"
    ),
    DeclareLaunchArgument(
        "flange_link",  # End Effector
        default_value=[LaunchConfiguration("robot_name"), "_end_link"],
        description="Name of the flange link",  # Name of the end effector
    ),
    DeclareLaunchArgument(
        "use_camera",
        default_value="false",
        choices=["true", "false"],
        description="Whether to use the RGBD Gazebo plugin for point cloud",
    ),
    DeclareLaunchArgument(
        "use_gazebo",
        default_value="false",
        choices=["true", "false"],
        description="Whether to use Gazebo simulation",
    ),
    DeclareLaunchArgument(
        "controllers_file",
        default_value="",
        description="Path to ros2_controllers.yaml (generated from template if empty)",
    ),
    # DeclareLaunchArgument(
    #     "use_gripper",
    #     default_value="false",
    #     choices=["true", "false"],
    #     description="Whether to attach a gripper",
    # ),
]


def generate_launch_description():
    """Generate the launch description for the Nova 3 robot visualization.

    This function sets up all necessary nodes and parameters for visualizing
    the Nova 3 robot in RViz, including:
    - Robot state publisher for broadcasting transforms
    - Joint state publisher for simulating joint movements
    - RViz for visualization

    Returns:
        LaunchDescription: Complete launch description for the visualization setup
    """
    # Define filenames
    urdf_package = "nova_description"
    urdf_filename = "nova.urdf.xacro"
    rviz_config_filename = "nova_description.rviz"

    # Set paths to important files
    pkg_share_description = FindPackageShare(urdf_package)
    default_urdf_model_path = PathJoinSubstitution(
        [pkg_share_description, "urdf", "mech", urdf_filename]
    )
    default_rviz_config_path = PathJoinSubstitution(
        [pkg_share_description, "rviz", rviz_config_filename]
    )

    # Launch configuration variables
    jsp_gui = LaunchConfiguration("jsp_gui")
    rviz_config_file = LaunchConfiguration("rviz_config_file")
    urdf_model = LaunchConfiguration("urdf_model")
    use_jsp = LaunchConfiguration("use_jsp")
    use_rviz = LaunchConfiguration("use_rviz")
    use_sim_time = LaunchConfiguration("use_sim_time")

    # Declare the launch arguments
    declare_jsp_gui_cmd = DeclareLaunchArgument(
        name="jsp_gui",
        default_value="true",
        choices=["true", "false"],
        description="Flag to enable joint_state_publisher_gui when use_jsp is true",
    )

    declare_rviz_config_file_cmd = DeclareLaunchArgument(
        name="rviz_config_file",
        default_value=default_rviz_config_path,
        description="Full path to the RVIZ config file to use",
    )

    declare_urdf_model_path_cmd = DeclareLaunchArgument(
        name="urdf_model",
        default_value=default_urdf_model_path,
        description="Absolute path to robot urdf file",
    )

    declare_use_jsp_cmd = DeclareLaunchArgument(
        name="use_jsp",
        default_value="true",
        choices=["true", "false"],
        description="Enable the joint state publisher (GUI or non-GUI based on jsp_gui)",
    )

    declare_use_rviz_cmd = DeclareLaunchArgument(
        name="use_rviz",
        default_value="true",
        choices=["true", "false"],
        description="Whether to start RVIZ",
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name="use_sim_time",
        default_value="false",
        choices=["true", "false"],
        description="Use simulation (Gazebo) clock if true",
    )

    robot_description_content = ParameterValue(
        Command(
            [
                "xacro",
                " ",
                urdf_model,
                " ",
                "robot_name:=",
                LaunchConfiguration("robot_name"),
                " ",
                "add_world:=",
                LaunchConfiguration("add_world"),
                " ",
                "base_link:=",
                LaunchConfiguration("base_link"),
                " ",
                "base_type:=",
                LaunchConfiguration("base_type"),
                " ",
                "flange_link:=",
                LaunchConfiguration("flange_link"),
                " ",
                "use_camera:=",
                LaunchConfiguration("use_camera"),
                " ",
                "use_gazebo:=",
                LaunchConfiguration("use_gazebo"),
                " ",
                "controllers_file:=",
                LaunchConfiguration("controllers_file"),
                # " ",
                # "use_gripper:=",
                # LaunchConfiguration("use_gripper"),
            ]
        ),
        value_type=str,
    )

    # Subscribe to the joint states of the robot, and publish the 3D pose of each link.
    start_robot_state_publisher_cmd = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {
                "use_sim_time": use_sim_time,
                "robot_description": robot_description_content,
            }
        ],
    )

    # Publish the joint state values for the non-fixed joints in the URDF file.
    # Depending on jsp_gui, either launch joint_state_publisher or joint_state_publisher_gui when use_jsp is true.
    start_joint_state_publisher_cmd = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(AndSubstitution(use_jsp, NotSubstitution(jsp_gui))),
    )

    start_joint_state_publisher_gui_cmd = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(AndSubstitution(use_jsp, jsp_gui)),
    )

    # Launch RViz
    start_rviz_cmd = Node(
        condition=IfCondition(use_rviz),
        package="rviz2",
        executable="rviz2",
        output="screen",
        arguments=["-d", rviz_config_file],
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # Create the launch description and populate
    ld = LaunchDescription(ARGUMENTS)

    # Process the controller configuration before starting nodes
    ld.add_action(OpaqueFunction(function=process_ros2_controllers_config))

    # Declare the launch options
    ld.add_action(declare_jsp_gui_cmd)
    ld.add_action(declare_rviz_config_file_cmd)
    ld.add_action(declare_urdf_model_path_cmd)
    ld.add_action(declare_use_jsp_cmd)
    ld.add_action(declare_use_rviz_cmd)
    ld.add_action(declare_use_sim_time_cmd)

    # Add any actions
    ld.add_action(start_joint_state_publisher_cmd)
    ld.add_action(start_joint_state_publisher_gui_cmd)
    ld.add_action(start_robot_state_publisher_cmd)
    ld.add_action(start_rviz_cmd)

    return ld
