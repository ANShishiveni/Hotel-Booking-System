"""
Email service for sending notifications and confirmations
"""

from flask import current_app, render_template_string
from flask_mail import Message, Mail
from app import mail
from datetime import datetime
import os

class EmailService:
    """Service class for sending emails"""
    
    @staticmethod
    def send_email(to, subject, template, **kwargs):
        """Send an email using a template"""
        try:
            msg = Message(
                subject=subject,
                recipients=[to],
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            
            # Render template with context
            msg.html = render_template_string(template, **kwargs)
            msg.body = render_template_string(template.replace('<br>', '\n').replace('<p>', '\n').replace('</p>', '\n'), **kwargs)
            
            mail.send(msg)
            current_app.logger.info(f"Email sent successfully to {to}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Failed to send email to {to}: {str(e)}")
            return False

    @staticmethod
    def send_booking_confirmation(booking):
        """Send booking confirmation email"""
        hotel = booking.hotel
        user = booking.user
        room_type = booking.room_type
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #06043e; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0;">Namibia Hotels</h1>
                    <p style="margin: 5px 0 0 0;">Booking Confirmation</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px;">
                    <h2 style="color: #06043e; margin-top: 0;">Hello {{ user.first_name }}!</h2>
                    
                    <p>Your hotel booking has been confirmed. Here are your booking details:</p>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #06043e; margin-top: 0;">Booking Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Booking Reference:</td>
                                <td style="padding: 8px 0;">{{ booking.booking_reference }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Hotel:</td>
                                <td style="padding: 8px 0;">{{ hotel.name }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Location:</td>
                                <td style="padding: 8px 0;">{{ hotel.city }}, {{ hotel.country }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Room Type:</td>
                                <td style="padding: 8px 0;">{{ room_type.name }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Check-in:</td>
                                <td style="padding: 8px 0;">{{ booking.check_in_date.strftime('%B %d, %Y') }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Check-out:</td>
                                <td style="padding: 8px 0;">{{ booking.check_out_date.strftime('%B %d, %Y') }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Nights:</td>
                                <td style="padding: 8px 0;">{{ booking.nights }} night{{ 's' if booking.nights != 1 else '' }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Guests:</td>
                                <td style="padding: 8px 0;">{{ booking.adults }} adult{{ 's' if booking.adults != 1 else '' }}{% if booking.children > 0 %}, {{ booking.children }} child{{ 'ren' if booking.children != 1 else '' }}{% endif %}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Total Amount:</td>
                                <td style="padding: 8px 0; font-weight: bold; color: #06043e;">N${{ "%.2f"|format(booking.total_amount) }}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background-color: #e8f4fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="color: #06043e; margin-top: 0;">Important Information</h4>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Please arrive at the hotel on your check-in date</li>
                            <li>Check-in time is typically after 2:00 PM</li>
                            <li>Check-out time is typically before 11:00 AM</li>
                            <li>Keep this confirmation email for your records</li>
                        </ul>
                    </div>
                    
                    <p>If you have any questions or need to modify your booking, please contact us.</p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <p style="color: #666; font-size: 14px;">
                            Thank you for choosing Namibia Hotels!<br>
                            We look forward to hosting you.
                        </p>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                    <p>© 2025 Namibia Hotels. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(
            to=user.email,
            subject=f"Booking Confirmation - {hotel.name}",
            template=template,
            booking=booking,
            hotel=hotel,
            user=user,
            room_type=room_type
        )

    @staticmethod
    def send_payment_confirmation(payment):
        """Send payment confirmation email"""
        booking = payment.booking
        hotel = booking.hotel
        user = booking.user
        
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #28a745; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0;">Namibia Hotels</h1>
                    <p style="margin: 5px 0 0 0;">Payment Confirmation</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px;">
                    <h2 style="color: #28a745; margin-top: 0;">Payment Successful!</h2>
                    
                    <p>Hello {{ user.first_name }},</p>
                    <p>Your payment for your hotel booking has been processed successfully.</p>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #28a745; margin-top: 0;">Payment Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Payment Reference:</td>
                                <td style="padding: 8px 0;">{{ payment.payment_reference }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Booking Reference:</td>
                                <td style="padding: 8px 0;">{{ booking.booking_reference }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Hotel:</td>
                                <td style="padding: 8px 0;">{{ hotel.name }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Amount Paid:</td>
                                <td style="padding: 8px 0; font-weight: bold; color: #28a745;">N${{ "%.2f"|format(payment.amount) }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Payment Method:</td>
                                <td style="padding: 8px 0;">{{ payment.payment_method|title }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Payment Date:</td>
                                <td style="padding: 8px 0;">{{ payment.created_at.strftime('%B %d, %Y at %I:%M %p') }}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background-color: #d4edda; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="color: #155724; margin-top: 0;">✅ Payment Status: Completed</h4>
                        <p style="margin: 5px 0; color: #155724;">Your booking is now confirmed and secured.</p>
                    </div>
                    
                    <p>Your booking confirmation has been sent separately. You can also view your booking details in your account.</p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <p style="color: #666; font-size: 14px;">
                            Thank you for your payment!<br>
                            We look forward to hosting you at {{ hotel.name }}.
                        </p>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                    <p>© 2025 Namibia Hotels. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(
            to=user.email,
            subject=f"Payment Confirmation - {hotel.name}",
            template=template,
            payment=payment,
            booking=booking,
            hotel=hotel,
            user=user
        )

    @staticmethod
    def send_registration_welcome(user):
        """Send welcome email to new user"""
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #06043e; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0;">Namibia Hotels</h1>
                    <p style="margin: 5px 0 0 0;">Welcome to Our Family!</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px;">
                    <h2 style="color: #06043e; margin-top: 0;">Welcome {{ user.first_name }}!</h2>
                    
                    <p>Thank you for joining Namibia Hotels! We're excited to have you as part of our community.</p>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #06043e; margin-top: 0;">Your Account Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Name:</td>
                                <td style="padding: 8px 0;">{{ user.first_name }} {{ user.last_name }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Email:</td>
                                <td style="padding: 8px 0;">{{ user.email }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Username:</td>
                                <td style="padding: 8px 0;">{{ user.username }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Member Since:</td>
                                <td style="padding: 8px 0;">{{ user.created_at.strftime('%B %d, %Y') }}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background-color: #e8f4fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="color: #06043e; margin-top: 0;">What's Next?</h4>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Explore our luxury hotels across Namibia</li>
                            <li>Book your next stay with exclusive member rates</li>
                            <li>Read reviews from other guests</li>
                            <li>Manage your bookings from your dashboard</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{{ url_for('main.index', _external=True) }}" 
                           style="background-color: #06043e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Start Exploring Hotels
                        </a>
                    </div>
                    
                    <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <p style="color: #666; font-size: 14px;">
                            Welcome to Namibia Hotels!<br>
                            Your journey to exceptional hospitality starts here.
                        </p>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                    <p>© 2025 Namibia Hotels. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(
            to=user.email,
            subject="Welcome to Namibia Hotels!",
            template=template,
            user=user
        )

    @staticmethod
    def send_password_reset(user, reset_token):
        """Send password reset email"""
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0;">Namibia Hotels</h1>
                    <p style="margin: 5px 0 0 0;">Password Reset Request</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px;">
                    <h2 style="color: #dc3545; margin-top: 0;">Password Reset Request</h2>
                    
                    <p>Hello {{ user.first_name }},</p>
                    <p>We received a request to reset your password for your Namibia Hotels account.</p>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                        <h3 style="color: #dc3545; margin-top: 0;">Reset Your Password</h3>
                        <p>Click the button below to reset your password:</p>
                        <a href="{{ url_for('auth.reset_password', token=reset_token, _external=True) }}" 
                           style="background-color: #dc3545; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 0;">
                            Reset Password
                        </a>
                        <p style="margin-top: 15px; font-size: 12px; color: #666;">
                            This link will expire in 1 hour for security reasons.
                        </p>
                    </div>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="color: #856404; margin-top: 0;">Security Notice</h4>
                        <ul style="margin: 10px 0; padding-left: 20px; color: #856404;">
                            <li>If you didn't request this password reset, please ignore this email</li>
                            <li>Your password will remain unchanged until you create a new one</li>
                            <li>For security, this link expires in 1 hour</li>
                        </ul>
                    </div>
                    
                    <p>If you're having trouble clicking the button, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #666; font-size: 12px;">
                        {{ url_for('auth.reset_password', token=reset_token, _external=True) }}
                    </p>
                    
                    <div style="text-align: center; margin-top: 30px;">
                        <p style="color: #666; font-size: 14px;">
                            If you have any questions, please contact our support team.
                        </p>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                    <p>© 2025 Namibia Hotels. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return EmailService.send_email(
            to=user.email,
            subject="Password Reset Request - Namibia Hotels",
            template=template,
            user=user,
            reset_token=reset_token
        )

    @staticmethod
    def send_contact_notification(contact_data):
        """Send contact form notification to admin"""
        template = """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background-color: #17a2b8; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0;">
                    <h1 style="margin: 0;">Namibia Hotels</h1>
                    <p style="margin: 5px 0 0 0;">New Contact Form Submission</p>
                </div>
                
                <div style="background-color: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px;">
                    <h2 style="color: #17a2b8; margin-top: 0;">Contact Form Submission</h2>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #17a2b8; margin-top: 0;">Contact Details</h3>
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Name:</td>
                                <td style="padding: 8px 0;">{{ contact_data.firstName }} {{ contact_data.lastName }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Email:</td>
                                <td style="padding: 8px 0;">{{ contact_data.email }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Subject:</td>
                                <td style="padding: 8px 0;">{{ contact_data.subject }}</td>
                            </tr>
                            <tr>
                                <td style="padding: 8px 0; font-weight: bold;">Submitted:</td>
                                <td style="padding: 8px 0;">{{ contact_data.submitted_at.strftime('%B %d, %Y at %I:%M %p') }}</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div style="background-color: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #17a2b8; margin-top: 0;">Message</h3>
                        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #17a2b8;">
                            {{ contact_data.message }}
                        </div>
                    </div>
                    
                    <div style="background-color: #e8f4fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <h4 style="color: #17a2b8; margin-top: 0;">Action Required</h4>
                        <p style="margin: 5px 0;">Please respond to this inquiry at your earliest convenience.</p>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 20px; color: #666; font-size: 12px;">
                    <p>© 2025 Namibia Hotels. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Get admin email from config or use default
        admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@namibiahotels.com')
        
        return EmailService.send_email(
            to=admin_email,
            subject=f"Contact Form: {contact_data.subject}",
            template=template,
            contact_data=contact_data
        )
