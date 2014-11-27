from rhqmetrics import RHQMetricsClient
import time

def send_example(id, value):
    r = RHQMetricsClient('localhost',8080, 3)
    r.create(id, value)
    r.create(id, float(value) + 2.4)
    r.flush()

    timestamp = int(round(time.time() * 1000))
    
    list = []

    item = { 'id': id,
             'timestamp': timestamp,
             'value': float(value) + 0.1}

    list.append(item)
    
    item = { 'id': id,
             'timestamp': timestamp,
             'value': float(value) + 0.2}

    list.append(item)

    r.put(list)

    item = { 'id': id,
             'timestamp': timestamp,
             'value': float(value) + 0.3}
    
    r.put(item)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        send_example(sys.argv[1], sys.argv[2])
    
