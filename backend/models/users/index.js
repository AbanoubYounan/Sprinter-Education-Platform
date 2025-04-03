const { SignUp } = require('./create')
const { getUserByEmail } = require('./retrieve')
const { VerifyUser, UpdateEmailVerificationToken, updatePassword } = require('./update')

module.exports = {
    SignUp,
    getUserByEmail,
    VerifyUser,
    UpdateEmailVerificationToken,
    updatePassword
}