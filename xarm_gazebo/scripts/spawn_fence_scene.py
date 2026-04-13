#!/usr/bin/env python3
"""
Publishes the safety fence as MoveIt collision objects so the planner
avoids it. Dimensions must match xarm_gazebo/worlds/table.world exactly.
"""

import rclpy
from rclpy.node import Node
from moveit_msgs.msg import CollisionObject, PlanningScene
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import Pose


# Coordinates are in MoveIt's 'world' frame (= URDF root link).
# The robot URDF 'world' link is spawned at Gazebo position (-0.2, -0.5, 1.021),
# so: MoveIt = Gazebo - spawn_pos  =>  x+0.2, y+0.5, z-1.021
FENCE_PANELS = [
    {
        'id': 'fence_back',
        'size': [0.85, 0.05, 1.5],
        'pose': [0.0, -0.44, -0.271],   # Gazebo: (-0.2, -0.94, 0.75)
    },
    {
        'id': 'fence_left',
        'size': [0.05, 0.44, 1.5],
        'pose': [-0.40, -0.22, -0.271], # Gazebo: (-0.60, -0.72, 0.75)
    },
    {
        'id': 'fence_right',
        'size': [0.05, 0.44, 1.5],
        'pose': [0.40, -0.22, -0.271],  # Gazebo: (0.20, -0.72, 0.75)
    },
]


class FenceScenePublisher(Node):
    def __init__(self):
        super().__init__('fence_scene_publisher')
        self._pub = self.create_publisher(PlanningScene, '/planning_scene', 10)
        # Give move_group time to start before publishing
        self._timer = self.create_timer(5.0, self._publish_once)

    def _publish_once(self):
        self._timer.cancel()

        scene = PlanningScene()
        scene.is_diff = True

        for panel in FENCE_PANELS:
            obj = CollisionObject()
            obj.header.frame_id = 'world'
            obj.id = panel['id']
            obj.operation = CollisionObject.ADD

            box = SolidPrimitive()
            box.type = SolidPrimitive.BOX
            box.dimensions = panel['size']

            pose = Pose()
            pose.position.x = panel['pose'][0]
            pose.position.y = panel['pose'][1]
            pose.position.z = panel['pose'][2]
            pose.orientation.w = 1.0

            obj.primitives.append(box)
            obj.primitive_poses.append(pose)
            scene.world.collision_objects.append(obj)

        self._pub.publish(scene)
        self.get_logger().info('Fence collision objects added to MoveIt planning scene.')
        raise SystemExit


def main():
    rclpy.init()
    node = FenceScenePublisher()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
