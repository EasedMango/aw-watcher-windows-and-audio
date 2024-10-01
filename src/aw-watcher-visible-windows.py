from time import sleep
from datetime import datetime, timezone
from aw_core.models import Event
from aw_client import ActivityWatchClient
import WindowInfo, WatcherUtils

config = WatcherUtils.get_config('aw-watcher-visible-windows')['settings']
client = ActivityWatchClient("test-client",testing = config['testing'])
bucket_id = "{}_{}".format("aw-watcher-visible-windows", client.client_hostname)
event_type = "visible-windows"
client.create_bucket(bucket_id, event_type="visible-windows")
with client:
    sleeptime = config['sleep-time']
    pulsetime = config['pulse-time']
    commitinterval = config['commit-interval']
    while True:
        windows =WindowInfo.get_visible_windows_data()
        visible_windows = [{'app': window['app'], 'title': window['title']}
                            for window in windows if window['visible']]
        now = datetime.now(timezone.utc)
        data = {'windows': visible_windows}
        heartbeat_event = Event(timestamp=now,data=data)
        client.heartbeat(bucket_id, heartbeat_event,pulsetime,True,commitinterval)
        sleep(sleeptime)