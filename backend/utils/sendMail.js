const { SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS } = require('../config/index')

const nodemailer = require('nodemailer');

// Create a transporter object with HostGator SMTP settings
const transporter = nodemailer.createTransport({
    name: 'www.mes-design.com',
    host: SMTP_HOST,
    port: SMTP_PORT,
    secure: true,
    auth: {
        user: SMTP_USER,
        pass: SMTP_PASS
    },
    tls: {
        rejectUnauthorized: false,
    },
});

// Function to send a standalone email
async function sendEmail(toEmail, subject, message) {
  try {
    const mailOptions = {
      from: SMTP_USER,
      to: toEmail,
      subject: subject,
      text: message,
    };

    // Send the email
    const info = await transporter.sendMail(mailOptions);
    console.log('Email sent: ', info.messageId);
  } catch (error) {
    console.error('Error sending email: ', error);
  }
}

// // Example usage: Send a standalone email
// const recipientEmail = 'abanoub.younanh@gmail.com';
// const emailSubject = 'Welcome to Sprinter Eduction Platform';
// const emailMessage = 'Hello I am Abanoub Younan from Sprinter How can I help you';

// (async () => {
//     await sendEmail(recipientEmail, emailSubject, emailMessage);
// })();

module.exports = sendEmail