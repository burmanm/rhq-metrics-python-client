from rhqmetrics import RHQMetricsClient

def send_example(id, value):
    r = RHQMetricsClient()
    r.put(id, value)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        send_example(sys.argv[1], sys.argv[2])
    
