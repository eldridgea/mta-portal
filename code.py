import board
import digitalio
import time

import time
import microcontroller
from board import NEOPIXEL
import displayio
import adafruit_display_text.label
from adafruit_datetime import datetime
from adafruit_bitmap_font import bitmap_font
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.network import Network


global TOP_STOP_ID
global BOTTOM_STOP_ID
global MINIMUM_MINUTES_DISPLAY
global UPDATE_DELAY
global TOP_DATA_SOURCE
global BOTTOM_DATA_SOURCE
global DATA_LOCATION
global ROUTE
global DATA_LOCATION
DATA_LOCATION = ["data"]
SYNC_TIME_DELAY = 30
BACKGROUND_IMAGE = 'g-dashboard.bmp'
ERROR_RESET_THRESHOLD = 10 #54
TOP_STOP_ID = "229"
BOTTOM_STOP_ID = "R25"
MINIMUM_MINUTES_DISPLAY = 1
UPDATE_DELAY = 30
TOP_TEXT = "BKLYN"
BOTTOM_TEXT = "BKLYN"

def get_arrival_in_minutes_from_now(now, date_str):
    train_date = datetime.fromisoformat(date_str).replace(tzinfo=None) # Remove tzinfo to be able to diff dates
    return round((train_date-now).total_seconds()/60.0)

def get_arrival_times():
    top_stop_trains =  network.fetch_data(TOP_DATA_SOURCE, json_path=(DATA_LOCATION,))
    bottom_stop_trains =  network.fetch_data(BOTTOM_DATA_SOURCE, json_path=(DATA_LOCATION,))
    top_stop_data = top_stop_trains[0]
    bottom_stop_data = bottom_stop_trains[0]
    top_trains = []
    bottom_trains = []
    for item in top_stop_data['S']:
        if item["route"] is "A":
            top_trains.append(item["time"])
    else:
        pass
    for item in bottom_stop_data['S']:
        if item["route"] is "R":
            bottom_trains.append(item["time"])
        else:
            pass

    now = datetime.now()
    print("Now: ", now)

    nortbound_arrivals = [get_arrival_in_minutes_from_now(now, x) for x in top_trains]
    southound_arrivals = [get_arrival_in_minutes_from_now(now, x) for x in bottom_trains]

    n = [str(x) for x in nortbound_arrivals if x>= int(MINIMUM_MINUTES_DISPLAY)]
    s = [str(x) for x in southound_arrivals if x>= int(MINIMUM_MINUTES_DISPLAY)]

    n0 = n[0] if len(n) > 0 else '-'
    n1 = n[1] if len(n) > 1 else '-'
    s0 = s[0] if len(s) > 0 else '-'
    s1 = s[1] if len(s) > 1 else '-'

    return n0,n1,s0,s1

def update_text(n0, n1, s0, s1):
    text_lines[2].text = "%s,%s m" % (n0,n1)
    text_lines[4].text = "%s,%s m" % (s0,s1)
    display.show(group)


# --- Display setup ---
matrix = Matrix()
display = matrix.display
network = Network(status_neopixel=NEOPIXEL, debug=False)


# --- Drawing setup ---
group = displayio.Group()
bitmap = displayio.OnDiskBitmap(open(BACKGROUND_IMAGE, 'rb'))
colors = [0x444444, 0xDD8000]  # [dim white, gold]

font = bitmap_font.load_font("fonts/6x10.bdf")
text_lines = [
displayio.TileGrid(bitmap, pixel_shader=getattr(bitmap, 'pixel_shader', displayio.ColorConverter())),
adafruit_display_text.label.Label(font, color=colors[0], x=20, y=3, text="NORTH"),
adafruit_display_text.label.Label(font, color=colors[1], x=20, y=11, text="- mins"),
adafruit_display_text.label.Label(font, color=colors[0], x=20, y=20, text="SOUTH"),
adafruit_display_text.label.Label(font, color=colors[1], x=20, y=28, text="- mins"),
]
for x in text_lines:
    group.append(x)
    display.show(group)

error_counter = 0
last_time_sync = None
while True:
    global TOP_STOP_ID
    global BOTTOM_STOP_ID
    global MINIMUM_MINUTES_DISPLAY
    global UPDATE_DELAY
    global TOP_DATA_SOURCE
    global BOTTOM_DATA_SOURCE
    global DATA_LOCATION
    global ROUTE
    try:
        # --- Get Variable from cloud ---
        try:
            cloud_vars = network.fetch_data("https://opensheet.elk.sh/1lEuu3-H8-mjQD3VgmoVNRJRceIwylFNRlmGvpuMqhnE/Sheet1", json_path=())
            cloud_vars = cloud_vars[0]
            ROUTE = str(cloud_vars['ROUTE'])
            TOP_STOP_ID = cloud_vars['TOP_STOP_ID']
            BOTTOM_STOP_ID = cloud_vars['BOTTOM_STOP_ID']
            MINIMUM_MINUTES_DISPLAY = cloud_vars['MINIMUM_MINUTES_DISPLAY']
            UPDATE_DELAY = int(cloud_vars['UPDATE_DELAY'])
            TOP_TEXT = str(cloud_vars['TOP_TEXT'])
            BOTTOM_TEXT = str(cloud_vars['BOTTOM_TEXT'])
            TOP_DATA_SOURCE = 'https://api.wheresthefuckingtrain.com/by-id/%s' % (TOP_STOP_ID,)
            BOTTOM_DATA_SOURCE = 'https://api.wheresthefuckingtrain.com/by-id/%s' % (BOTTOM_STOP_ID,)
            DATA_LOCATION = ["data"]
            text_lines[1].text = TOP_TEXT
            text_lines[3].text = BOTTOM_TEXT
            display.show(group)
        except:
            DATA_LOCATION = ["data"]
            SYNC_TIME_DELAY = 30
            BACKGROUND_IMAGE = 'g-dashboard.bmp'
            TOP_STOP_ID = "229"
            BOTTOM_STOP_ID = "R25"
            MINIMUM_MINUTES_DISPLAY = 1
            UPDATE_DELAY = 30
            TOP_TEXT = "BKLYN"
            BOTTOM_TEXT = "BKLYN"
            text_lines[1].text = TOP_TEXT
            text_lines[3].text = BOTTOM_TEXT
            display.show(group)
        if last_time_sync is None or time.monotonic() > last_time_sync + SYNC_TIME_DELAY:
            # Sync clock to minimize time drift
            network.get_local_time()
            last_time_sync = time.monotonic()
        arrivals = get_arrival_times()
        update_text(*arrivals)
    except (ValueError, RuntimeError) as e:
        print("Some error occured, retrying! -", e)
        if error_counter > ERROR_RESET_THRESHOLD:
            microcontroller.reset()

    time.sleep(UPDATE_DELAY)
