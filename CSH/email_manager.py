from django.core.mail import send_mail
from django.core.mail import EmailMessage
from django.http import HttpResponse


#Common function to send email with no attachment
def send_email_custom(from_emails1, to_emails, subject, body):
    email_subject = subject
    email_body = body
    email_from = from_emails1
    recipient_list = to_emails

    send_mail(email_subject, email_body, email_from, recipient_list)

    return HttpResponse('Email sent successfully!')


#Common function to send email with attachment
def send_email_with_attachment_custom(from_emails1, to_emails, subject, body,filepath1,admin_email):
    sender_email = from_emails1
    recipient_email = to_emails
    cc_email = admin_email
    email = EmailMessage(
        subject,
        body,
        sender_email,
        recipient_email,
        cc=cc_email,
    )
    file_path = filepath1 
    try:
        with open(file_path, 'rb') as file:
            email.attach_file(file.name)
    except Exception as e:
        return str(f'Error sending email: {str(e)}')

    try:
        # Send the email
        email.send()
        return "success"
    except Exception as e:
        return "error"



