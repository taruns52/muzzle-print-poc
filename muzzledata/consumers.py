import json
import base64
import cv2
import numpy as np

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile

from .models import Cow
from .utils import generate_encoding, verify_encoding


class CowDetectionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.mode = self.scope['url_route']['kwargs']['mode']
        print(f"WebSocket connected in {self.mode} mode.")

    async def receive(self, text_data):
        data = json.loads(text_data)
        image_data = data['image']
        cow_name = data.get('cow_name', 'Unknown')

        try:
            # Decode image
            header, encoded = image_data.split(',', 1)
            image_bytes = base64.b64decode(encoded)
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Detect muzzle and encode
            descriptors, cropped_image, box, confidence = generate_encoding(frame, 'live_detect')

            # FIX: check descriptors properly
            if descriptors is not None and len(descriptors) > 0 and cropped_image is not None:
                response = {
                    'status': 'processing',
                    'confidence': float(confidence),
                    'box': box,
                    'message': 'Muzzle detected'
                }

                if self.mode == 'register':
                    await self.save_cow(cow_name, cropped_image, descriptors)
                    response['status'] = 'done'
                    response['message'] = 'Cow data saved!'
                    await self.send(text_data=json.dumps(response))
                    await self.close()

                elif self.mode == 'verify':
                    cow = await self.verify_cow(descriptors)
                    if cow:
                        response = {
                            'status': 'success',
                            'cow_name': cow.cow_name,
                            'cow_image_url': cow.cow_image.url
                        }
                        await self.send(text_data=json.dumps(response))
                        await self.close()
                    else:
                        response['status'] = 'fail'
                        response['message'] = 'No match found'
                        await self.send(text_data=json.dumps(response))

                else:
                    await self.send(text_data=json.dumps(response))

            else:
                await self.send(text_data=json.dumps({
                    'status': 'fail',
                    'message': 'Muzzle not detected'
                }))

        except Exception as e:
            await self.send(text_data=json.dumps({
                'status': 'error',
                'message': str(e)
            }))

    async def disconnect(self, close_code):
        print("WebSocket disconnected.")

    @sync_to_async
    def save_cow(self, name, image_bytes, descriptors):
        file = ContentFile(image_bytes)
        file.name = f"{name}.jpg"
        Cow.objects.create(
            cow_name=name,
            cow_image=file,
            cow_encoding=descriptors
        )

    @sync_to_async
    def verify_cow(self, descriptors):
        return verify_encoding(descriptors)