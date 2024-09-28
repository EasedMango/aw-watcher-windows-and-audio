import ctypes
import ctypes.wintypes
import win32api
import win32con
import win32gui
import win32process
import psutil
import os

def rect_intersection(rect_a, rect_b):
    """Return the intersection of two rectangles or None if they don't intersect."""
    left = max(rect_a[0], rect_b[0])
    top = max(rect_a[1], rect_b[1])
    right = min(rect_a[2], rect_b[2])
    bottom = min(rect_a[3], rect_b[3])
    if left < right and top < bottom:
        return (left, top, right, bottom)
    else:
        return None


def rect_union(rect_a, rect_b):
    """Return the union of two rectangles."""
    left = min(rect_a[0], rect_b[0])
    top = min(rect_a[1], rect_b[1])
    right = max(rect_a[2], rect_b[2])
    bottom = max(rect_a[3], rect_b[3])
    return (left, top, right, bottom)


def is_completely_overlapping(rect_a, rect_b):
    """Check if rect_a completely contains rect_b."""
    left_a, top_a, right_a, bottom_a = rect_a
    left_b, top_b, right_b, bottom_b = rect_b
    return (left_a <= left_b and top_a <= top_b and
            right_a >= right_b and bottom_a >= bottom_b)


def sort_by_z(element):
    """Helper function to sort windows by their Z-order."""
    return element['z_order']


def is_application_window(hwnd):
    """
    Determine if hwnd corresponds to a visible application window.
    """
    # Check if window is visible
    if not win32gui.IsWindowVisible(hwnd):
        return False

    # Check if window has no title
    title = win32gui.GetWindowText(hwnd)
    if not title:
        return False

    # Get window styles
    style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
    exstyle = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

    # Skip over tool windows and child windows
    if exstyle & win32con.WS_EX_TOOLWINDOW or style & win32con.WS_CHILD:
        return False

    # Skip over windows that are owned
    if win32gui.GetWindow(hwnd, win32con.GW_OWNER):
        return False

    # Additional check: Use DWM API to check if window is cloaked
    try:
        DWMWA_CLOAKED = 14
        is_cloaked = ctypes.c_int(0)
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            ctypes.wintypes.HWND(hwnd),
            ctypes.wintypes.DWORD(DWMWA_CLOAKED),
            ctypes.byref(is_cloaked),
            ctypes.sizeof(is_cloaked)
        )
        if is_cloaked.value != 0:
            return False
    except Exception:
        pass  # DwmGetWindowAttribute might not be available on older Windows versions

    # Additional check: Exclude windows from certain processes
    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        process_name = process.name().lower()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False



    return True  # It's a top-level unowned window


def get_monitor_sizes():
    """Retrieve information about all monitors."""
    monitors = []
    for monitor in win32api.EnumDisplayMonitors():
        h_monitor, hdc_monitor, (left, top, right, bottom) = monitor
        width = right - left
        height = bottom - top
        monitor_info = win32api.GetMonitorInfo(h_monitor)
        work_area = monitor_info['Work']
        work_left, work_top, work_right, work_bottom = work_area
        work_width = work_right - work_left
        work_height = work_bottom - work_top

        monitors.append({
            'monitor_handle': h_monitor,
            'monitor_rect': (left, top, right, bottom),
            'monitor_position': (left, top),
            'monitor_size': (width, height),
            'work_area_rect': work_area,
            'work_area_position': (work_left, work_top),
            'work_area_size': (work_width, work_height)
        })
    return monitors

def get_process_name(hwnd):
    """Get the process name for a given window handle (hwnd)."""
    try:
        # Get the PID of the process that owns the window
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        # Open the process with query information rights
        process_handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
        # Get the full path to the executable
        exe_name = win32process.GetModuleFileNameEx(process_handle, 0)
        # Close the process handle
        win32api.CloseHandle(process_handle)
        # Return only the executable name (without the full path)
        return os.path.basename(exe_name)
    except Exception:
        return None
    
def get_visible_windows():
    """Get a list of all visible application windows."""
    windows = []

    def enum_window_callback(hwnd, lParam):
        if is_application_window(hwnd):
            title = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            z_order = 0
            prev_hwnd = hwnd

            while True:
                prev_hwnd = win32gui.GetWindow(prev_hwnd, win32con.GW_HWNDPREV)
                if not prev_hwnd:
                    break
                z_order += 1
            #print(get_process_name(hwnd))
            windows.append({
                'handle': hwnd,
                'title': title,
                'app': get_process_name(hwnd),
                'rect': rect,
                'size': (width, height),
                'z_order': z_order,
                'visible': True
            })

    win32gui.EnumWindows(enum_window_callback, None)

    return windows


def get_visible_region(window_rect, monitors):
    """Calculate the visible region of a window within the monitor's work areas."""
    visible_region = None
    for monitor in monitors:
        work_area_rect = monitor['work_area_rect']
        intersection = rect_intersection(window_rect, work_area_rect)
        if intersection:
            if visible_region:
                visible_region = rect_union(visible_region, intersection)
            else:
                visible_region = intersection
    return visible_region


def occluded_windows(windows, monitors):
    """Determine which windows are occluded by others, considering cumulative occlusion."""
    # Precompute the visible regions for all windows
    for window in windows:
        window_rect = window['visible_region'] = get_visible_region(window['rect'], monitors)
        if not window['visible_region']:
            window['visible'] = False  # Entire window is outside work area
        else:
            window['visible'] = True  # Reset visibility status

    # Initialize an empty region for cumulative occlusion
    cumulative_occlusion_region = win32gui.CreateRectRgnIndirect((0, 0, 0, 0))

    for window in windows:
        if not window['visible']:
            continue

        # Create a region for the window's visible region
        left, top, right, bottom = window['visible_region']
        window_region = win32gui.CreateRectRgnIndirect((left, top, right, bottom))

        # Compute the difference between the window region and cumulative occlusion region
        diff_region = win32gui.CreateRectRgnIndirect((0, 0, 0, 0))
        win32gui.CombineRgn(diff_region, window_region, cumulative_occlusion_region, win32con.RGN_DIFF)

        # Get the bounding rectangle of the diff_region
        region_type, diff_rect = win32gui.GetRgnBox(diff_region)

        if region_type == win32con.NULLREGION:
            # diff_region is empty; window is completely occluded
            window['visible'] = False
        else:
            # Window is partially or fully visible
            window['visible_region'] = diff_rect

        if window['visible']:
            # Add the window's region to the cumulative occlusion region
            win32gui.CombineRgn(cumulative_occlusion_region, cumulative_occlusion_region, window_region, win32con.RGN_OR)

        # Clean up
        win32gui.DeleteObject(window_region)
        win32gui.DeleteObject(diff_region)

    # Clean up cumulative occlusion region
    win32gui.DeleteObject(cumulative_occlusion_region)


    
def occluded_remove_windows(windows, monitors):
    """Determine which windows are occluded by others, considering cumulative occlusion."""
    # Precompute the visible regions for all windows
    for window in windows[:]:  # Iterate over a copy of the list
        window_rect = window['visible_region'] = get_visible_region(window['rect'], monitors)
        if not window['visible_region']:
            windows.remove(window)  # Delete the entire window from the list
        else:
            window['visible'] = True  # Reset visibility status

    # Initialize an empty region for cumulative occlusion
    cumulative_occlusion_region = win32gui.CreateRectRgnIndirect((0, 0, 0, 0))

    for window in windows:
        should_remove = False
        # Create a region for the window's visible region
        left, top, right, bottom = window['visible_region']
        window_region = win32gui.CreateRectRgnIndirect((left, top, right, bottom))

        # Compute the difference between the window region and cumulative occlusion region
        diff_region = win32gui.CreateRectRgnIndirect((0, 0, 0, 0))
        win32gui.CombineRgn(diff_region, window_region, cumulative_occlusion_region, win32con.RGN_DIFF)

        # Get the bounding rectangle of the diff_region
        region_type, diff_rect = win32gui.GetRgnBox(diff_region)

        if region_type == win32con.NULLREGION:
            # diff_region is empty; window is completely occluded
            should_remove = True  # Delete the entire window from the list
        else:
            # Window is partially or fully visible
            window['visible_region'] = diff_rect
           # print(window['app'])

        # Add the window's region to the cumulative occlusion region
        win32gui.CombineRgn(cumulative_occlusion_region, cumulative_occlusion_region, window_region, win32con.RGN_OR)

        # Clean up
        win32gui.DeleteObject(window_region)
        win32gui.DeleteObject(diff_region)
        
        if should_remove:
            windows.remove(window)  # Delete the entire window from the list
            

    # Clean up cumulative occlusion region
    win32gui.DeleteObject(cumulative_occlusion_region)


def get_window_data():
    """
    Retrieve and return window data after occlusion calculations.
    Returns a list of window dictionaries with visibility status and visible regions.
    """
    monitors = get_monitor_sizes()
    windows = get_visible_windows()
    windows.sort(key=sort_by_z)
    occluded_windows(windows, monitors)
    return windows, monitors

def get_window_data():
    """
    Retrieve and return window data after occlusion calculations.
    Returns a list of window dictionaries with visibility status and visible regions.
    """
    monitors = get_monitor_sizes()
    windows = get_visible_windows()
    windows.sort(key=sort_by_z)
    occluded_windows(windows, monitors)
    return windows

def get_visible_windows_data():
    monitors = get_monitor_sizes()
    windows = get_visible_windows()
    windows.sort(key=sort_by_z)
    occluded_remove_windows(windows, monitors)
    return windows
