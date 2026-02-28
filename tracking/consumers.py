from channels.generic.websocket import AsyncJsonWebsocketConsumer


class LiveTrackingConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.vehicle_id = self.scope["url_route"]["kwargs"]["vehicle_id"]
        self.group_name = f"vehicle_{self.vehicle_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        payload = {
            "type": "vehicle.location",
            "vehicle_id": self.vehicle_id,
            "latitude": content.get("latitude"),
            "longitude": content.get("longitude"),
            "speed_kmh": content.get("speed_kmh", 0),
            "timestamp": content.get("timestamp"),
        }
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "broadcast_location", "payload": payload},
        )

    async def broadcast_location(self, event):
        await self.send_json(event["payload"])
