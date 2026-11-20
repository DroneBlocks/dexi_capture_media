# dexi_capture_media

Capture photos and record video on DEXI, from the web GCS or a RadioMaster switch, and keep them on the Pi. Solves [DroneBlocks/dexi-os#102](https://github.com/DroneBlocks/dexi-os/issues/102).

One node, `capture_media_node`, runs as `/dexi/capture_media`. It records from the camera topic that bringup already publishes (`/cam0/image_raw/compressed`), so it works with every DEXI camera without touching the camera node.

- **Photos** are the camera's own JPEG frames saved as received, at the stream resolution (640x480 by default).
- **Videos** are H.264 MP4 files encoded by `ffmpeg`, so they play in any browser.
- Files go to `/home/dexi/dexi_media` as `photo_<timestamp>.jpg` and `video_<timestamp>.mp4`.

## ROS interface

| Name | Type | |
|---|---|---|
| `/dexi/capture_media/capture_photo` | `std_srvs/srv/Trigger` | Save the next camera frame. `message` is the file name. |
| `/dexi/capture_media/start_recording` | `std_srvs/srv/Trigger` | Start a recording. |
| `/dexi/capture_media/stop_recording` | `std_srvs/srv/Trigger` | Stop it. |
| `/dexi/capture_media/status` | `std_msgs/msg/String` | JSON at 1 Hz and on every change (see below). |
| `/dexi/capture_media/recording` | `std_msgs/msg/Bool` | Latched; true while recording. `dexi_led` blinks the LED ring red while it is true. |

```bash
ros2 service call /dexi/capture_media/capture_photo std_srvs/srv/Trigger
ros2 service call /dexi/capture_media/start_recording std_srvs/srv/Trigger
ros2 service call /dexi/capture_media/stop_recording std_srvs/srv/Trigger
ros2 topic echo /dexi/capture_media/status
```

Status:

```json
{"recording": true, "file": "video_20261120_140307_042.mp4", "elapsed_s": 12.0,
 "photos": 4, "videos": 2, "free_mb": 18234, "http_port": 8090,
 "last_event": "video_20261120_140307_042.mp4"}
```

## HTTP (browse, download, delete)

Media files are too large for rosbridge, so the node serves them itself on port 8090, the same way mavlink2rest serves on 8088. CORS is open so the GCS on port 80 can call it.

| Request | |
|---|---|
| `GET /media` | `{"files": [{"name", "type", "size", "mtime"}], "free_mb"}`, newest first |
| `GET /media/<name>` | The file. Supports `Range`, so videos can be seeked. Add `?download=1` to save it. |
| `DELETE /media/<name>` | Delete the file. |

Only files this node created are listed, served or deleted.

## RC switch (RadioMaster)

1. Pick a spare channel. First check which channels PX4 already uses: `RC_MAP_ARM_SW`, `RC_MAP_FLTMODE`, `RC_MAP_KILL_SW`, `RC_MAP_OFFB_SW`, `RC_MAP_RETURN_SW`. They differ between airframes; a DEXI 5 uses 5 (arm), 6 (flight mode) and 7 (kill), while the flight kit baseline has its kill switch on 8. Never reuse the kill switch channel.
2. On the transmitter, assign a button or switch to that channel. On a DEXI 5 the photo button is CH8 (for example the SE button).
3. In PX4, map the channel to an aux slot: `RC_MAP_AUX1 = 8`. Check the value moves in QGroundControl under Radio.
4. In `~/.dexi-config.yaml`, set the aux slot number:

```yaml
nodes:
  capture_media:
    photo_aux_index: 1   # momentary button: tap for a photo, hold 3 s to start/stop recording
    video_aux_index: 2   # 2-position switch: records while high
```

5. `sudo systemctl restart dexi.service`

With one button: a **tap** takes a photo (on release), and **holding it for 3 s** starts a recording, or stops the one running. While recording, the LED ring blinks red. `record_hold_s` sets the hold time; `0` turns holding off and takes the photo on the press itself. A separate 2-position switch on `video_aux_index` still works too.

This is the same `/fmu/out/manual_control_setpoint` aux mapping that `tag_nav` uses for its engage switch (`engage_aux_index`), so give each feature its own aux slot; one slot set in both would trigger both. A switch that is already high at boot does not start a recording; it has to be flipped.

## Parameters

| Parameter | Default | |
|---|---|---|
| `image_topic` | `/cam0/image_raw/compressed` | Compressed camera topic |
| `media_dir` | `/home/dexi/dexi_media` | Where files are saved |
| `http_port` | `8090` | HTTP port |
| `photo_aux_index` | `0` | RC aux channel for photos (1-6), 0 = off |
| `video_aux_index` | `0` | RC aux channel for video (1-6), 0 = off |
| `aux_threshold` | `0.5` | Aux value that counts as high |
| `record_hold_s` | `3.0` | Hold the photo button this long to start/stop recording; 0 = off |
| `max_video_s` | `600` | Stop a recording after this long, 0 = no limit |
| `video_fps` | `15` | Frame rate of recorded video; the newest camera frame is written at this rate, so the length always matches real time |
| `min_free_mb` | `200` | Refuse to capture, and stop recording, below this free space |

## Running it

On DEXI it is started by `dexi_bringup` when `nodes.capture_media.enabled` is true (the default). To run it on its own:

```bash
ros2 launch dexi_capture_media capture_media.launch.py
```

Requires `ffmpeg` (`sudo apt install ffmpeg`) for video. Photos work without it.

## Tests

```bash
colcon build --packages-select dexi_capture_media
colcon test --packages-select dexi_capture_media && colcon test-result --verbose
```
