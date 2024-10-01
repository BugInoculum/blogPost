# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer


class PostConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'posts'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Method to handle post update or delete
    async def send_post_update(self, event):
        action = event['action']
        post = event['post']
        print(f"Sending WebSocket message: action={action}, post_id={post['id']}")

        # Send the post data to WebSocket clients
        await self.send(text_data=json.dumps({
            'action': action,
            'post': post
        }))


class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(
            "comments_group",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            "comments_group",
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        comment = data['comment']

        # Broadcast the new comment to all connected WebSocket clients
        await self.channel_layer.group_send(
            "comments_group",
            {
                'type': 'send_comment',
                'comment': comment
            }
        )

    async def send_comment(self, event):
        comment = event['comment']

        # Send the comment to the WebSocket clients
        await self.send(text_data=json.dumps({
            'comment': comment
        }))