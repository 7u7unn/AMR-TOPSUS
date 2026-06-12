from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import hashlib
import os
import re
from pathlib import Path


def _keepout_selection_state_file() -> Path:
    return Path.home() / '.arya_amr' / 'selected_keepout_mask.txt'


def _resolve_keepout_candidate(raw_value: str, maps_dir: str) -> str:
    candidate = os.path.expanduser(str(raw_value or '').strip())
    if not candidate:
        return ''
    if not os.path.isabs(candidate):
        candidate = os.path.join(maps_dir, candidate)
    return candidate if _keepout_yaml_has_image(candidate) else ''


def _read_simple_yaml_value(yaml_path: str, key: str) -> str:
    pattern = re.compile(rf'^\s*{re.escape(key)}\s*:\s*(.*?)\s*(?:#.*)?$')
    try:
        with open(yaml_path, 'r', encoding='utf-8') as stream:
            for line in stream:
                match = pattern.match(line)
                if match:
                    return match.group(1).strip().strip('"').strip("'")
    except OSError:
        return ''
    return ''


def _resolve_yaml_image(yaml_path: str) -> str:
    image = _read_simple_yaml_value(yaml_path, 'image')
    if not image:
        return ''
    image = os.path.expanduser(image)
    if not os.path.isabs(image):
        image = os.path.join(os.path.dirname(yaml_path), image)
    return image


def _keepout_yaml_has_image(yaml_path: str) -> bool:
    if not os.path.exists(yaml_path):
        return False
    image_path = _resolve_yaml_image(yaml_path)
    return bool(image_path and os.path.exists(image_path))


def _read_pgm_size(image_path: str) -> tuple[int, int] | None:
    try:
        with open(image_path, 'rb') as stream:
            data = stream.read(4096)
    except OSError:
        return None

    tokens: list[bytes] = []
    index = 0
    while index < len(data) and len(tokens) < 4:
        while index < len(data) and data[index:index + 1].isspace():
            index += 1
        if index < len(data) and data[index:index + 1] == b'#':
            while index < len(data) and data[index:index + 1] not in (b'\n', b'\r'):
                index += 1
            continue
        start = index
        while index < len(data) and not data[index:index + 1].isspace():
            index += 1
        if start != index:
            tokens.append(data[start:index])

    if len(tokens) < 4 or tokens[0] not in (b'P2', b'P5'):
        return None

    try:
        return int(tokens[1]), int(tokens[2])
    except ValueError:
        return None


def _read_origin_xy(origin: str) -> tuple[str, str]:
    match = re.search(r'\[([^\]]+)\]', origin or '')
    if not match:
        return '0.0', '0.0'
    parts = [part.strip() for part in match.group(1).split(',')]
    if len(parts) < 2:
        return '0.0', '0.0'
    return parts[0] or '0.0', parts[1] or '0.0'


def _write_empty_keepout_for_map(map_yaml: str) -> str:
    if not os.path.exists(map_yaml):
        return ''

    image_path = _resolve_yaml_image(map_yaml)
    size = _read_pgm_size(image_path) if image_path else None
    if not size:
        return ''

    resolution = _read_simple_yaml_value(map_yaml, 'resolution') or '0.05'
    origin_x, origin_y = _read_origin_xy(_read_simple_yaml_value(map_yaml, 'origin'))
    map_key = hashlib.sha1(os.path.abspath(map_yaml).encode('utf-8')).hexdigest()[:10]
    output_dir = Path.home() / '.arya_amr' / 'generated_keepout_masks'
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        pgm_path = output_dir / f'{Path(map_yaml).stem}_{map_key}_keepout.pgm'
        yaml_path = output_dir / f'{Path(map_yaml).stem}_{map_key}_keepout.yaml'
        width, height = size
        with pgm_path.open('wb') as stream:
            stream.write(f'P5\n{width} {height}\n255\n'.encode('ascii'))
            stream.write(bytes([255]) * (width * height))
        yaml_path.write_text(
            '\n'.join([
                f'image: {pgm_path.name}',
                'mode: trinary',
                f'resolution: {resolution}',
                f'origin: [{origin_x}, {origin_y}, 0]',
                'negate: 0',
                'occupied_thresh: 0.65',
                'free_thresh: 0.25',
                '',
            ]),
            encoding='utf-8'
        )
    except OSError:
        return ''

    return str(yaml_path)


def _resolve_default_keepout_mask(bringup_share: str) -> str:
    maps_dir = os.path.join(bringup_share, 'maps')
    env_mask = os.environ.get('AMR_KEEPOUT_MASK', '').strip()
    if env_mask:
        resolved_env_mask = _resolve_keepout_candidate(env_mask, maps_dir)
        if resolved_env_mask:
            return resolved_env_mask

    selected_map_file = Path.home() / '.arya_amr' / 'selected_localization_map.txt'
    try:
        selected_map = selected_map_file.read_text(encoding='utf-8').strip()
    except OSError:
        selected_map = ''
    if selected_map:
        map_candidate = os.path.expanduser(selected_map)
        if not os.path.isabs(map_candidate):
            map_candidate = os.path.join(maps_dir, os.path.basename(map_candidate))
        keepout_candidate = os.path.join(
            os.path.dirname(map_candidate),
            f'{Path(map_candidate).stem}_keepout.yaml'
        )
        if _keepout_yaml_has_image(keepout_candidate):
            return keepout_candidate
        generated_keepout = _write_empty_keepout_for_map(map_candidate)
        if generated_keepout:
            return generated_keepout

    selection_file = _keepout_selection_state_file()
    try:
        selected_mask = selection_file.read_text(encoding='utf-8').strip()
    except OSError:
        selected_mask = ''
    if selected_mask:
        resolved_selected_mask = _resolve_keepout_candidate(selected_mask, maps_dir)
        if resolved_selected_mask:
            return resolved_selected_mask

    return ''


def generate_launch_description():
    params_file = LaunchConfiguration('params_file')
    enable_collision_monitor = LaunchConfiguration('enable_collision_monitor')
    enable_keepout_zones = LaunchConfiguration('enable_keepout_zones')
    keepout_mask = LaunchConfiguration('keepout_mask')
    default_nav_to_pose_bt_xml = LaunchConfiguration('default_nav_to_pose_bt_xml')
    default_nav_through_poses_bt_xml = LaunchConfiguration('default_nav_through_poses_bt_xml')
    bringup_share = get_package_share_directory('amr_bringup_headless')
    default_params_file = os.path.join(
        bringup_share,
        'config',
        'nav2_params.yaml'
    )
    default_nav_to_pose_bt_file = os.path.join(
        bringup_share,
        'behavior_trees',
        'navigate_to_pose_no_spin.xml'
    )
    default_nav_through_poses_bt_file = os.path.join(
        bringup_share,
        'behavior_trees',
        'navigate_through_poses_no_spin.xml'
    )
    default_keepout_mask = _resolve_default_keepout_mask(bringup_share)
    default_enable_keepout_zones = 'true' if default_keepout_mask else 'false'

    return LaunchDescription([
        DeclareLaunchArgument(
            'params_file',
            default_value=default_params_file,
            description='Full path to the Nav2 parameters file'
        ),
        DeclareLaunchArgument(
            'cmd_vel_raw_topic',
            default_value='cmd_vel_raw_nav2',
            description='Velocity output topic from Nav2 velocity smoother (normally cmd_vel_raw).'
        ),
        DeclareLaunchArgument(
            'enable_collision_monitor',
            default_value='true',
            description='Route Nav2 velocity commands through Collision Monitor safety gate.'
        ),
        DeclareLaunchArgument(
            'enable_keepout_zones',
            default_value=default_enable_keepout_zones,
            description='Enable Nav2 keepout filter mask servers. Defaults to true only when a usable mask is found.'
        ),
        DeclareLaunchArgument(
            'keepout_mask',
            default_value=default_keepout_mask,
            description='Full path to keepout mask YAML file.'
        ),
        DeclareLaunchArgument(
            'default_nav_to_pose_bt_xml',
            default_value=default_nav_to_pose_bt_file,
            description='Behavior tree XML for NavigateToPose. Default disables Spin recovery.'
        ),
        DeclareLaunchArgument(
            'default_nav_through_poses_bt_xml',
            default_value=default_nav_through_poses_bt_file,
            description='Behavior tree XML for NavigateThroughPoses. Default disables Spin recovery.'
        ),

        LogInfo(msg=['Nav2 keepout mask: ', keepout_mask]),

        Node(
            package='nav2_controller',
            executable='controller_server',
            name='controller_server',
            output='screen',
            parameters=[params_file],
            remappings=[('cmd_vel', 'cmd_vel_nav')]
        ),

        Node(
            package='nav2_planner',
            executable='planner_server',
            name='planner_server',
            output='screen',
            parameters=[params_file]
        ),

        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            name='behavior_server',
            output='screen',
            parameters=[params_file],
            remappings=[('cmd_vel', 'cmd_vel_nav')]
        ),

        Node(
            package='nav2_velocity_smoother',
            executable='velocity_smoother',
            name='velocity_smoother',
            output='screen',
            parameters=[params_file],
            remappings=[('cmd_vel', 'cmd_vel_nav'), ('cmd_vel_smoothed', 'cmd_vel_auto')],
            condition=UnlessCondition(enable_collision_monitor)
        ),

        Node(
            package='nav2_velocity_smoother',
            executable='velocity_smoother',
            name='velocity_smoother',
            output='screen',
            parameters=[params_file],
            remappings=[('cmd_vel', 'cmd_vel_nav'), ('cmd_vel_smoothed', LaunchConfiguration('cmd_vel_raw_topic'))],
            condition=IfCondition(enable_collision_monitor)
        ),

        Node(
            package='nav2_collision_monitor',
            executable='collision_monitor',
            name='collision_monitor',
            output='screen',
            parameters=[params_file],
            condition=IfCondition(enable_collision_monitor)
        ),

        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            name='bt_navigator',
            output='screen',
            parameters=[
                params_file,
                {
                    'default_nav_to_pose_bt_xml': ParameterValue(default_nav_to_pose_bt_xml, value_type=str),
                    'default_nav_through_poses_bt_xml': ParameterValue(default_nav_through_poses_bt_xml, value_type=str),
                },
            ]
        ),

        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            name='waypoint_follower',
            output='screen',
            parameters=[params_file]
        ),

        Node(
            package='nav2_map_server',
            executable='map_server',
            name='keepout_filter_mask_server',
            output='screen',
            parameters=[
                params_file,
                {'yaml_filename': ParameterValue(keepout_mask, value_type=str)}
            ],
            condition=IfCondition(enable_keepout_zones)
        ),

        Node(
            package='nav2_map_server',
            executable='costmap_filter_info_server',
            name='keepout_costmap_filter_info_server',
            output='screen',
            parameters=[params_file],
            condition=IfCondition(enable_keepout_zones)
        ),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            output='screen',
            parameters=[params_file]
        ),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_keepout_zone',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'autostart': True,
                'node_names': [
                    'keepout_filter_mask_server',
                    'keepout_costmap_filter_info_server',
                ],
            }],
            condition=IfCondition(enable_keepout_zones)
        ),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_collision_monitor',
            output='screen',
            parameters=[{
                'use_sim_time': False,
                'autostart': True,
                'node_names': ['collision_monitor'],
            }],
            condition=IfCondition(enable_collision_monitor)
        ),
    ])
