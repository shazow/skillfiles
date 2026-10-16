# Beacon Protocol

Beacon connects small sensor devices to a collector. A device connects over
WebSocket, sends readings, and receives configuration.

## 1. Framing

- Each WebSocket text message carries one JSON object, called a frame.
- Requests carry an `id`; notifications don't. Every request gets a result or
  an error with the same `id`.
- Unknown keys in a frame are ignored.

## 2. Devices

```ts
class Device {
  device_id: string;   // assigned by the collector
  name?: string;       // set by the device with `set_name`
  tags?: string[];     // set by operators on the collector
}
```

- The collector assigns `device_id` at first connection.
- Devices set `name` with the `set_name` request:
  `{"method": "set_name", "id": "n1", "params": {"name": "greenhouse-2"}}`.
- Collectors MUST ignore unknown keys in a `set_name` request.

## 3. Readings

- Devices send readings with the `report` notification:
  `{"method": "report", "params": {"sensor": "temp", "value": 21.5, "time": 1791400000}}`.
- `time` is in seconds since the Unix epoch.
- The collector stores readings in the order it receives them.
- The collector MUST ignore unknown keys in a `report`.

## 4. Listing devices

- Operators' tools list devices with the `devices` request. The result is
  `{"devices": [Device, ...]}`.
- The collector returns every device it knows.
