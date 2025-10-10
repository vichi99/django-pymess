import pytest
from unittest.mock import Mock, patch

from pymess.backend.sms import SMSController
from pymess.enums import OutputSMSMessageState
from pymess.models.sms import OutputSMSMessage, SMSTemplate


@pytest.mark.django_db
class TestSMSController:
    def test_create_message_should_inherit_voice_flag_from_template(self):
        template = SMSTemplate.objects.create(
            slug='voice-otp',
            body='Voice body',
            sender_name='MyApp',
            is_voice_message=True,
        )
        controller = SMSController()

        with patch.object(controller, 'get_backend') as mock_get_backend:
            backend = Mock()
            backend.get_extra_message_kwargs.return_value = {}
            mock_get_backend.return_value = backend

            message = controller.create_message(
                recipient='+420123456789',
                content='content',
                related_objects=[],
                tag='otp',
                template=template,
            )

        assert message.is_voice_message is True
        assert message.sender == 'MyApp'
        mock_get_backend.assert_called_once_with('+420123456789', is_voice_message=True)

    def test_create_message_without_template_should_default_to_sms(self):
        controller = SMSController()

        with patch.object(controller, 'get_backend') as mock_get_backend:
            backend = Mock()
            backend.get_extra_message_kwargs.return_value = {}
            mock_get_backend.return_value = backend

            message = controller.create_message(
                recipient='+420123456789',
                content='content',
                related_objects=[],
                tag='otp',
                template=None,
            )

        assert message.is_voice_message is False
        mock_get_backend.assert_called_once_with('+420123456789', is_voice_message=False)

    def test_get_backend_should_pass_voice_flag_to_router(self):
        controller = SMSController()

        with patch.object(controller, 'router') as mock_router:
            with patch('pymess.backend.get_backend') as mock_get_backend:
                backend = Mock()
                backend.get_extra_message_kwargs.return_value = {}
                mock_get_backend.return_value = backend
                mock_router.get_backend_name.return_value = 'dummy-backend'

                controller.get_backend(recipient='+420123456789', is_voice_message=True)

        mock_router.get_backend_name.assert_called_once_with('+420123456789', is_voice_message=True)
        mock_get_backend.assert_called_once_with(controller.backend_type_name, 'dummy-backend')
