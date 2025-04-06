const bcrypt = require('bcrypt');
const crypto = require("crypto");
const jwt = require('jsonwebtoken');

const userModel = require('../models/users/index');
const authModel = require('../models/auth/index')

const signCookie = require('../utils/cdnSignCookies')
const sendEmail = require('../utils/sendMail')
const { CLOUDFRONT_DOMAIN_NAME_Cookie, JWT_SECRET } = require('../config/index')


exports.Login = async (req, res) => {
    const { Email, Password } = req.body;
    if(!Email || !Password){
        return res.status(400).json({'Message': "Email, and Password are Required"})
    }

    try {
        const userData = await userModel.getUserByEmail(Email);

        if(!userData){
            return res.status(400).json({'Message': "Email doesn't Exist."})
        }

        if(!userData['verified']){
            return res.status(400).json({'Message': "Your Account hasn't activated yet!"})
        }

        const concat_password = Email + Password ;
        const isPasswordValid = await bcrypt.compare(concat_password, userData.password_hash);

        if (!isPasswordValid) {
            return res.status(400).json({'Message': "Invalid Password!"})
        }

        const token = jwt.sign(
            {   
                "UserID": userData.user_ID, "UserType": userData.role,
                "Name": userData.full_name,
                "Email": userData.email
            },
            JWT_SECRET,
            // { expiresIn: '12h' } // Remove it now for simplicity 
        );

        const signedCookies = await signCookie();
        Object.entries(signedCookies).forEach(([key, value]) => {
            res.cookie(key, value, {
                domain: CLOUDFRONT_DOMAIN_NAME_Cookie,
                httpOnly: false,
                secure: true,
                sameSite: "None",
              });
        });
        res.status(200).json({ message: 'Login successful', token});
    } catch (error) {
        console.error(error);
        res.status(401).json({ message: error.message });
    }
};

exports.StudentSignUp = async (req, res) => {
    const { FullName, Email, Password } = req.body;

    if(!FullName || !Email || !Password){
        return res.status(400).json({'Message': "FullName, Email, and Password are Required"})
    }

    try {

        const userData = await userModel.getUserByEmail(Email);

        if(userData && userData['verified']){
            return res.status(400).json({'Message': "This Email Exist."})
        }

        
        const EmailVerificationToken = crypto.randomBytes(32).toString("hex"); // Generate Verification Token
        
        const EmailVerificationExpires = new Date();
        EmailVerificationExpires.setHours(EmailVerificationExpires.getHours() + 24); // Set expiration to 24 hours
        
        const verificationLink = `http://sprinter.mes-design.com/verify-email?token=${EmailVerificationToken}`;
        
        const emailSubject = 'Verify Your Email'
        const emailMessage = `
        Welcome to Sprinter!,
        
        Click the link to verify your email: ${verificationLink}\nThis link expires in 24 hours.
        `
        await sendEmail(Email, emailSubject, emailMessage);
        
        if(!userData){ // If user doesn't exist inser 
            // Concatenate Email with the password and hash it
            const concatenatedPassword = Email + Password;
            const PasswordHash = await bcrypt.hash(concatenatedPassword, 10);
    
            await userModel.SignUp(FullName, Email, PasswordHash, 'student', EmailVerificationToken, EmailVerificationExpires)
        }else{
            await userModel.UpdateEmailVerificationToken(EmailVerificationToken, EmailVerificationExpires, Email)
        }

        res.status(200).json({ message: 'Verfication Code sent to your email'});
    } catch (error) {                                               
        console.error('Error in Creating New Student', error);
        res.status(401).json({ message: error.message });
    }
};

exports.VerifyEmail = async (req, res) => {
    const { Token } = req.body;

    if(!Token){
        return res.status(400).json({'Message': "Token is Required"})
    }

    try {
        const VerifyRes = await authModel.checkEmailVerficationToken(Token)

        if(!VerifyRes){
            return res.status(400).json({'Message': "Invalid token"});
        }

        const currentTime = new Date();
        if (new Date(VerifyRes.email_verification_expires) < currentTime) {
            return res.status(400).json({'Message': "Token expired. Please sign up again."});
        }

        await userModel.VerifyUser(VerifyRes.user_ID)

        res.status(200).json({ message: 'Email verified successfully! You can now log in.'});
    } catch (error) {                                               
        console.error('Error in Verifing Email', error);
        res.status(401).json({ message: error.message });
    }
}


exports.requestPasswordReset = async (req, res) => {
    try {
      const { Email } = req.body;
      if(!Email){
        return res.status(400).json({message:"Email is Required."})
      }
      const user = await userModel.getUserByEmail(Email);
  
      if (!user) {
        return res.status(404).json({ message: "This Email doesn't exist on TwinAI" });
      }
  
      const token = crypto.randomBytes(32).toString('hex');
      const expiresAt = new Date(Date.now() + 3600000); // Token valid for 1 hour
  
      await authModel.StoreResetToken(Email, token, expiresAt);
  
      // Here you should call your email-sending logic with the token
      const verificationLink = `http://sprinter.mes-design.com/forget-password?t=${token}`;
        
      const emailSubject = 'Password Reset Request';
      const emailMessage = `
      Hello,

        We received a request to reset your password. Click the link below to set a new password:

        ${verificationLink}

        This link will expire in 1 hour for security reasons. If you didn't request this, please ignore this email.

        If you have any questions, please contact our support team.

        Best regards,  
        Sprinter
      `
      await sendEmail(Email, emailSubject, emailMessage);
      
      return res.status(201).json({ message: 'Password reset link sent to email' });

    } catch (error) {
      return res.status(500).json({ message: 'Server error', error });
    }
};

exports.resetPassword = async (req, res) => {
    try {
      const { token, newPassword } = req.body;
      if(!token || !newPassword){
        return res.status(400).json({message:"Fields can't be empty."})
      }
      
      const resetRecord = await authModel.FindResetToken(token);
      if (!resetRecord) {
        return res.status(400).json({ message: 'Invalid or expired token' });
      }
      const concatenatedPassword = resetRecord['email'] + newPassword;
      const PasswordHash = await bcrypt.hash(concatenatedPassword, 10);
      await userModel.updatePassword(resetRecord['email'], PasswordHash);
      await authModel.deleteResetToken(resetRecord['email']);
  
      return res.json({ message: 'Password reset successfully' });
    } catch (error) {
      return res.status(500).json({ message: 'Server error', error });
    }
};
