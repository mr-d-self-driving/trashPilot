from class_webcam_client import FrameClient
import time
import av

client = FrameClient()

container = av.open("video.mp4", "w")
stream = container.add_stream("libx264", rate=20)

stream.width = client.shape[1]
stream.height = client.shape[0]
stream.pix_fmt = "yuv420p"
# stream.time_base = Fraction(1, FPS)
stream.codec_context.options = {
    "preset": "ultrafast",
    "tune": "zerolatency",
    "crf": "23",          # quality (lower = better, higher = smaller)
}

try:
    while True:
        # Read shared memory → numpy
        start = time.perf_counter()
        frame = av.VideoFrame.from_numpy_buffer(client.frameStream, "bgr24")

        # Convert to yuv420p
        frame = frame.reformat(format="yuv420p")

        for packet in stream.encode(frame):
            container.mux(packet)

        elapsed = time.perf_counter() - start
        sleep_time = 0.05 - elapsed
        if sleep_time > 0:
            time.sleep(sleep_time)

finally:
    for packet in stream.encode(None):
        container.mux(packet)
    container.close()