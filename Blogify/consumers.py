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
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.group_name = f'comments_{self.post_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        comment = data['comment']

        # Broadcast the comment to the group
        await self.channel_layer.group_send(
            self.group_name,
            {
                'type': 'send_comment',
                'comment': comment
            }
        )

    # Send comment to WebSocket
    async def send_comment(self, event):
        comment = event['comment']

        # Send the comment data to the WebSocket
        await self.send(text_data=json.dumps({
            'comment': comment
        }))
