import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Mock boto3 at the module level
sys.modules['boto3'] = MagicMock()

from pymess.backend.sms.sns import SNSSMSBackend


class TestSNSSMSBackend:
    """
    Test cases for SNS SMS backend sender name cleaning functionality
    """

    def setup_method(self):
        self.backend = SNSSMSBackend()

    @pytest.mark.parametrize("input_name,expected_output", [
        # Basic CamelCase conversion
        ("Skip Pay OTP", "SkipPayOTP"),
        ("My Company", "MyCompany"),

        # Truncation
        ("Very Long Company Name Here", "VeryLongCom"),

        # Special characters and hyphens
        ("Company-Name!", "Company-Nam"),
        ("My-Company", "My-Company"),

        # Numeric cases
        ("123456", "123456Msg"),
        ("123-456", "123-456Msg"),
        ("123456789012", "12345678Msg"),

        # Edge cases
        ("", None),
        (None, None),
        ("   ", None),
        ("!@#$%", None),

        # Start/end alphanumeric
        ("-Company-", "Company"),
        ("!@Company Name#$", "CompanyName"),

        # Mixed cases
        ("Company123", "Company123"),
        ("Test-123-Name", "Test-123-Na"),
    ])
    def test_clean_sender_name(self, input_name, expected_output):
        """Test sender name cleaning with various inputs"""
        result = self.backend._clean_sender_name(input_name)
        assert result == expected_output

    @patch('pymess.backend.sms.sns.boto3.client')
    def test_publish_message_with_cleaned_sender(self, mock_boto3_client):
        """Test that publish_message uses cleaned sender name"""
        mock_sns_client = Mock()
        mock_boto3_client.return_value = mock_sns_client

        # Create a mock message with sender
        message = Mock()
        message.recipient = "+1234567890"
        message.content = "Test message"
        message.sender = "Skip Pay OTP"  # This should be cleaned to "SkipPayOtp"

        # Mock the backend methods
        self.backend._update_message_after_sending = Mock()

        # Call publish_message
        self.backend.publish_message(message)

        # Verify SNS client was called with cleaned sender
        mock_sns_client.publish.assert_called_once()
        call_args = mock_sns_client.publish.call_args[1]

        assert 'MessageAttributes' in call_args
        assert 'AWS.SNS.SMS.SenderID' in call_args['MessageAttributes']
        assert call_args['MessageAttributes']['AWS.SNS.SMS.SenderID']['StringValue'] == 'SkipPayOTP'

    @patch('pymess.backend.sms.sns.boto3.client')
    def test_publish_message_fallback_to_config(self, mock_boto3_client):
        """Test that publish_message falls back to config SENDER_ID when message.sender is None"""
        mock_sns_client = Mock()
        mock_boto3_client.return_value = mock_sns_client

        # Set config SENDER_ID
        self.backend.config['SENDER_ID'] = "Default Company"

        # Create a mock message without sender
        message = Mock()
        message.recipient = "+1234567890"
        message.content = "Test message"
        message.sender = None

        # Mock the backend methods
        self.backend._update_message_after_sending = Mock()

        # Call publish_message
        self.backend.publish_message(message)

        # Verify SNS client was called with cleaned config sender
        mock_sns_client.publish.assert_called_once()
        call_args = mock_sns_client.publish.call_args[1]

        assert 'MessageAttributes' in call_args
        assert call_args['MessageAttributes']['AWS.SNS.SMS.SenderID']['StringValue'] == 'DefaultComp'

    @patch('pymess.backend.sms.sns.boto3.client')
    def test_publish_message_no_sender_attributes_when_empty(self, mock_boto3_client):
        """Test that no MessageAttributes are set when sender name cleans to empty/None"""
        mock_sns_client = Mock()
        mock_boto3_client.return_value = mock_sns_client

        # Create a mock message with sender that cleans to None
        message = Mock()
        message.recipient = "+1234567890"
        message.content = "Test message"
        message.sender = "!@#$%"  # This cleans to None

        # Mock the backend methods
        self.backend._update_message_after_sending = Mock()

        # Call publish_message
        self.backend.publish_message(message)
        
        # Verify SNS client was called without MessageAttributes
        mock_sns_client.publish.assert_called_once()
        call_args = mock_sns_client.publish.call_args[1]

        assert 'MessageAttributes' not in call_args
