import pytest
from unittest.mock import patch

from pymess.models.sms import OutputSMSMessage
from pymess.enums import OutputSMSMessageState


@pytest.mark.django_db
class TestOutputSMSMessageCleanContent:

    @pytest.mark.parametrize('use_accent,expected_content', [
        (False, 'Prilis zlutoucky kun upel dabelske ody'),
        (True, 'Příliš žluťoučký kůň úpěl ďábelské ódy'),
    ])
    def test_clean_content_should_handle_accents_for_regular_sms_based_on_setting(self, use_accent, expected_content):
        message = OutputSMSMessage(
            recipient='+420123456789',
            content='Příliš žluťoučký kůň úpěl ďábelské ódy',
            state=OutputSMSMessageState.WAITING,
            is_voice_message=False,
        )

        with patch('pymess.models.sms.settings.SMS_USE_ACCENT', use_accent):
            message.clean_content()

        assert message.content == expected_content

    @pytest.mark.parametrize('use_accent', [False, True])
    def test_clean_content_should_keep_accents_for_voice_message_regardless_of_setting(self, use_accent):
        message = OutputSMSMessage(
            recipient='+420123456789',
            content='Příliš žluťoučký kůň úpěl ďábelské ódy',
            state=OutputSMSMessageState.WAITING,
            is_voice_message=True,
        )

        with patch('pymess.models.sms.settings.SMS_USE_ACCENT', use_accent):
            message.clean_content()

        assert message.content == 'Příliš žluťoučký kůň úpěl ďábelské ódy'
