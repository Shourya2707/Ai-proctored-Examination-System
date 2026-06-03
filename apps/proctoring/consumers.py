import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .ai_engine import AIProctorEngine
from .models import ViolationLog
from apps.exams.models import ExamAttempt

ai_engine = AIProctorEngine()

class ProctoringConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.exam_id = self.scope['url_route']['kwargs']['exam_id']
        self.room_group_name = f'exam_{self.exam_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        event_type = text_data_json.get('type')

        if event_type == 'video_frame':
            frame_data = text_data_json['image']
            
            # Heavy CV analysis using threadpool/sync-to-async would be ideal, 
            # but running directly for this high-performance proctor engine.
            violations, metrics = ai_engine.process_frame(frame_data)
            
            # Save and calculate risk scores
            risk_score, warnings, is_disqualified = await self.save_violations(violations, frame_data)
            
            # Always stream active video frames & metrics to the admin dashboard
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'admin_feed_update',
                    'student_id': self.scope['user'].id if self.scope['user'].is_authenticated else 'Unknown',
                    'username': self.scope['user'].username if self.scope['user'].is_authenticated else 'Unknown',
                    'image': frame_data,
                    'metrics': metrics,
                    'violations': violations,
                    'risk_score': risk_score,
                    'warnings': warnings,
                    'is_disqualified': is_disqualified
                }
            )

            # Send immediate feedback back to student
            await self.send(text_data=json.dumps({
                'type': 'ai_alert',
                'violations': violations,
                'risk_score': risk_score,
                'warnings': warnings,
                'is_disqualified': is_disqualified
            }))

        elif event_type == 'browser_event':
            event_name = text_data_json['event']
            
            # Process browser-side event
            risk_score, warnings, is_disqualified = await self.save_violations([event_name], None)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'admin_alert',
                    'student_id': self.scope['user'].id if self.scope['user'].is_authenticated else 'Unknown',
                    'username': self.scope['user'].username if self.scope['user'].is_authenticated else 'Unknown',
                    'violations': [event_name],
                    'risk_score': risk_score,
                    'warnings': warnings,
                    'is_disqualified': is_disqualified
                }
            )
            
            await self.send(text_data=json.dumps({
                'type': 'ai_alert',
                'violations': [event_name],
                'risk_score': risk_score,
                'warnings': warnings,
                'is_disqualified': is_disqualified
            }))

    @database_sync_to_async
    def save_violations(self, violations, base64_image=None):
        if not self.scope['user'].is_authenticated:
            return 0.0, 0, False
            
        try:
            attempt = ExamAttempt.objects.filter(
                student=self.scope['user'], 
                exam_id=self.exam_id, 
                status='IN_PROGRESS'
            ).latest('start_time')
            
            exam = attempt.exam
            
            # Map risk weight increments
            risk_weights = {
                'NO_FACE': 10.0,
                'MULTIPLE_FACES': 30.0,
                'EYE_LOOKAWAY': 12.0,
                'HEAD_TURN': 15.0,
                'PHONE_DETECTED': 40.0,
                'HEADPHONES': 20.0,
                'TAB_SWITCH': 20.0,
                'FULLSCREEN_EXIT': 25.0,
                'CLIPBOARD_USE': 5.0,
                'RIGHT_CLICK': 5.0,
                'HOTKEY_PRESS': 10.0,
                'WEBCAM_DISCONNECT': 15.0,
                'NETWORK_DISCONNECT': 10.0
            }
            
            photo_file = None
            if base64_image and len(violations) > 0:
                import base64
                from django.core.files.base import ContentFile
                try:
                    format, imgstr = base64_image.split(';base64,')
                    ext = format.split('/')[-1]
                    photo_file = ContentFile(base64.b64decode(imgstr), name=f"violation_{attempt.id}_{violations[0]}.{ext}")
                except Exception as e:
                    print(f"Error parsing violation image: {e}")

            for v_type in violations:
                log = ViolationLog.objects.create(
                    attempt=attempt,
                    violation_type=v_type
                )
                if photo_file:
                    log.snapshot = photo_file
                    log.save()
                
                # Increment risk score
                weight = risk_weights.get(v_type, 10.0)
                attempt.cheating_risk_score = min(100.0, attempt.cheating_risk_score + weight)
                
                # Dynamic warning levels
                if v_type in ['TAB_SWITCH', 'FULLSCREEN_EXIT', 'MULTIPLE_FACES', 'PHONE_DETECTED', 'EYE_LOOKAWAY', 'HEAD_TURN']:
                    attempt.warning_count += 1
            
            is_disqualified = False
            # Check thresholds
            if attempt.cheating_risk_score >= 100.0 or attempt.warning_count >= exam.allowed_warnings:
                attempt.status = 'DISQUALIFIED'
                attempt.save()
                is_disqualified = True
            else:
                attempt.save()
                
            return attempt.cheating_risk_score, attempt.warning_count, is_disqualified
        except ExamAttempt.DoesNotExist:
            return 0.0, 0, False

    # Receive message from room group
    async def admin_alert(self, event):
        await self.send(text_data=json.dumps({
            'type': 'admin_alert',
            'student_id': event['student_id'],
            'username': event.get('username', 'Unknown'),
            'violations': event['violations'],
            'risk_score': event['risk_score'],
            'warnings': event['warnings'],
            'is_disqualified': event['is_disqualified']
        }))

    async def admin_feed_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'admin_feed_update',
            'student_id': event['student_id'],
            'username': event['username'],
            'image': event['image'],
            'metrics': event['metrics'],
            'violations': event.get('violations', []),
            'risk_score': event.get('risk_score', 0.0),
            'warnings': event.get('warnings', 0),
            'is_disqualified': event.get('is_disqualified', False)
        }))
