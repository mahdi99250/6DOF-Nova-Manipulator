#!/usr/bin/env python3
"""
Launch Gazebo simulation with a robot.

This launch file sets up a complete ROS 2 simulation environment with Gazebo for
a Nova 3 robot.

:author: Mahdi Momeni
:date: November 16, 2026
"""

import os

from launch import LaunchDescription
from launch.actions import (
    AppendEnvironmentVariable,
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import (
    AndSubstitution,
    LaunchConfiguration,
    NotSubstitution,
    PathJoinSubstitution,
)
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    """
    Generate a launch description for the Gazebo simulation.

    This function sets up all necessary parameters, paths, and nodes required to launch
    the Gazebo simulation with a robot. It handles:
    1. Setting up package paths and constants
    2. Declaring launch arguments for robot configuration
    3. Setting up the Gazebo environment
    4. Spawning the robot in simulation

    Returns:
        LaunchDescription: A complete launch description for the simulation
    """
    # Constants for paths to different files and folders
    package_name_gazebo = "nova_gazebo"
    package_name_description = "nova_description"
    package_name_moveit = "nova_moveit_config"

    default_robot_name = "nova"
    gazebo_models_path = "models"
    default_world_file = "pick_and_place_demo.world"
    gazebo_worlds_path = "worlds"

    ros_gz_bridge_config_file_path = "config/ros_gz_bridge.yaml"
    ros_gz_camera_bridge_config_file_path = "config/ros_gz_camera_bridge.yaml"

    # Set the path to different files and folders
    pkg_ros_gz_sim = FindPackageShare(package="ros_gz_sim").find("ros_gz_sim")
    pkg_share_gazebo = FindPackageShare(package=package_name_gazebo).find(
        package_name_gazebo
    )
    pkg_share_description = FindPackageShare(package=package_name_description).find(
        package_name_description
    )
    pkg_share_moveit = FindPackageShare(package=package_name_moveit).find(
        package_name_moveit
    )

    gazebo_models_path = os.path.join(pkg_share_gazebo, gazebo_models_path)
    gazebo_resource_paths = os.pathsep.join(
        [gazebo_models_path, os.path.dirname(pkg_share_description)]
    )
    default_ros_gz_bridge_config_file_path = os.path.join(
        pkg_share_gazebo, ros_gz_bridge_config_file_path
    )
    default_ros_gz_camera_bridge_config_file_path = os.path.join(
        pkg_share_gazebo, ros_gz_camera_bridge_config_file_path
    )

    # Launch configuration variables
    jsp_gui = LaunchConfiguration("jsp_gui")
    load_controllers = LaunchConfiguration("load_controllers")
    robot_name = LaunchConfiguration("robot_name")
    use_rviz = LaunchConfiguration("use_rviz")
    use_camera = LaunchConfiguration("use_camera")
    use_gazebo = LaunchConfiguration("use_gazebo")
    use_jsp = LaunchConfiguration("use_jsp")
    use_robot_state_pub = LaunchConfiguration("use_robot_state_pub")
    use_sim_time = LaunchConfiguration("use_sim_time")
    world_file = LaunchConfiguration("world_file")

    world_path = PathJoinSubstitution(
        [pkg_share_gazebo, gazebo_worlds_path, world_file]
    )

    # Set the pose configuration variables
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    roll = LaunchConfiguration("roll")
    pitch = LaunchConfiguration("pitch")
    yaw = LaunchConfiguration("yaw")

    # Declare the launch arguments
    declare_robot_name_cmd = DeclareLaunchArgument(
        name="robot_name",
        default_value=default_robot_name,
        description="The name for the robot",
    )

    declare_load_controllers_cmd = DeclareLaunchArgument(
        name="load_controllers",
        default_value="true",
        choices=["true", "false"],
        description="Flag to enable loading of ROS 2 controllers",
    )

    declare_use_robot_state_pub_cmd = DeclareLaunchArgument(
        name="use_robot_state_pub",
        default_value="true",
        choices=["true", "false"],
        description="Flag to enable robot state publisher",
    )

    # GUI and visualization arguments
    declare_jsp_gui_cmd = DeclareLaunchArgument(
        name="jsp_gui",
        default_value="false",
        choices=["true", "false"],
        description="Flag to enable joint_state_publisher_gui",
    )

    declare_use_jsp_cmd = DeclareLaunchArgument(
        name="use_jsp",
        default_value="false",
        choices=["true", "false"],
        description="Flag to enable joint_state_publisher",
    )

    declare_use_camera_cmd = DeclareLaunchArgument(
        name="use_camera",
        default_value="false",
        choices=["true", "false"],
        description="Flag to enable the RGBD camera for Gazebo point cloud simulation",
    )

    declare_use_gazebo_cmd = DeclareLaunchArgument(
        name="use_gazebo",
        default_value="true",
        choices=["true", "false"],
        description="Flag to enable Gazebo",
    )

    declare_use_rviz_cmd = DeclareLaunchArgument(
        name="use_rviz",
        default_value="true",
        choices=["true", "false"],
        description="Flag to enable RViz",
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        name="use_sim_time",
        default_value="true",
        choices=["true", "false"],
        description="Use simulation (Gazebo) clock if true",
    )

    declare_world_cmd = DeclareLaunchArgument(
        name="world_file",
        default_value=default_world_file,
        description="World file name (e.g., empty.world, house.world, pick_and_place_demo.world)",
    )

    # Pose arguments
    declare_x_cmd = DeclareLaunchArgument(
        name="x",
        default_value="0.0",
        description="x component of initial position, meters",
    )

    declare_y_cmd = DeclareLaunchArgument(
        name="y",
        default_value="0.0",
        description="y component of initial position, meters",
    )

    declare_z_cmd = DeclareLaunchArgument(
        name="z",
        default_value="0.05",
        description="z component of initial position, meters",
    )

    declare_roll_cmd = DeclareLaunchArgument(
        name="roll",
        default_value="0.0",
        description="roll angle of initial orientation, radians",
    )

    declare_pitch_cmd = DeclareLaunchArgument(
        name="pitch",
        default_value="0.0",
        description="pitch angle of initial orientation, radians",
    )

    declare_yaw_cmd = DeclareLaunchArgument(
        name="yaw",
        default_value="0.0",
        description="yaw angle of initial orientation, radians",
    )

    # Prevent joint_state_publisher from conflicting with joint_state_broadcaster on /joint_states
    controllers_active = AndSubstitution(use_gazebo, load_controllers)
    effective_use_jsp = AndSubstitution(use_jsp, NotSubstitution(controllers_active))

    warn_jsp_conflict_cmd = LogInfo(
        msg="Ignoring use_jsp:=true because joint_state_broadcaster is enabled via load_controllers:=true.",
        condition=IfCondition(AndSubstitution(use_jsp, controllers_active)),
    )

    warn_no_rsp_cmd = LogInfo(
        msg="Skipping Gazebo robot spawn and controller loading because use_robot_state_pub is false (/robot_description unavailable).",
        condition=IfCondition(
            AndSubstitution(use_gazebo, NotSubstitution(use_robot_state_pub))
        ),
    )

    # Include Robot State Publisher launch file if enabled
    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    pkg_share_description, "launch", "robot_state_publisher.launch.py"
                )
            ]
        ),
        launch_arguments={
            "jsp_gui": jsp_gui,
            "robot_name": robot_name,
            "use_camera": use_camera,
            "use_gazebo": use_gazebo,
            "use_jsp": effective_use_jsp,
            "use_rviz": use_rviz,
            "use_sim_time": use_sim_time,
        }.items(),
        condition=IfCondition(use_robot_state_pub),
    )

    # Include ROS 2 Controllers launch file if enabled
    load_controllers_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [
                os.path.join(
                    pkg_share_moveit, "launch", "load_ros2_controllers.launch.py"
                )
            ]
        ),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
        condition=IfCondition(load_controllers),
    )

    # Set Gazebo model and description resource paths
    set_env_vars_resources = AppendEnvironmentVariable(
        "GZ_SIM_RESOURCE_PATH", gazebo_resource_paths
    )

    # Start Gazebo
    start_gazebo_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, "launch", "gz_sim.launch.py")
        ),
        launch_arguments=[("gz_args", [" -r -v 4 ", world_path])],
        condition=IfCondition(use_gazebo),
    )

    # Bridge ROS topics and Gazebo messages for establishing communication
    start_gazebo_ros_bridge_cmd = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {
                "config_file": default_ros_gz_bridge_config_file_path,
            }
        ],
        output="screen",
        condition=IfCondition(use_gazebo),
    )

    # Bridge camera sensor topics only when both Gazebo and camera are enabled
    start_gazebo_ros_camera_bridge_cmd = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        parameters=[
            {
                "config_file": default_ros_gz_camera_bridge_config_file_path,
                "use_sim_time": use_sim_time,
            }
        ],
        output="screen",
        condition=IfCondition(AndSubstitution(use_gazebo, use_camera)),
    )

    # Includes optimizations to minimize latency and bandwidth when streaming image data
    start_gazebo_ros_image_bridge_cmd = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=[
            "/camera_head/depth_image",
            "/camera_head/image",
        ],
        remappings=[
            ("/camera_head/depth_image", "/camera_head/depth/image_rect_raw"),
            ("/camera_head/image", "/camera_head/color/image_raw"),
        ],
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(AndSubstitution(use_gazebo, use_camera)),
    )

    # Spawn the robot
    start_gazebo_ros_spawner_cmd = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic",
            "/robot_description",
            "-name",
            robot_name,
            "-allow_renaming",
            "true",
            "-x",
            x,
            "-y",
            y,
            "-z",
            z,
            "-R",
            roll,
            "-P",
            pitch,
            "-Y",
            yaw,
        ],
        condition=IfCondition(AndSubstitution(use_gazebo, use_robot_state_pub)),
    )

    # Load ROS 2 controllers only if the robot spawned successfully
    def on_spawner_exit(event, _context):
        if event.returncode != 0:
            return [
                LogInfo(
                    msg=f"Gazebo spawner exited with code {event.returncode}; skipping controller loading."
                )
            ]
        return [load_controllers_cmd]

    load_controllers_after_spawn_cmd = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=start_gazebo_ros_spawner_cmd,
            on_exit=on_spawner_exit,
        )
    )

    # Create the launch description and populate
    ld = LaunchDescription()

    # Declare the launch options
    ld.add_action(declare_robot_name_cmd)
    ld.add_action(declare_jsp_gui_cmd)
    ld.add_action(declare_load_controllers_cmd)
    ld.add_action(declare_use_camera_cmd)
    ld.add_action(declare_use_gazebo_cmd)
    ld.add_action(declare_use_jsp_cmd)
    ld.add_action(declare_use_rviz_cmd)
    ld.add_action(declare_use_robot_state_pub_cmd)
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_world_cmd)

    # Add pose arguments
    ld.add_action(declare_x_cmd)
    ld.add_action(declare_y_cmd)
    ld.add_action(declare_z_cmd)
    ld.add_action(declare_roll_cmd)
    ld.add_action(declare_pitch_cmd)
    ld.add_action(declare_yaw_cmd)

    # Add the actions to the launch description
    ld.add_action(set_env_vars_resources)
    ld.add_action(warn_jsp_conflict_cmd)
    ld.add_action(warn_no_rsp_cmd)
    ld.add_action(robot_state_publisher_cmd)
    ld.add_action(start_gazebo_cmd)
    ld.add_action(start_gazebo_ros_bridge_cmd)
    ld.add_action(start_gazebo_ros_camera_bridge_cmd)
    ld.add_action(start_gazebo_ros_image_bridge_cmd)
    ld.add_action(start_gazebo_ros_spawner_cmd)
    ld.add_action(load_controllers_after_spawn_cmd)

    return ld
