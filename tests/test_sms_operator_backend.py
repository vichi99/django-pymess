from unittest.mock import Mock, patch, call

import pytest
import xml.etree.ElementTree as ET

from pymess.backend.sms.sms_operator import RequestType, SMSOperatorBackend, SmsOperatorState
from pymess.enums import OutputSMSMessageState
from pymess.models.sms import OutputSMSMessage


@pytest.fixture
def backend():
    return SMSOperatorBackend(config={
        'USERNAME': 'user',
        'PASSWORD': 'pass',
        'UNIQ_PREFIX': 'pref',
        'SMS_URL': 'https://sms.example',
        'VOICE_URL': 'https://voice.example',
        'TIMEOUT': 1,
    })


@pytest.mark.django_db
class TestSMSOperatorBackend:
    def test_serialize_voice_message_should_use_voice_template(self, backend):
        message = OutputSMSMessage.objects.create(
            recipient='+420111111111',
            content='Voice content',
            state=OutputSMSMessageState.WAITING,
            is_voice_message=True,
            sender='CallerID',
        )

        xml = backend._serialize_messages([message], RequestType.VOICE_MESSAGE)
        root = ET.fromstring(xml)

        assert root.tag == 'VoiceServices'
        header = root.find('./DataHeader/DataType')
        assert header.text == 'VoiceMessage'
        item = root.find('.//DataItem')
        assert item.find('PhoneNumber').text == '+420111111111'
        assert item.find('./VoiceMsg/Text').text == 'Voice content'
        assert item.find('MsgId').text.endswith(str(message.pk))

    def test_serialize_sms_message_should_use_sms_template(self, backend):
        message = OutputSMSMessage.objects.create(
            recipient='+420222222222',
            content='Sms content',
            state=OutputSMSMessageState.WAITING,
        )

        xml = backend._serialize_messages([message], RequestType.SMS)
        root = ET.fromstring(xml)

        assert root.tag == 'SmsServices'
        header = root.find('./DataHeader/DataType')
        assert header.text == 'SMS'
        item = root.find('.//DataItem')
        assert item.find('SmsId').text.endswith(str(message.pk))

    @pytest.mark.parametrize(
        'request_type,expected_url_attr',
        [
            (RequestType.SMS, 'SMS_URL'),
            (RequestType.VOICE_MESSAGE, 'VOICE_URL'),
        ],
    )
    @patch('pymess.backend.sms.sms_operator.generate_session')
    def test_send_requests_should_use_expected_endpoint(self, mock_generate_session, backend, request_type, expected_url_attr):
        message = OutputSMSMessage.objects.create(
            recipient='+420123456789',
            content='content',
            state=OutputSMSMessageState.WAITING,
            is_voice_message=request_type == RequestType.VOICE_MESSAGE,
        )

        session = Mock()
        if request_type == RequestType.VOICE_MESSAGE:
            body = f'<VoiceServices><DataItem><MsgId>pref-{message.pk}</MsgId><Status>0</Status></DataItem></VoiceServices>'
        else:
            body = f'<SmsServices><DataItem><SmsId>pref-{message.pk}</SmsId><Status>0</Status></DataItem></SmsServices>'
        response = Mock(status_code=200, text=body)
        session.post.return_value = response
        mock_generate_session.return_value = session

        backend._send_requests([message], request_type=request_type, is_sending=True)

        session.post.assert_called_once()
        called_url = session.post.call_args[0][0]
        assert called_url == backend.config[expected_url_attr]

    @patch('pymess.backend.sms.sms_operator.generate_session')
    def test_publish_messages_should_use_endpoint_based_on_sms_message_type(self, mock_generate_session, backend):
        sms = OutputSMSMessage.objects.create(
            recipient='+420111111111',
            content='sms',
            state=OutputSMSMessageState.WAITING,
            is_voice_message=False,
        )
        voice = OutputSMSMessage.objects.create(
            recipient='+420222222222',
            content='voice',
            state=OutputSMSMessageState.WAITING,
            is_voice_message=True,
        )

        session = Mock()
        voice_response = Mock(
            status_code=200,
            text=(
                f'<VoiceServices>'
                f'<DataItem><MsgId>pref-{voice.pk}</MsgId><Status>0</Status></DataItem>'
                f'</VoiceServices>'
            )
        )
        sms_response = Mock(
            status_code=200,
            text=(
                f'<SmsServices>'
                f'<DataItem><SmsId>pref-{sms.pk}</SmsId><Status>0</Status></DataItem>'
                f'</SmsServices>'
            )
        )
        session.post.side_effect = [voice_response, sms_response]
        mock_generate_session.return_value = session

        backend.publish_messages([sms, voice])

        assert session.post.call_count == 2
        called_urls = [call.args[0] for call in session.post.call_args_list]
        assert called_urls[0] == backend.config['VOICE_URL']
        assert called_urls[1] == backend.config['SMS_URL']

    @pytest.mark.parametrize(
        'is_voice_message,expected_request_type,expected_url_key',
        [
            (True, RequestType.VOICE_MESSAGE, 'VOICE_URL'),
            (False, RequestType.SMS, 'SMS_URL'),
        ],
    )
    @patch('pymess.backend.sms.sms_operator.generate_session')
    def test_publish_message_should_use_expected_endpoint(
        self,
        mock_generate_session,
        backend,
        is_voice_message,
        expected_request_type,
        expected_url_key,
    ):
        content = 'voice' if is_voice_message else 'sms'
        message = OutputSMSMessage.objects.create(
            recipient='+420999999999',
            content=content,
            state=OutputSMSMessageState.WAITING,
            is_voice_message=is_voice_message,
        )

        session = Mock()
        template_tag = 'VoiceServices' if is_voice_message else 'SmsServices'
        id_tag = 'MsgId' if is_voice_message else 'SmsId'
        body = (
            f'<{template_tag}>'
            f'<DataItem><{id_tag}>pref-{message.pk}</{id_tag}><Status>0</Status></DataItem>'
            f'</{template_tag}>'
        )
        response = Mock(status_code=200, text=body)
        session.post.return_value = response
        mock_generate_session.return_value = session

        with patch.object(backend, '_send_requests', wraps=backend._send_requests) as mock_send_requests:
            backend.publish_message(message)

        mock_send_requests.assert_called_once()
        send_args, send_kwargs = mock_send_requests.call_args
        assert send_args[0] == [message]
        assert send_kwargs['request_type'] == expected_request_type
        assert send_kwargs['is_sending'] is True
        assert 'sent_at' in send_kwargs

        called_url = session.post.call_args[0][0]
        assert called_url == backend.config[expected_url_key]

    def test_update_sms_states_should_send_requests_per_message_type(self, backend):
        sms = OutputSMSMessage.objects.create(
            recipient='+420111111111',
            content='sms',
            state=OutputSMSMessageState.SENDING,
            is_voice_message=False,
        )
        voice = OutputSMSMessage.objects.create(
            recipient='+420222222222',
            content='voice',
            state=OutputSMSMessageState.SENDING,
            is_voice_message=True,
        )

        with patch.object(backend, '_send_requests') as mock_send_requests:
            backend.update_sms_states([sms, voice])

        expected_calls = [
            call([voice], request_type=RequestType.VOICE_MESSAGE_DELIVERY_REQUEST),
            call([sms], request_type=RequestType.DELIVERY_REQUEST),
        ]
        mock_send_requests.assert_has_calls(expected_calls)
        assert mock_send_requests.call_count == 2

    def test_parse_response_codes_should_accept_msgid_and_smsid(self, backend):
        xml = '''
            <VoiceServices>
              <DataItem><MsgId>pref-10</MsgId><Status>0</Status></DataItem>
              <DataItem><SmsId>pref-11</SmsId><Status>1</Status></DataItem>
            </VoiceServices>
        '''

        result = backend._parse_response_codes(xml)

        assert result[10] == SmsOperatorState.DELIVERED
        assert result[11] == SmsOperatorState.NOT_DELIVERED
