from time import sleep
from datetime import datetime, timezone
from aw_core.models import Event
from aw_client import ActivityWatchClient
import AudioInfo
import WatcherUtils
config = WatcherUtils.get_config('aw-watcher-audio-sources.toml')['settings']
client = ActivityWatchClient("test-client",testing=config['testing'])
bucket_id = "{}_{}".format("aw-watcher-audible-sources", client.client_hostname)
event_type = "audible-sources"
client.create_bucket(bucket_id, event_type="audible-sources")
with client:
    sleeptime = config['sleep-time']
    pulsetime = config['pulse-time']
    while True:
        sources = AudioInfo.get_audible_audio_sources()
        now = datetime.now(timezone.utc)
        data = {'sources': [source['name'] for source in sources]}
        heartbeat_event = Event(timestamp=now,data=data)
        client.heartbeat(bucket_id, heartbeat_event,pulsetime=pulsetime,queued=True,commit_interval=4.0)
        sleep(sleeptime)
        
        