#!/usr/bin/env python3
"""
Control the Nova robot arm to perform repetitive movements between waypoints and home.

This script creates a ROS 2 node that moves the robot arm through a list of target
joint waypoints and back to the home position in a continuous, non-blocking loop.

Action Clients:
    /arm_controller/follow_joint_trajectory (control_msgs/FollowJointTrajectory):
        Commands for controlling arm joint positions

:author: Mahdi Momeni
:date: November 27, 2026
"""

import signal

import rclpy
from action_msgs.msg import GoalStatus
from builtin_interfaces.msg import Duration
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.signals import SignalHandlerOptions
from trajectory_msgs.msg import JointTrajectoryPoint


class ArmWaypointsLoopController(Node):
    """
    A ROS 2 node for controlling robot arm movements across waypoints in a loop.

    This class creates a non-blocking action-driven control loop that:
    1. Moves the arm through each target waypoint
    2. Pauses briefly after each reached waypoint
    3. Returns the arm to the home position
    4. Pauses briefly before starting the next cycle
    """

    def __init__(self):
        """
        Initialize the node, arm action client, waypoints, and startup timer.
        """
        super().__init__("arm_waypoints_loop_controller")

        self.declare_parameter("robot_name", "nova")
        robot_name = self.get_parameter("robot_name").get_parameter_value().string_value

        # Set up arm trajectory action client for arm movement control
        self.arm_client = ActionClient(
            self, FollowJointTrajectory, "/arm_controller/follow_joint_trajectory"
        )

        # List of joint names for the Nova robot arm
        self.joint_names = [f"{robot_name}_joint{i}" for i in range(1, 7)]

        # Define target waypoints and home position for the arm (radians)
        self.waypoints = [
            [1.345, -1.23, 0.264, -0.296, 0.389, -1.5],
            [0.500, -0.80, 0.400, -0.100, 0.200, -0.5],
            [-0.75, -1.10, 0.300, 0.250, 0.500, 0.0],
        ]
        self.home_pos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        self.targets = [
            (f"waypoint {index}", point)
            for index, point in enumerate(self.waypoints, start=1)
        ] + [("home position", self.home_pos)]
        self.target_index = 0
        self.pause_timer = None
        self.start_timer = None
        self._active_goal_handle = None
        self._shutting_down = False

    def wait_for_action_server(self) -> bool:
        """Wait until the arm trajectory action server is available or shutdown occurs."""
        self.get_logger().info(
            "Waiting for /arm_controller/follow_joint_trajectory action server..."
        )
        while rclpy.ok() and not self.arm_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info("Arm action server not available yet, waiting...")

        if not rclpy.ok():
            return False

        self.get_logger().info("Arm action server connected!")
        return True

    def start(self) -> None:
        """Start the waypoint loop timer once the action server is connected."""
        if self.start_timer is None and not self._shutting_down and rclpy.ok():
            self.start_timer = self.create_timer(0.1, self._start_once)

    def _cancel_timer(self, attr_name: str) -> None:
        """Cancel and destroy a node timer attribute if it exists."""
        timer = getattr(self, attr_name)
        if timer is not None:
            timer.cancel()
            self.destroy_timer(timer)
            setattr(self, attr_name, None)

    def _start_once(self) -> None:
        """Trigger the first target once and destroy the startup timer."""
        self._cancel_timer("start_timer")
        self._send_next_target()

    def send_arm_command(self, positions: list[float]):
        """
        Send a FollowJointTrajectory goal to move the arm to specified joint positions.

        Args:
            positions (list[float]): List of 6 joint angles in radians.

        Returns:
            rclpy.task.Future: Future resolving to the ClientGoalHandle.
        """
        point = JointTrajectoryPoint()
        point.positions = [float(p) for p in positions]
        point.velocities = [0.0] * len(self.joint_names)
        point.time_from_start = Duration(sec=2, nanosec=0)

        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = self.joint_names
        goal_msg.trajectory.points = [point]

        return self.arm_client.send_goal_async(goal_msg)

    def _send_next_target(self) -> None:
        """Send the current target in the waypoint/home cycle."""
        if self._shutting_down or not rclpy.ok():
            return
        label, positions = self.targets[self.target_index]
        self.get_logger().info(f"Moving to {label}: {positions}")
        goal_future = self.send_arm_command(positions)
        goal_future.add_done_callback(self._goal_response_callback)

    def _goal_response_callback(self, future) -> None:
        """Handle goal acceptance or rejection from arm_controller."""
        exc = future.exception()
        if exc is not None:
            self.get_logger().error(f"Failed to send trajectory goal: {exc}")
            self._schedule_next_target(1.0)
            return

        goal_handle = future.result()
        if not goal_handle.accepted:
            label, _ = self.targets[self.target_index]
            self.get_logger().error(f"Goal for {label} was rejected by arm_controller")
            self._schedule_next_target(1.0)
            return

        if self._shutting_down:
            goal_handle.cancel_goal_async()
            return

        self._active_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._get_result_callback)

    def _get_result_callback(self, future) -> None:
        """Handle trajectory execution completion and pause before the next target."""
        self._active_goal_handle = None
        if self._shutting_down:
            return

        exc = future.exception()
        label, _ = self.targets[self.target_index]
        if exc is not None:
            self.get_logger().error(f"Failed to receive result for {label}: {exc}")
            self._schedule_next_target(1.0)
            return

        wrapped_result = future.result()
        if wrapped_result.status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info(f"Reached {label} - Pausing")
        else:
            self.get_logger().warning(
                f"{label} ended with status={wrapped_result.status}, "
                f"error_code={wrapped_result.result.error_code} "
                f"({wrapped_result.result.error_string})"
            )

        self._schedule_next_target(1.0)

    def _schedule_next_target(self, delay_sec: float) -> None:
        """Schedule a one-shot ROS timer before advancing to the next target."""
        self._cancel_timer("pause_timer")
        if not self._shutting_down and rclpy.ok():
            self.pause_timer = self.create_timer(delay_sec, self._on_pause_done)

    def _on_pause_done(self) -> None:
        """Advance to the next waypoint/home target after the pause timer expires."""
        self._cancel_timer("pause_timer")
        self.target_index = (self.target_index + 1) % len(self.targets)
        self._send_next_target()

    def cancel_active_goal(self):
        """Stop scheduling new targets and request cancellation of any active goal."""
        self._shutting_down = True
        self._cancel_timer("start_timer")
        self._cancel_timer("pause_timer")

        if self._active_goal_handle is None or not rclpy.ok():
            return None

        self.get_logger().info("Canceling active trajectory goal...")
        cancel_future = self._active_goal_handle.cancel_goal_async()
        self._active_goal_handle = None
        return cancel_future


def main(args=None):
    """
    Initialize and run the arm waypoints loop control node.

    Args:
        args: Command-line arguments (default: None)
    """
    # Keep Python SIGINT handling so Ctrl+C raises KeyboardInterrupt while rclpy stays active
    # long enough to cancel any in-flight trajectory goal before shutting down.
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)

    def _handle_sigterm(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _handle_sigterm)
    controller = None

    try:
        controller = ArmWaypointsLoopController()
        if controller.wait_for_action_server():
            controller.start()
            if rclpy.ok():
                rclpy.spin(controller)
    except KeyboardInterrupt:
        if controller is not None:
            controller.get_logger().info("Shutting down arm waypoints controller...")
            cancel_future = controller.cancel_active_goal()
            if cancel_future is not None and rclpy.ok():
                rclpy.spin_until_future_complete(
                    controller, cancel_future, timeout_sec=1.0
                )
    finally:
        if controller is not None:
            controller.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
