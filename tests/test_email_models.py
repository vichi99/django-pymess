import pytest
from pymess.models.emails import EmailMessage
from pymess.enums import EmailMessageState


@pytest.mark.django_db
class TestEmailMessage:

    def test_email_message_failed_property(self):
        """
        Test that the failed property correctly identifies error states.
        """
        # Test non-error state
        message = EmailMessage.objects.create(
            recipient='test@example.com',
            sender='sender@example.com',
            subject='Test Subject',
            content='Test Content',
            state=EmailMessageState.WAITING,
        )
        assert message.failed is False

        # Test error state
        message.change_and_save(state=EmailMessageState.ERROR)
        assert message.failed is True

        # Test error retry state
        message.change_and_save(state=EmailMessageState.ERROR_RETRY)
        assert message.failed is True
