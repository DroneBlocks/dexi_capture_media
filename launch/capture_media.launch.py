from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

ARGS = [
    ('image_topic', '/cam0/image_raw/compressed', 'Compressed camera topic to capture from'),
    ('media_dir', '/home/dexi/dexi_media', 'Where photos and videos are saved'),
    ('http_port', '8090', 'Port for listing, downloading and deleting media'),
    ('photo_aux_index', '0', 'RC aux channel (1-6) that takes a photo; 0 = off'),
    ('video_aux_index', '0', 'RC aux channel (1-6) that records while high; 0 = off'),
    ('aux_threshold', '0.5', 'Aux value above which a switch counts as high'),
    ('record_hold_s', '3.0', 'Hold the photo button this long to start/stop recording; 0 = off'),
    ('max_video_s', '600.0', 'Stop a recording after this many seconds; 0 = no limit'),
    ('video_fps', '15.0', 'Frame rate of recorded video (DEXI camera runs ~15 fps)'),
    ('min_free_mb', '200', 'Refuse to capture below this much free disk (MB)'),
]


def generate_launch_description():
    ld = LaunchDescription([DeclareLaunchArgument(n, default_value=d, description=h) for n, d, h in ARGS])
    ld.add_action(Node(
        package='dexi_capture_media',
        executable='capture_media_node',
        name='capture_media',
        namespace='dexi',
        output='screen',
        parameters=[{n: LaunchConfiguration(n) for n, _, _ in ARGS}],
    ))
    return ld
