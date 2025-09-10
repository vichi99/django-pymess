import re
import boto3

from django.conf import settings
from django.utils import timezone

from pymess.config import settings
from pymess.backend.sms import SMSBackend
from pymess.enums import OutputSMSMessageState


class SNSSMSBackend(SMSBackend):
    """
    SMS backend implementing AWS SNS service via boto3 library https://aws.amazon.com/sns/
    """

    sns_client = None
    config = {
        'AWS_ACCESS_KEY_ID': None,
        'AWS_SECRET_ACCESS_KEY': None,
        'AWS_REGION': None,
        'SENDER_ID': None,
    }

    def _clean_sender_name(self, sender_name: str) -> str | None:
        """
        Clean sender name to comply with AWS SNS requirements:
        - Maximum 11 alphanumeric or hyphen (-) characters
        - At least one letter
        - No spaces
        - Must start and end with an alphanumeric character
        """
        if not sender_name or not sender_name.strip():
            return None

        # First pass: preserve hyphens and convert to CamelCase
        # Split by spaces and non-alphanumeric except hyphens
        parts = re.split(r'[^\w-]+', sender_name)

        # Filter out empty parts and create CamelCase while preserving hyphens
        camel_case_parts = []
        for part in parts:
            if part:
                # Handle parts with hyphens
                if '-' in part:
                    # Keep hyphen structure but capitalize each sub-part
                    subparts = part.split('-')
                    camel_subparts = [sub.capitalize() if sub else '' for sub in subparts]
                    camel_case_parts.append('-'.join(camel_subparts))
                else:
                    # Regular word - keep original case for acronyms like "OTP"
                    if part.isupper() and len(part) <= 4:  # Likely acronym
                        camel_case_parts.append(part)
                    else:
                        camel_case_parts.append(part.capitalize())

        cleaned = ''.join(camel_case_parts)

        # Remove any remaining non-alphanumeric characters except hyphens
        cleaned = re.sub(r'[^a-zA-Z0-9-]', '', cleaned)

        # Ensure it starts and ends with alphanumeric
        cleaned = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', cleaned)
        
        # If empty after cleaning, return None
        if not cleaned:
            return None

        # Ensure at least one letter is present
        if not re.search(r'[a-zA-Z]', cleaned):
            # If no letter, add "Msg" suffix (truncate if needed)
            if len(cleaned) > 8:
                cleaned = cleaned[:8]
            cleaned += 'Msg'
        
        # Final truncation to ensure we don't exceed 11 characters
        return cleaned[:11] if len(cleaned) > 11 else cleaned

    def _get_sns_client(self):
        """
        Connect to the SNS service
        """
        if not self.sns_client:
            self.sns_client = boto3.client(
                service_name='sns',
                aws_access_key_id=self.config['AWS_ACCESS_KEY_ID'],
                aws_secret_access_key=self.config['AWS_SECRET_ACCESS_KEY'],
                region_name=self.config['AWS_REGION'],
                use_ssl=True
            )
        return self.sns_client

    def publish_message(self, message):
        """
        Method uses boto3 client via witch SMS message is send
        :param message: SMS message
        """
        sns_client = self._get_sns_client()
        publish_kwargs = {
            'PhoneNumber': str(message.recipient),
            'Message': message.content,
        }

        # Use sender from message (template.sender_name) or fallback to config SENDER_ID
        sender_name = message.sender or self.config['SENDER_ID']
        if sender_name:
            cleaned_sender = self._clean_sender_name(sender_name)
            if cleaned_sender:
                publish_kwargs.update({
                    'MessageAttributes': {
                        'AWS.SNS.SMS.SenderID': {
                            'DataType': 'String',
                            'StringValue': cleaned_sender,
                        }
                    }
                })
        try:
            sns_client.publish(**publish_kwargs)
            self._update_message_after_sending(message, state=OutputSMSMessageState.SENT, sent_at=timezone.now())
        except Exception as ex:
            self._update_message_after_sending_error(
                message, error=str(ex)
            )
            # Do not re-raise caught exception. We do not know exact exception to catch so we catch them all
            # and log them into database. Re-raise exception causes transaction rollback (lost of information about
            # exception).
