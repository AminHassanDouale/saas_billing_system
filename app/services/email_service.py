"""
Email Notification Service
Send transactional emails to users
"""

import logging
from typing import Optional, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from app.config import settings
from app.models.user import User
from app.models.transaction import Transaction
from app.models.subscription import Subscription

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME
        self.enabled = settings.ENABLE_EMAIL_NOTIFICATIONS

    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text fallback
            
        Returns:
            True if email sent successfully
        """
        if not self.enabled:
            logger.info(f"Email notifications disabled. Would send: {subject} to {to_email}")
            return False

        if not all([self.smtp_host, self.smtp_user, self.smtp_password, self.from_email]):
            logger.warning("Email configuration incomplete. Cannot send email.")
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email

            # Add text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_welcome_email(self, user: User) -> bool:
        """Send welcome email to new user"""
        subject = f"Welcome to {settings.APP_NAME}!"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Welcome to {settings.APP_NAME}! 🎉</h2>
                    
                    <p>Hi {user.first_name or user.username},</p>
                    
                    <p>Thank you for joining {settings.APP_NAME}! We're excited to have you on board.</p>
                    
                    <p>Your account has been successfully created with the following details:</p>
                    <ul>
                        <li><strong>Username:</strong> {user.username}</li>
                        <li><strong>Email:</strong> {user.email}</li>
                    </ul>
                    
                    <p>Get started by exploring our subscription plans and finding the perfect fit for your needs.</p>
                    
                    <div style="margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/plans" 
                           style="background-color: #2563eb; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            View Plans
                        </a>
                    </div>
                    
                    <p>If you have any questions, feel free to reach out to our support team.</p>
                    
                    <p>Best regards,<br>The {settings.APP_NAME} Team</p>
                    
                    <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                    <p style="font-size: 12px; color: #666;">
                        This is an automated message, please do not reply.
                    </p>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(user.email, subject, html_content)

    def send_subscription_confirmation(self, user: User, subscription: Subscription) -> bool:
        """Send subscription confirmation email"""
        subject = f"Subscription Confirmed - {subscription.plan.name}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Subscription Confirmed! ✅</h2>
                    
                    <p>Hi {user.first_name or user.username},</p>
                    
                    <p>Your subscription to the <strong>{subscription.plan.name}</strong> plan has been confirmed!</p>
                    
                    <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Subscription Details</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li><strong>Plan:</strong> {subscription.plan.name}</li>
                            <li><strong>Status:</strong> {subscription.status.value.title()}</li>
                            <li><strong>Period:</strong> {subscription.current_period_start.strftime('%Y-%m-%d')} to {subscription.current_period_end.strftime('%Y-%m-%d')}</li>
                            <li><strong>Price:</strong> {subscription.plan.price} {subscription.plan.currency}/{subscription.plan.interval.value}</li>
                            <li><strong>Auto-renewal:</strong> {'Enabled' if subscription.auto_renew else 'Disabled'}</li>
                        </ul>
                    </div>
                    
                    <p>You can manage your subscription anytime from your account dashboard.</p>
                    
                    <div style="margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/dashboard" 
                           style="background-color: #2563eb; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Go to Dashboard
                        </a>
                    </div>
                    
                    <p>Thank you for choosing {settings.APP_NAME}!</p>
                    
                    <p>Best regards,<br>The {settings.APP_NAME} Team</p>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(user.email, subject, html_content)

    def send_payment_receipt(self, user: User, transaction: Transaction) -> bool:
        """Send payment receipt email"""
        subject = f"Payment Receipt - {transaction.transaction_id}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb;">Payment Receipt 💳</h2>
                    
                    <p>Hi {user.first_name or user.username},</p>
                    
                    <p>Thank you for your payment! Here are the details of your transaction:</p>
                    
                    <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0;">Transaction Details</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li><strong>Transaction ID:</strong> {transaction.transaction_id}</li>
                            <li><strong>Order ID:</strong> {transaction.order_id}</li>
                            <li><strong>Description:</strong> {transaction.title}</li>
                            <li><strong>Amount:</strong> {transaction.amount} {transaction.currency}</li>
                            <li><strong>Fee:</strong> {transaction.fee} {transaction.currency}</li>
                            <li><strong>Net Amount:</strong> {transaction.net_amount} {transaction.currency}</li>
                            <li><strong>Payment Method:</strong> {transaction.payment_method.value.title()}</li>
                            <li><strong>Date:</strong> {transaction.created_at.strftime('%Y-%m-%d %H:%M:%S')}</li>
                            <li><strong>Status:</strong> <span style="color: #059669;">Completed</span></li>
                        </ul>
                    </div>
                    
                    <p>This receipt serves as confirmation of your payment.</p>
                    
                    <p>If you have any questions about this transaction, please contact our support team.</p>
                    
                    <p>Best regards,<br>The {settings.APP_NAME} Team</p>
                    
                    <hr style="margin-top: 30px; border: none; border-top: 1px solid #ddd;">
                    <p style="font-size: 12px; color: #666;">
                        Transaction ID: {transaction.transaction_id}<br>
                        Keep this email for your records.
                    </p>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(user.email, subject, html_content)

    def send_payment_failed(self, user: User, transaction: Transaction) -> bool:
        """Send payment failed notification"""
        subject = f"Payment Failed - Action Required"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #dc2626;">Payment Failed ⚠️</h2>
                    
                    <p>Hi {user.first_name or user.username},</p>
                    
                    <p>We were unable to process your recent payment. Please review the details below:</p>
                    
                    <div style="background-color: #fef2f2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #dc2626;">
                        <h3 style="margin-top: 0; color: #dc2626;">Payment Details</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li><strong>Transaction ID:</strong> {transaction.transaction_id}</li>
                            <li><strong>Amount:</strong> {transaction.amount} {transaction.currency}</li>
                            <li><strong>Description:</strong> {transaction.title}</li>
                            <li><strong>Error:</strong> {transaction.error_message or 'Payment declined'}</li>
                        </ul>
                    </div>
                    
                    <p><strong>What to do next:</strong></p>
                    <ul>
                        <li>Check that you have sufficient funds</li>
                        <li>Verify your payment details</li>
                        <li>Try again with a different payment method</li>
                    </ul>
                    
                    <div style="margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/billing" 
                           style="background-color: #dc2626; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Update Payment Method
                        </a>
                    </div>
                    
                    <p>If you continue to experience issues, please contact our support team.</p>
                    
                    <p>Best regards,<br>The {settings.APP_NAME} Team</p>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(user.email, subject, html_content)

    def send_subscription_expiring(self, user: User, subscription: Subscription, days: int) -> bool:
        """Send subscription expiring notification"""
        subject = f"Your Subscription Expires in {days} Days"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #f59e0b;">Subscription Expiring Soon ⏰</h2>
                    
                    <p>Hi {user.first_name or user.username},</p>
                    
                    <p>This is a friendly reminder that your <strong>{subscription.plan.name}</strong> subscription will expire in <strong>{days} days</strong>.</p>
                    
                    <div style="background-color: #fffbeb; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                        <h3 style="margin-top: 0;">Subscription Details</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li><strong>Plan:</strong> {subscription.plan.name}</li>
                            <li><strong>Expires:</strong> {subscription.current_period_end.strftime('%Y-%m-%d')}</li>
                            <li><strong>Auto-renewal:</strong> {'Enabled' if subscription.auto_renew else 'Disabled'}</li>
                        </ul>
                    </div>
                    
                    {'<p>Your subscription will automatically renew on ' + subscription.current_period_end.strftime('%Y-%m-%d') + '. No action needed!</p>' if subscription.auto_renew else '<p><strong>Action Required:</strong> To continue using our services, please renew your subscription before it expires.</p>'}
                    
                    <div style="margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/subscription" 
                           style="background-color: #2563eb; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Manage Subscription
                        </a>
                    </div>
                    
                    <p>Thank you for being a valued customer!</p>
                    
                    <p>Best regards,<br>The {settings.APP_NAME} Team</p>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(user.email, subject, html_content)

    def send_refund_processed(self, user: User, refund) -> bool:
        """Send refund processed notification"""
        subject = f"Refund Processed - {refund.refund_id}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #059669;">Refund Processed ✅</h2>
                    
                    <p>Hi {user.first_name or user.username},</p>
                    
                    <p>Your refund request has been processed successfully.</p>
                    
                    <div style="background-color: #f0fdf4; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #059669;">
                        <h3 style="margin-top: 0;">Refund Details</h3>
                        <ul style="list-style: none; padding: 0;">
                            <li><strong>Refund ID:</strong> {refund.refund_id}</li>
                            <li><strong>Original Amount:</strong> {refund.original_amount} {refund.currency}</li>
                            <li><strong>Refund Amount:</strong> {refund.refund_amount} {refund.currency}</li>
                            <li><strong>Type:</strong> {'Partial Refund' if refund.is_partial else 'Full Refund'}</li>
                            <li><strong>Processed Date:</strong> {refund.completed_at.strftime('%Y-%m-%d %H:%M:%S') if refund.completed_at else 'Processing'}</li>
                        </ul>
                    </div>
                    
                    <p>The refunded amount will be credited to your original payment method within 5-10 business days.</p>
                    
                    <p>If you have any questions about this refund, please contact our support team.</p>
                    
                    <p>Best regards,<br>The {settings.APP_NAME} Team</p>
                </div>
            </body>
        </html>
        """
        
        return self._send_email(user.email, subject, html_content)
