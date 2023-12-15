import json


class Message:
    def __init__(self, event, data):
        self.event = event
        self.data = data

    def to_json(self):
        if self.event in ('requestState', 'requestTelemetry'):
            return json.dumps({'event': self.event})
        else:
            return json.dumps({'event': self.event, 'data': self.data})

    @classmethod
    def from_json(cls, json_str):
        obj = json.loads(json_str)
        return cls(obj['event'], obj['data'])
