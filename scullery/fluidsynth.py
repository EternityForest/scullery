
# Copyright Daniel Dunn 2020

# Scullery is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.

# Scullery is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Scullery.  If not, see <http://www.gnu.org/licenses/>.

import time
import weakref
import os
import yaml
import threading
import logging
gmInstruments = None

players = weakref.WeakValueDictionary()

lock = threading.Lock()


def all_notes_off():
    try:
        for i in players:
            players[i].fs.all_notes_off(-1)
    except:
        pass


def stop_all():
    try:
        for i in players:
            players[i].close()
    except:
        pass


def remake_all():
    try:
        for i in players:
            players[i].close()
    except:
        pass


def get_gm_instruments():
    global gmInstruments
    if gmInstruments:
        return gmInstruments
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gm_instruments.yaml')) as f:
        gmInstruments = yaml.load(f.read(), yaml.SafeLoader)
    return gmInstruments


def find_gm_instrument(name, look_in_soundfont=None, bank=None):
    # Allow manually selected instruments
    try:
        return (bank, int(name))
    except:
        pass
    name = name.replace("(", '').replace(')', '')
    # Try to find a matching patch name in the soundfont
    if look_in_soundfont:
        try:
            from sf2utils.sf2parse import Sf2File
            with open(look_in_soundfont, 'rb') as sf2_file:
                sf2 = Sf2File(sf2_file)
            # Names
            x = [i[0].split(b"\0")[0].decode("utf8")
                 for i in sf2.raw.pdta['Phdr']]
        except Exception as e:
            logging.exception("Can't get metadata from this soundfont")
            print("Error looking through soundfont data", e)
            x = []

        # Indexes
        for i in range(len(x)):
            n = x[i].lower()
            n = n.replace("(", '').replace(')', '')
            n = n.split(" ")
            match = True

            for j in name.lower().split(" "):
                if not j in n:
                    # Bank 128 is reserved for drums so it can substitute for drum related words,
                    # It's still a match
                    if not (j in ('kit', 'drums', 'drum') and sf2.raw.pdta['Phdr'][i][2] == 128):
                        match = False
            if match:
                if bank == None:
                    return (sf2.raw.pdta['Phdr'][i][2], sf2.raw.pdta['Phdr'][i][1])
                return (bank, sf2.raw.pdta['Phdr'][i][1])

    x = get_gm_instruments()
    for i in x:
        n = x[i].lower()
        n = n.replace("(", '').replace(')', '')
        n = n.split(" ")
        match = True
        for j in name.lower().split(" "):
            if not j in n:
                match = False
        if match:
            return (bank or 0, i)
    raise ValueError("No matching instrument")


def wait_for_jack():
    from scullery import jacktools
    for i in range(10):
        if not jacktools.get_ports():
            time.sleep(1)
        else:
            return

    raise RuntimeError("It appears that JACK is not running")


def find_sound_font(specific=None, extra_fallback=None):
    # Support the debian, Arch, and EmberOS conventions
    l = ['/usr/share/sounds/sf3/MuseScore_General_Lite.sf3',
         '/var/public.files/emberos/SoundFonts/MuseScore_General.sf3',
         '/usr/share/sounds/sf3/MuseScore_General.sf3',
         "/usr/share/sounds/sf2/FluidR3_GM.sf2",
         '/var/public.files/emberos/SoundFonts/FluidR3_GM.sf3',
         '/usr/share/soundfonts/FluidR3_GM.sf2'
         ]

    if os.path.exists(specific):
        return specific

    for i in l:
        if os.path.exists(l):
            return l

    return extra_fallback


class FluidSynth():
    defaultSoundfont = "/usr/share/sounds/sf2/FluidR3_GM.sf2"

    def __init__(self, soundfont=None, jack_client_name=None, gain=0.2,
                 connect_midi=None, connect_output=None, reverb=False, chorus=False, ondemand=True):
        players[id(self)] = self

        if jack_client_name:
            from . import jacktools
            wait_for_jack()

        self.soundfont = soundfont or self.defaultSoundfont

        if not os.path.isfile(self.soundfont):
            raise OSError("Soundfont: "+soundfont +
                          " does not exist or is not a file")

        from . thirdparty import fluidsynth

        def remake():
            self.fs = fluidsynth.Synth(gain=gain)
            self.fs.setting("synth.chorus.active", 1 if chorus else 0)
            self.fs.setting("synth.reverb.active", 1 if reverb else 0)

            try:
                self.fs.setting("synth.dynamic-sample-loading",
                                1 if ondemand else 0)
            except:
                logging.exception("No dynamic loading support, ignoring")
            self.sfid = self.fs.sfload(self.soundfont)
            usingJack = False

            if jack_client_name:
                self.fs.setting("audio.jack.id", jack_client_name)
                self.fs.setting("midi.jack.id", "fstest")

                usingJack = True

            if connect_midi:
                pass
                # self.midiAirwire = jackmanager.Mono

            if connect_output:
                self.airwire = jacktools.Airwire(
                    jack_client_name or 'KaithemFluidsynth', connect_output)
                self.airwire.connect()

            if usingJack:
                if not jack_client_name:
                    self.fs.setting("audio.jack.id", "fstest")
                    self.fs.setting("midi.jack.id", "fstest")

                self.fs.setting("midi.driver", 'jack')
                self.fs.start(driver="jack", midi_driver="jack")

            else:
                # self.fs.setting("audio.driver", 'alsa')
                self.fs.start()
            for i in range(16):
                self.fs.program_select(i, self.sfid, 0, 0)
        remake()

        # allow restart after JACK settings change
        self.remake = remake

    def setInstrument(self, channel, instrument, bank=None):
        bank, insNumber = find_gm_instrument(instrument, self.soundfont, bank)
        self.fs.program_select(channel, self.sfid, bank, insNumber)

    def noteOn(self, channel, note, velocity):
        self.fs.noteon(channel, note, velocity)

    def noteOff(self, channel, note):
        self.fs.noteoff(channel, note)

    def cc(self, channel, control, val):
        self.fs.cc(channel, control, val)

    def pitchBend(self, channel, val):
        self.fs.pitch_bend(channel, val)

    def programChange(self, channel, val):
        self.fs.program_change(channel, val)

    def __del__(self):
        self.close()

    def close(self):
        with lock:
            try:
                if hasattr(self, 'fs'):
                    self.fs.delete()
                    del self.fs
            except AttributeError:
                pass
