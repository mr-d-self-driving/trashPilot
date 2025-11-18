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
        # print(msg)
        try:
            decoded = self.db.decode_message(msg.arbitration_id, msg.data)
            self.state.update(decoded)
            # print(msg)
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
    channel='/dev/ttyACM0@115200',
    interface='slcan',
    can_filters=[]
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
    # print(latest_state.get("BrakeSw1", False))# latest_state.get("brake", 0)
    car_state.brakePressed = bool(latest_state.get("BrakeSw2", False))# latest_state.get("brake", 0)
    # print(latest_state.get("measured_angle", 0.0))
    car_state.steeringAngleDeg = (latest_state.get("measured_angle", 0.0)-337)

    pub.send(msg.to_bytes())
    
    elapsed = time.perf_counter() - start
    sleep_time = period - elapsed
    if sleep_time > 0:
      time.sleep(sleep_time)
    start = time.perf_counter()
    
    

