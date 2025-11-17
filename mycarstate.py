# publishes carstate and takes input from car control
import time
import zmq
import capnp
import can
import cantools

class CarStateListener(can.Listener):
    def __init__(self, db, state_dict):
        self.db = db
        self.state = state_dict

    def on_message_received(self, msg):
        try:
            decoded = self.db.decode_message(msg.arbitration_id, msg.data)
            self.state.update(decoded)
        except Exception:
            pass

example_capnp = capnp.load('experiments/messaging/example.capnp')
ctx = zmq.Context()
pub = ctx.socket(zmq.PUB)
pub.bind("tcp://*:5556")

# Load DBC
db = cantools.database.load_file("assets/samples/hyundai_elantra_2006.dbc")

# Setup CAN bus
bus = can.interface.Bus(
    channel='virtual',
    interface='virtual',
    can_filters=[{"can_id": 0x440, "can_mask": 0x7FF}]
)
period = 1/20
start = time.perf_counter()

latest_state = {}   # start empty
listener = CarStateListener(db, latest_state)

notifier = can.Notifier(bus, [listener])

while True:
    # Build outgoing message
    msg = example_capnp.Event.new_message()
    car_state = msg.init("carState")

    car_state.vEgo = latest_state.get("speed", 0.0)
    car_state.brakePressed = True# latest_state.get("brake", 0)
    car_state.steeringAngleDeg = latest_state.get("steerangle", 0.0)

    pub.send(msg.to_bytes())
    
    elapsed = time.perf_counter() - start
    sleep_time = period - elapsed
    if sleep_time > 0:
      time.sleep(sleep_time)
    start = time.perf_counter()
    
    

