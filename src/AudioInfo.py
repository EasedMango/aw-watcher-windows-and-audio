from pycaw.pycaw import AudioUtilities
from pycaw.pycaw import IAudioMeterInformation
def get_audible_audio_sources():
    sessions = AudioUtilities.GetAllSessions()
    audible_sources = []
    for session in sessions:
        if session.Process:
            volume = session._ctl.QueryInterface(IAudioMeterInformation)
            peak_volume = volume.GetPeakValue()
            if peak_volume > 0.001:
                audible_sources.append({
                    'pid': session.Process.pid,
                    'name': session.Process.name()
                    
                })
    return audible_sources