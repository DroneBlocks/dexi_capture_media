import os
from datetime import datetime
from types import SimpleNamespace

from dexi_capture_media import media_files as mf
from dexi_capture_media.rc_switch import AuxSwitch

NOW = datetime(2026, 11, 20, 14, 3, 7, 42000)


def test_names():
    assert mf.photo_name('jpeg', NOW) == 'photo_20261120_140307_042.jpg'
    assert mf.photo_name('rgb8; png compressed', NOW).endswith('.png')
    assert mf.video_name(NOW) == 'video_20261120_140307_042.mp4'
    assert mf.is_valid_name(mf.photo_name('jpeg')) and mf.is_valid_name(mf.video_name())


def test_rejects_other_files():
    for bad in ['', '../photo_1.jpg', 'photo_1.jpg/x', 'video_1.mp4.part', 'notes.txt', 'photo_a.jpg', '.bashrc']:
        assert not mf.is_valid_name(bad), bad


def test_list_media(tmp_path):
    for name, t in [('photo_1.jpg', 100), ('video_2.mp4', 300), ('video_3.mp4.part', 400), ('x.txt', 500)]:
        p = tmp_path / name
        p.write_bytes(b'abc')
        os.utime(p, (t, t))
    files = mf.list_media(str(tmp_path))
    assert [f['name'] for f in files] == ['video_2.mp4', 'photo_1.jpg']
    assert files[0]['type'] == 'video' and files[1]['size'] == 3
    assert mf.list_media(str(tmp_path / 'missing')) == []


def test_parse_range():
    assert mf.parse_range(None, 100) is None
    assert mf.parse_range('bytes=0-9', 100) == (0, 9)
    assert mf.parse_range('bytes=90-', 100) == (90, 99)
    assert mf.parse_range('bytes=-10', 100) == (90, 99)
    assert mf.parse_range('bytes=50-500', 100) == (50, 99)
    assert mf.parse_range('bytes=100-', 100) == 'unsatisfiable'
    assert mf.parse_range('bytes=0-1,5-6', 100) is None


def _rc(**aux):
    return SimpleNamespace(**{f'aux{i}': aux.get(f'aux{i}', 0.0) for i in range(1, 7)})


def test_aux_switch_edges():
    sw = AuxSwitch(3)
    assert sw.update(_rc(aux3=1.0)) is None      # first sample is never an edge
    assert sw.update(_rc(aux3=1.0)) is None
    assert sw.update(_rc(aux3=-1.0)) == 'falling'
    assert sw.update(_rc(aux3=0.9)) == 'rising'
    assert sw.update(_rc(aux3=0.9, aux1=1.0)) is None


def test_aux_switch_off():
    assert not AuxSwitch(0).enabled
    assert AuxSwitch(0).update(_rc(aux1=1.0)) is None
    assert not AuxSwitch(7).enabled


def test_hold_button_tap_and_hold():
    from dexi_capture_media.rc_switch import HoldButton
    b = HoldButton(1, hold_s=3.0)
    up, down = _rc(aux1=-1.0), _rc(aux1=1.0)
    assert b.update(up, 0.0) is None          # first sample
    assert b.update(down, 1.0) is None        # pressed
    assert b.update(up, 1.2) == 'tap'         # released quickly
    assert b.update(down, 2.0) is None        # pressed again
    assert b.update(down, 4.9) is None        # 2.9 s: not yet
    assert b.update(down, 5.0) == 'hold'      # 3 s: hold fires once
    assert b.update(down, 7.0) is None        # still held: nothing more
    assert b.update(up, 7.5) is None          # release after hold: no photo


def test_hold_button_held_at_boot_and_disabled_hold():
    from dexi_capture_media.rc_switch import HoldButton
    b = HoldButton(1, hold_s=3.0)
    assert b.update(_rc(aux1=1.0), 0.0) is None    # already down at boot
    assert b.update(_rc(aux1=1.0), 10.0) is None   # never a hold from boot state
    assert b.update(_rc(aux1=-1.0), 11.0) is None  # release: not a tap either
    t = HoldButton(1, hold_s=0)
    assert t.update(_rc(aux1=-1.0), 0.0) is None
    assert t.update(_rc(aux1=1.0), 0.1) == 'tap'   # hold off: photo on press
    assert not HoldButton(0).enabled
